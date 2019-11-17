import json
import pickle
from collections import defaultdict
from typing import Dict, Set, List, Optional
from tqdm import tqdm
from pathlib import Path
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go


from arxiv_net.dashboard.assets.style import *
from arxiv_net.dashboard.server import app
from arxiv_net.textsearch.whoosh import get_index, search_index
from arxiv_net.users import USER_DIR
from arxiv_net.utilities import Config, ROOT_DIR

################################################################################
# DATA LOADING
################################################################################
DASHBOARD_DIR = ROOT_DIR / "dashboard"
DB = pickle.load(open(Config.ss_db_path, 'rb'))
DB_ARXIV = pickle.load(open(Config.db_path, 'rb'))

embed_db_path = Path(Config.bert_abstract_embed_db_path)
embeds_tsne_csv_path = embed_db_path.with_name(embed_db_path.name.replace(".p", "_tsne.csv"))
TSNE_CSV = pd.read_csv(embeds_tsne_csv_path, dtype=str)
TSNE_CSV["Topic"] = [DB_ARXIV[i]["arxiv_primary_category"]["term"] if i in DB_ARXIV else None for i in TSNE_CSV['Unnamed: 0']]
TSNE_CSV["CitationVelocity"] = [DB[i].citationVelocity if i in DB else None for i in TSNE_CSV['Unnamed: 0']]
TSNE_CSV["Year"] = [int(DB_ARXIV[i]["published"][:4]) if i in DB_ARXIV else None for i in TSNE_CSV['Unnamed: 0']]
TSNE_CSV["Title"] = [DB[i].title if i in DB else None for i in TSNE_CSV['Unnamed: 0']]

# TODO: add auto-completion (https://community.plot.ly/t/auto-complete-text-suggestion-option-in-textfield/8940)

# Indexing db, should be done asynchronously while fetching from SS
PaperID = Title = AuthorName = Topic = str
AUTHORS: Dict[AuthorName, Set[PaperID]] = defaultdict(set)
TOPICS: Dict[Topic, Set[PaperID]] = defaultdict(set)
TITLES: Dict[Title, Set[PaperID]] = defaultdict(set)
LOOKBACKS = ['This Week', 'This Month', 'This Year',
             'Filter By Year (Callback Popup)']
index = get_index()

for paper_id, paper in tqdm(DB.items()):
    if paper is None:
        # TODO (Andrei): why are there None's?
        continue
    for author in paper.authors:
        AUTHORS[author.name].add(paper_id)
    for topic in paper.topics:
        TOPICS[topic.topic].add(paper_id)
    TITLES[paper.title].add(paper_id)


class PaperFeed:
    """" A tracker for displayed / selected papers
    """
    
    def __init__(self,
                 collection: List[PaperID],
                 selected: Optional[PaperID] = None,
                 display_size: int = 10,
                 ):
        self.collection = collection
        self.display_size = display_size
        self.selected = selected
        self.current_page = 0
        self.total_pages = len(self.collection) // display_size + 1
    
    @property
    def displayed(self):
        return self.collection[self.display_size * self.current_page:
                               self.display_size * self.current_page + self.display_size]
    
    def __call__(self, *args, **kwargs):
        return self.displayed
    
    def reset(self):
        self.collection = list()
        self.selected = None
        self.current_page = 0
    
    def pg_up(self):
        self.current_page += 1
    
    def pg_down(self):
        self.current_page -= 1


class Dashboard:
    """ Encapsulates all methods related to the dash.
    """

    def __init__(self, current_user: str = 'default', feed: PaperFeed = None):
        self.current_user = current_user
        self.feed = feed or PaperFeed(collection=[])


DASH = Dashboard()


################################################################################
# HTML DIVS
################################################################################

# Configure static layout
date_filter = html.Div(
    id='date-div',
    children=[
        html.Label('Published:'),
        dcc.Dropdown(
            id='date',
            className='feed-input',
            options=[{'label': c, 'value': c} for c
                     in LOOKBACKS],
            value=LOOKBACKS[0]
        )
    ],
    # style={'display': 'block'},
    # className='two columns',
)

