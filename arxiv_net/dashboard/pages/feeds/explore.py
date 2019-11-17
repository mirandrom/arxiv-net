import datetime
from typing import Set

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from tqdm import tqdm

from arxiv_net.dashboard import DB, DB_ARXIV, SIMILARITIES, PaperID, TITLES, AUTHORS, TOPICS
from arxiv_net.dashboard.dashboard import Dashboard, Hider
from arxiv_net.dashboard.pages.feeds.feed import PaperFeed
from arxiv_net.dashboard.server import app
from arxiv_net.textsearch.whoosh import get_index, search_index

DASH = Dashboard()

__all__ = ['highlight_selected_paper', 'hide_search_feed', 'display_exploration_feed', 'focus_feed', 'graph']


def _soft_match_title(user_title: str) -> Set[PaperID]:
    search_results = set()
    if user_title == 'Any':
        for papers in TITLES.values():
            search_results |= papers
        return search_results
    search_results = set(search_index(user_title, "abstract", get_index()))
    return search_results


def _soft_match_author(user_author: str) -> Set[PaperID]:
    # TODO: Adjust for casing
    matched = set()
    for author, papers in AUTHORS.items():
        if user_author == 'Any' or user_author in author:
            matched |= papers
    return matched


def _soft_match_topic(user_topic: str) -> Set[PaperID]:
    # TODO: Adjust for casing
    matched = set()
    for topic, papers in TOPICS.items():
        if user_topic == 'Any' or user_topic in topic:
            matched |= papers
    return matched


@app.callback(
    [Output(f'paper-placeholder-{i}', 'className') for i in
     range(DASH.feed.display_size)],
    [Input('focus-feed-div', 'children')],
)
def highlight_selected_paper(*args):
    print(f'Highlighting selected paper: {DASH.feed.selected}')
    classnames = ['paper-placeholder' for _ in range(DASH.feed.display_size)]
    if DASH.feed.selected is not None:
        classnames[DASH.feed.selected] = 'selected-paper-div'
    return classnames


@app.callback(
    [
        Output('search-feed', 'style'),
        Output('hide-button', 'children'),
        Output('cytoscape-nodes', 'className'),
        Output('focus-feed', 'className')
    
    ],
    [Input('hide-button', 'n_clicks')],
    [State('hide-button', 'children')]

)
def hide_search_feed(_, button_state):
    print(button_state)
    if button_state == 'hide_search_feed':
        return [Hider.show, 'show_search_feed', 'four columns', 'four columns']
    elif button_state == 'show_search_feed':
        return [Hider.hide, 'hide_search_feed', 'six columns', 'six columns']


@app.callback(
    [
        Output(f'paper-placeholder-{i}', 'children')
        for i in range(DASH.feed.display_size)
    ],
    [
        Input('button', 'n_clicks'),
    ],
    [
        State('filters', 'children'),
        State('button', 'children'),
        State('feed', 'value'),
        State('user-name', 'children')
    ],
)
def display_exploration_feed(
    n_clicks,
    filters,
    button_state,
    feed,
    username
):
    """ Populates pre-allocated list in the explore-div with the papers
    that match search results. Updates the global state of `PaperFeed` to
    allow for other callbacks to utilize the search results.
    """
    if not n_clicks:
        raise PreventUpdate
    if button_state == 'Stop':
        raise PreventUpdate
    
    if feed != 'Explore':
        return []
    
    # Extract values for selected filters
    ff = dict()
    for f in filters:
        filter_name = f['props']['id'].split('-')[0]
        if filter_name == 'button':
            continue
        filter_value = f['props']['children'][1]['props']['value']
        ff[filter_name] = filter_value
    
    # Extract username in case logged in
    username = 'default'
    if isinstance(username, dict):
        # username = username['props']
        pass  # Use `default` user for testing
    
    matched_titles = _soft_match_title(ff['title'])
    matched_authors = _soft_match_author(ff['author'])
    # matched_topics = _soft_match_topic(ff['topic'])
    print(ff)
    # print(f'Matched authors: {matched_authors}')
    # print(f'Matched titles: {matched_titles}')
    # print(f'Matched topics: {matched_topics}')
    
    possible_papers = list(matched_authors & matched_titles)
    DASH.feed = PaperFeed(collection=possible_papers)
    
    li = list()
    for i in range(DASH.feed.display_size):
        if i >= len(DASH.feed.displayed):
            li.append([])
            continue
        paper_id = DASH.feed.displayed[i]
        paper = DB[paper_id]
        li.append(
            [
                dcc.Markdown(
                    f"""
                    ##### [{paper.title}]({paper.url})
                    _{', '.join([author.name for author in paper.authors])} -- {paper.year} -- {paper.venue}_
                    """
                ),
                html.Hr(),
            ]
        )
    return li


