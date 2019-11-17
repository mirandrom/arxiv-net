import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from tqdm import tqdm

from arxiv_net.dashboard import DB
from arxiv_net.dashboard.server import app
from arxiv_net.users import USER_DIR

__all__ = ['display_user_library', 'display_recommendation_feed']


@app.callback(
    Output('user-library', 'children'),
    [Input('feed', 'value')],
    [State('user-name', 'children')],
)
def display_user_library(feed: str, username: dict):
    if feed != 'Recommend':
        return []
    print(username)
    
    # Extract username in case logged in
    if not isinstance(username, dict):
        return html.Div(
            [
                dcc.Markdown("You need to be logged in to view your library."),
                html.A('LOGIN', href='/')
            ]
        )
    else:
        username = username['props']['children'].split(' ')[1]
        with open(f'{USER_DIR}/{username}.json') as f:
            pref = json.load(f)
        
        li = list()
        for paper in tqdm(pref):
            paper = DB[paper]
            li.append(html.Li(
                children=[
                    dcc.Markdown(f"""
                        ##### [{paper.title}]({paper.url})
                        _{', '.join([author.name for author in paper.authors])} -- {paper.year} -- {paper.venue}_
                    """),
                    html.Hr(),
                ],
                style={'list-style-type': 'none'}
            ))
        return html.Ul(children=li)


@app.callback(
    Output('user-recommendations', 'children'),
    [Input('feed', 'value')],
    [State('user-name', 'children')],
)
def display_recommendation_feed(
    feed,
    username
):
    # TODO: dump preferences in SQL instead of flat files
    # TODO: pre-populate the div so that we can assign callbacks to buttons
    if feed != 'Recommend':
        return []
    
    # Do not show recommendations unless logged in
    print(username)
    if not isinstance(username, dict):
        return []
    
    username = username['props']['children'].split(' ')[1]
    with open(f'{USER_DIR}/{username}.json') as f:
        pref = json.load(f)
    
    li = list()
    for paper_id in pref:
        paper = DB[paper_id]
        li.append(html.Li(
            [
                html.Button('Mark As Read', id=f'read-{paper.doi}'),
                html.Button('Save To Library', id=f'save-{paper.doi}'),
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