topics_filter = html.Div(
    id='topic-div',
    children=[
        html.Label('Topic:'),
        dcc.Dropdown(
            id='topic',
            className='feed-input',
            options=[{'label': c, 'value': c} for c
                     in TOPICS],
            value='Any'
        )
    ]
)

title_filter = html.Div(
    id='title-div',
    children=[
        html.Label('Title:'),
        dcc.Input(
            id='title',
            className='feed-input',
            placeholder='Attention Is All You Need',
            type='text',
            value='Any'
        )
    ]
)

author_filter = html.Div(
    id='author-div',
    children=[
        html.Label('Author:'),
        dcc.Input(
            id='author',
            className='feed-input',
            placeholder='Richard Sutton',
            type='text',
            value='Any'
        )
    ]
)

search_button = html.Div(
    id='button-div',
    children=[
        html.Button('Search', id='button'),
    ],
    className='one column custom_button',
)

tsne_plot = html.Div(
    className="six columns",
    children=[
        dcc.Graph(id="graph-3d-plot-tsne", style={"height": "98vh"})
    ],
),

################################################################################
# LAYOUT
################################################################################

layout = html.Div([
    html.Div(
        children=[
            html.Div(
                id='header',
                children=[
                    html.Div(
                        [
                            html.Div(
                                id='title-div',
                                children=[
                                    html.H2("arXiv NET"),
                                ],
                                className='two columns title',
                            ),
                            html.Div(
                                id='tabs-div',
                                children=[
                                    dcc.Tabs(
                                        id='feed',
                                        style=container_style,
                                        value='Recommended',
                                        children=[
                                            dcc.Tab(
                                                label='Explore',
                                                value='Explore',
                                                style=tab_style,
                                                selected_style=selected_style,
                                            ),
                                            dcc.Tab(
                                                label="Recommended",
                                                value="Recommended",
                                                style=tab_style,
                                                selected_style=selected_style
                                            ),
                                            dcc.Tab(
                                                label="Discover",
                                                value="Discover",
                                                style=tab_style,
                                                selected_style=selected_style
                                            )
                                        ],
                                    ),
                                ],
                                className='eight columns',
                            ),
                        ],
                        className='row'
                    ),
                ],
                className='header'
            ),
            
            html.Div(
                id='feed-1',
                children=[
                    html.Div(
                        id='filters',
                        children=[
                            author_filter,
                            topics_filter,
                            title_filter,
                            date_filter,
                            search_button
                        ]
                    ),
                    html.Hr(),
                    html.Div(
                        id='feed-div',
                        children=[
                            dcc.Loading(
                                id='display-feed',
                                type='cube',
                                children=[
                                    html.Ul(
                                        children=[
                                            html.Li(id=f'paper-placeholder-{i}')
                                            for i in
                                            range(DASH.feed.display_size - 1)
                                        ],
                                        style={'list-style-type': 'none'}
                                    )
                                
                                ]
                            )
                        ]
                    )
                ],
                className='six columns'
            ),

            html.Div(
                id='feed-2',
                children=[
                    dcc.Checklist(
                        id='checklist',
                        options=[
                            {'label': 'Similar', 'value': 'similar'},
                            {'label': 'References', 'value': 'references'},
                            {'label': 'Citations', 'value': 'citations'}
                        ],
                        value=['Citations']
                    ),
                    html.Hr(),
                    html.Div(
                        id='feed2-div',
                        children=[
                        ],
                        style={
                            'textAlign' : 'center',
                            'fontFamily': 'Avenir',
                        },
                    ),
                ],
                # className='six columns'
            ),
        ],
        className='page',
    )
])
################################################################################
# STATIC MARKDOWN
################################################################################
discover_intro_md = (DASHBOARD_DIR / "assets/discover_intro.md").read_text()

################################################################################
# COMPONENT FACTORIES
################################################################################
def Card(children, **kwargs):
    return html.Section(children, className="card-style")

def NamedRangeSlider(name, short, min, max, step, val, marks=None):
    if marks:
        step = None
    else:
        marks = {i: i for i in range(min, max + 1, step)}

    return html.Div(
        style={"margin": "25px 5px 30px 0px"},
        children=[
            f"{name}:",
            html.Div(
                style={"margin-left": "5px"},
                children=[
                    dcc.RangeSlider(
                        id=f"slider-{short}",
                        min=min,
                        max=max,
                        marks=marks,
                        step=step,
                        value=val,
                    )
                ],
            ),
        ],
    )