@app.callback(
    Output('focus-feed-div', 'children'),
    [Input(f'paper-placeholder-{i}', 'n_clicks') for i in
     range(DASH.feed.display_size)],
    [State('radio', 'value')]
)
def focus_feed(*args):
    """  """
    triggers = dash.callback_context.triggered
    print(triggers)
    category = args[-1]
    idx = int(triggers[0]['prop_id'].split('.')[0].split('-')[-1])
    DASH.feed.selected = idx
    DASH.focus_feed.collection = list()
    paper_id = DASH.feed.displayed[idx]
    paper = DB[paper_id]
    
    print(f'PAPER SELECTED: {paper.title}')
    
    to_display = list()
    if category == 'similar':
        to_display += [DB[pid] for pid in SIMILARITIES[paper_id] if pid in DB]
    elif category == 'citations':
        to_display += paper.citations
    elif category == 'references':
        to_display += paper.references
    
    to_display = to_display[:10]
    # TODO: sort things here + color code
    li = list()
    for p in tqdm(to_display):
        if p.arxivId is None or p.arxivId not in DB:
            continue
        DASH.focus_feed.collection.append(p.arxivId)
        paper = DB[p.arxivId]
        li.append(html.Li(
            children=[
                dcc.Markdown(
                    f"""
                    ##### [{paper.title}]({paper.url})
                    _{', '.join([author.name for author in paper.authors])} -- {paper.year} -- {paper.venue}_
                    """
                ),
                html.Button('More like this', id=f'more-{paper.doi}'),
                html.Button('Less like this', id=f'less-{paper.doi}'),
                html.Hr(),
            ],
            style={'list-style-type': 'none'}
        ))
    return html.Ul(children=li)


@app.callback(
    Output('cytoscape-two-nodes', 'elements'),
    [Input('focus-feed-div', 'children')],
)
def graph(*args):
    if not DASH.focus_feed.collection:
        return []
    
    parent_nodes, nodes, edges = list(), list(), list()
    
    years = []
    seconds_in_year = 31622400
    x = 0
    
    # Get list of years
    for paper_id in DASH.focus_feed.collection:
        date = DB_ARXIV[paper_id]['published']
        date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        
        if date.year not in years:
            years.append(date.year)
            parent_nodes.append({
                'data'   : {'id': date.year, 'label': date.year},
                'classes': 'parent_node'
            })
    
    years.sort(reverse=True)
    
    # Generate Nodes and Edges
    total_height = 500
    number_of_sections = len(years)
    section_height = total_height / number_of_sections
    for paper_id in tqdm(DASH.focus_feed.collection):
        paper = DB[paper_id]
        date = DB_ARXIV[paper_id]['published']
        date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        date_start_of_year = datetime.datetime(date.year, 1, 1)
        seconds_difference = (date - date_start_of_year).total_seconds()
        normalized_date = (seconds_difference / seconds_in_year)
        year_index = years.index(date.year)
        y = round(
            normalized_date * section_height) + section_height * year_index
        # print(y)
        # print(date)
        nodes.append({
            'data'    : {'id'    : paper_id,
                         'label' : str(date.year) + paper.title[:30],
                         'parent': date.year},
            'position': {'x': x, 'y': y}
        })
        x += 50
        for reference in paper.references:
            if reference.paperId in DASH.focus_feed.collection:
                edges.append({'data': {'id'    : reference.paperId + "." + paper_id,
                                       'source': reference.paperId,
                                       'target': paper_id}})
    print(parent_nodes + nodes + edges)
    return parent_nodes + nodes + edges