################################################################################
# LAYOUT FACTORIES
################################################################################
def create_discover_layout(app):
    return html.Div(
        className="row",
        style={"max-width": "100%", "font-size": "1.5rem", "padding": "0px 0px"},
        children=[
            # Demo Description
            html.Div(
                className="row background",
                id="discover-explanation",
                style={"padding": "50px 45px"},
                children=[
                    html.Div(
                        id="discover-description-text",
                        children=dcc.Markdown(discover_intro_md)
                    ),
                    # TODO: what is this
                    html.Div(
                        html.Button(id="learn-more-button", children=["Learn More"])
                    ),
                ],
            ),
            # Body
            html.Div(
                className="row background",
                style={"padding": "10px"},
                children=[
                    html.Div(
                        className="three columns",
                        children=[
                            Card(
                                [
                                    dcc.Dropdown(
                                        id="discover-categories",
                                        searchable=False,
                                        clearable=False,
                                        options=[
                                            {
                                                "label": "Machine Learning",
                                                "value": "cs.LG",
                                            },
                                            {
                                                "label": "Computer Vision",
                                                "value": "cs.CV",
                                            },
                                            {
                                                "label": "Computational Ling.",
                                                "value": "cs.CL",
                                            },
                                        ],
                                        placeholder="Select a machine learning field",
                                        value="cs.LG",
                                    ),
                                    NamedRangeSlider(
                                        name="Year",
                                        short="discover-year",
                                        min=1995,
                                        max=2020,
                                        step=None,
                                        val=(2019, 2020),
                                        marks={
                                            i: str(i) for i in range(1995, 2020, 5)
                                        },
                                    ),
                                ]
                            )
                        ],
                    ),
                    html.Div(
                        className="six columns",
                        children=[
                            dcc.Graph(id="graph-3d-plot-tsne", style={"height": "98vh"})
                        ],
                    ),
                ],
            ),
        ],
    )


################################################################################
# HELPER METHODS
################################################################################
def _soft_match_title(user_title: str) -> Set[PaperID]:
    search_results = set()
    if user_title == 'Any':
        for papers in TITLES.values():
            search_results |= papers
        return search_results
    search_results = set(search_index(user_title, "abstract", index))
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


def exploration_feed(username: str,
                     author: str,
                     title: str,
                     topic: str,
                     date: str
                     ):
    matched_titles = _soft_match_title(title)
    matched_authors = _soft_match_author(author)
    matched_topics = _soft_match_topic(topic)

    print(author, title, topic)
    # print(f'Matched authors: {matched_authors}')
    # print(f'Matched titles: {matched_titles}')
    # print(f'Matched topics: {matched_topics}')

    possible_papers = list(matched_authors & matched_topics & matched_titles)
    DASH.feed = PaperFeed(collection=possible_papers)

    li = list()
    for i, paper_id in enumerate(DASH.feed.displayed):
        paper = DB[paper_id]
        li.append(
            [
                html.H5([html.A(paper.title, href=paper.url)]),
                html.H6([', '.join([author.name for author in paper.authors]),
                         ' -- ', paper.year, ' -- ', paper.venue]),
                html.Hr(),
            ]
        )
    return li

################################################################################
# CALLBACKS
################################################################################
@app.callback(
    Output('filters', 'children'),
    [Input('feed', 'value')]
)
def display_filters(feed: str):
    """ Choose available filters based on the type of feed """
    if feed == 'Explore':
        return [topics_filter, author_filter, title_filter, date_filter, search_button]
    elif feed == 'Recommended':
        return [date_filter, search_button]
    elif feed == 'Discover':
        return create_discover_layout(app)
    else:
        return []

@app.callback(
    [
        # Output('display-feed', 'children'),
        Output(f'paper-placeholder-{i}', 'children')
        for i in range(DASH.feed.display_size - 1)
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
def display_feed(
    n_clicks,
    filters,
    button_state,
    feed,
    username
):
    if not n_clicks:
        raise PreventUpdate
    if button_state == 'Stop':
        raise PreventUpdate
    
    # Extract values for selected filters
    ff = dict()
    for f in filters:
        filter_name = f['props']['id'].split('-')[0]
        filter_value = f['props']['children'][1]['props']['value']
        ff[filter_name] = filter_value
    
    # Extract username in case logged in
    username = 'default'
    if isinstance(username, dict):
        # username = username['props']
        pass  # Use `default` user for testing
    
    # Construct appropraite feed
    if feed == 'Recommended':
        return recommendation_feed(username, **ff)
    elif feed == 'Explore':
        return exploration_feed(username, **ff)
    else:
        raise ValueError(f'Unknown feed {feed}')


@app.callback(
    Output('feed2-div', 'children'),
    [Input('checklist', 'value')] +
    [Input(f'paper-placeholder-{i}', 'n_clicks') for i in
     range(DASH.feed.display_size - 1)]
)
def feed2(checklist, *args):
    """ Dynamically create callbacks for each paper? """
    print(dash.callback_context.triggered)
    idx = int(
        dash.callback_context.triggered[0]['prop_id'].split('.')[0].split('-')[
            -1])
    paper = DB[DASH.feed.displayed[idx]]
    
    print(f'PAPER SELECTED: {paper.title}')
    li = list()

    to_display = list()
    for category in checklist:
        if category == 'similar':
            pass
        elif category == 'citations':
            to_display += paper.citations
        elif category == 'references':
            to_display += paper.references

    for p in tqdm(to_display):
        if p.arxivId is None or p.arxivId not in DB:
            continue
        paper = DB[p.arxivId]
        print(f'FOUND CITATION: {p.arxivId}')
        li.append(html.Li(
            children=[
                html.H5([html.A(paper.title, href=paper.url)]),
                html.H6([', '.join([author.name for author in paper.authors]),
                         ' -- ', paper.year, ' -- ', paper.venue]),
                html.Button('More like this', id=f'more-{paper.doi}'),
                html.Button('Less like this', id=f'less-{paper.doi}'),
                html.Hr(),
            ],
            style={'list-style-type': 'none'}
        ))
    return html.Ul(children=li)


@app.callback(
    Output("graph-3d-plot-tsne", "figure"),
    [
        Input("discover-categories", "value"),
        Input("slider-discover-year", "value"),
    ],
)
def display_3d_scatter_plot(
        category,
        year_range,
):
    start, end = year_range
    tsne_df = TSNE_CSV.loc[(TSNE_CSV["Topic"] == category) &
                           (TSNE_CSV["Year"] <= end) &
                           (TSNE_CSV["Year"] >= start)].sort_values("CitationVelocity")

    axes = dict(title="", showgrid=True, zeroline=False,
                showticklabels=False)
    layout = go.Layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(xaxis=axes, yaxis=axes, zaxis=axes),
    )

    scatter = go.Scatter3d(
        name=str(tsne_df.index),
        x=tsne_df["x"],
        y=tsne_df["y"],
        z=tsne_df["z"],
        text=tsne_df["Title"],
        textposition="middle center",
        showlegend=False,
        mode="markers",
        marker=dict(size=3, color="#3266c1", symbol="circle"),
    )

    figure = go.Figure(data=[scatter], layout=layout)
    return figure


def recommendation_feed(username: str, date: str) -> html.Ul:
    """ Generates a list of recommended paper based on user's preference.

    """
    # TODO: dump preferences in SQL instead of flat files
    
    with open(f'{USER_DIR}/{username}.json') as f:
        pref = json.load(f)
    
    li = list()
    for paper in tqdm(pref):
        paper = DB[paper]
        li.append(html.Li(
            children=[
                html.H5([html.A(paper.title, href=paper.url),
                         html.Button('Mark As Read', id=f'read-{paper.doi}'),
                         html.Button('Save To Library',
                                     id=f'save-{paper.doi}')]),
                html.H6([', '.join([author.name for author in paper.authors]),
                         ' -- ', paper.year, ' -- ', paper.venue]),
                html.Button('More like this', id=f'more-{paper.doi}'),
                html.Button('Less like this', id=f'less-{paper.doi}'),
                html.Hr(),
            ],
            style={'list-style-type': 'none'}
        ))
    return html.Ul(children=li)
