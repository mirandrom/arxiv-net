import datetime
import json
import pickle
from collections import defaultdict
from typing import Dict, Set, List, Optional
from tqdm import tqdm
from pathlib import Path
import pandas as pd
import dash_cytoscape as cyto
from collections import Counter

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go

from arxiv_net.dashboard import DASH_DIR, LOOKBACKS, TOPICS
from arxiv_net.dashboard.assets.style import *
from arxiv_net.dashboard.dashboard import Hider
from arxiv_net.dashboard.pages.feeds.explore import DASH
from arxiv_net.dashboard.server import app
from arxiv_net.textsearch.whoosh import get_index, search_index
from arxiv_net.users import USER_DIR
from arxiv_net.utilities import Config
from arxiv_net.dashboard import DASH_DIR
from typing import NamedTuple

################################################################################
# DATA LOADING
################################################################################
DB = pickle.load(open(Config.ss_db_path, 'rb'))
DB_ARXIV = pickle.load(open(Config.db_path, 'rb'))
SIMILARITIES = pickle.load(open(Config.sim_path, 'rb'))

embed_db_path = Path(Config.bert_abstract_embed_db_path)
embeds_tsne_csv_path = embed_db_path.with_name(embed_db_path.name.replace(".p", "_tsne.csv"))
TSNE_CSV = pd.read_csv(embeds_tsne_csv_path, dtype=str, names=["arxiv_id", "x", "y", "z"], skiprows=1)
TSNE_CSV["Category"] = [DB_ARXIV[i]["arxiv_primary_category"]["term"] if i in DB_ARXIV else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["CitationVelocity"] = [DB[i].citationVelocity if i in DB else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["InfluentialCitationCount"] = [DB[i].influentialCitationCount if i in DB else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["Topics"] = [[t.topic for t in DB[i].topics] if i in DB else [] for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["Year"] = [int(DB_ARXIV[i]["published"][:4]) if i in DB_ARXIV else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["Title"] = [f"[{i}] {DB[i].title}" if i in DB else None for i in TSNE_CSV['arxiv_id']]

# TODO: add auto-completion (https://community.plot.ly/t/auto-complete-text-suggestion-option-in-textfield/8940)


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

################################################################################
# STATIC MARKDOWN
################################################################################
discover_intro_md = (DASH_DIR / "assets/discover_intro.md").read_text()


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
# LAYOUT
################################################################################

discover_feed_layout = html.Div(
    id='discover-feed',
    className="row",
    style={
        "max-width": "100%",
        "font-size": "1.5rem",
        "padding"  : "0px 0px",
        'display'  : 'none'
    },
    children=[
        # Body
        html.Div(
            className="row background",
            style={"padding": "10px"},
            children=[
                html.Div(
                    className="three columns",
                    style={"padding": "30px"},
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
                                    min=2015,
                                    max=2020,
                                    step=1,
                                    val=(2019, 2021),
                                    marks={
                                        i: str(i) for i in range(2015, 2021)
                                    },
                                ),
                                html.Div(
                                    className="row background",
                                    id="discover-explanation",
                                    children=[
                                        html.Div(
                                            id="discover-description-text",
                                            children=dcc.Markdown(
                                                discover_intro_md)
                                        ),
                                        # TODO: what is this
                                        html.Div(
                                            html.Button(id="learn-more-button",
                                                        children=["Learn More"])
                                        ),
                                    ],
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
                html.Div(
                    className="three columns",
                    id="side-pane",
                    children=[
                        Card(
                            style={"padding": "25px"},
                            children=[
                                html.Div(id="div-plot-click-abstract"),
                            ],
                        )
                    ],
                ),
            ],
        ),
    ],
)

explore_feed_layout = html.Div(
    id='explore-feed',
    children=[
        html.Div(
            id='search-feed',
            children=[
                html.Div(
                    id='filters',
                    children=[
                        topics_filter,
                        author_filter,
                        # title_filter,
                        date_filter,
                        search_button
                    ]
                ),
                html.Hr(),
                html.Div(
                    id='feed-div',
                    children=[
                        html.Div(
                            # dcc.Loading(
                            # type='cube',
                            id='display-feed',
                            children=[
                                html.Ul(
                                    children=[
                                        html.Li(
                                            id=f'paper-placeholder-{i}')
                                        for i in range(DASH.feed.display_size)
                                    ],
                                    style={'list-style-type': 'none'}
                                )

                            ]
                        )
                    ]
                )
            ],
            className='four columns'
        ),
        html.Div(
            id='focus-feed',
            children=[
                html.Button('hide search feed', id='hide-button'),
                html.Div('Related papers: '),
                dcc.RadioItems(
                    id='radio',
                    options=[
                        {'label': 'Similar', 'value': 'similar'},
                        {'label': 'References', 'value': 'references'},
                        {'label': 'Citations', 'value': 'citations'}
                    ],
                    value='similar',
                    labelStyle={'display': 'inline-block'},

                ),
                html.Hr(),
                html.Div(
                    id='focus-feed-div',
                    children=[
                    ],
                    style={
                        'textAlign' : 'center',
                        'fontFamily': 'Avenir',
                    },
                ),
            ],
            className='four columns'
        ),
        html.Div(
            id='cytoscape-nodes',
            children=[
                cyto.Cytoscape(
                    id='cytoscape-two-nodes',
                    userPanningEnabled=True,
                    userZoomingEnabled=False,
                    layout={'name': 'preset', 'padding': 40, 'fit': True, 'autosize': True},
                    style={'width' : '500px', 'height': '700px'},
                    stylesheet=[
                        {
                            'selector': 'node',
                            'style'   : {
                                'shape'         : 'circle',
                                'text-valign'   : 'center',
                                'padding'       : 3,
                                'content'       : 'data(label)',
                                'text-wrap'     : 'wrap',
                                'text-max-width': '12px',
                                'font-size'     : 12,
                                'font-weight': 600
                            }
                        },
                        {
                            'selector': 'edge',
                            'style'   : {
                                # The default curve style does not work with certain arrows
                                'curve-style'       : 'bezier',
                                'color'             : 'black',
                                'font-size'         : 8
                            }
                        },
                        {
                            'selector': '#one',
                            'style'   : {
                                'text-valign': 'center',
                                'width'      : 'label',
                                'content'    : 'hi\nbye',
                                'height'     : 'label',
                                'padding'    : 5
                            }
                        },
                        {
                            'selector': '.parent_node',
                            'style'   : {
                                'shape'        : 'rectangle',
                                'text-halign'  : 'left',
                                'text-valign'  : 'top',
                                'text-margin-x': 45,
                                'text-margin-y': 25,
                                'font-size'    : 14,
                                'min-width'    : '400px',
                                'min-height'   : '250px',
                            }
                        },
                        {
                            'selector': '.node',
                            'style': {
                                'background-color': 'white',
                                'border-width': '2px',
                                'shape': 'circle',
                            }
                        },
                        {
                            'selector': '.main_node',
                            'style': {
                                'background-color': 'rgb(255, 220, 246)',
                                'border-width': '2px',
                                'border-color': 'darkred',
                                'width': '50px',
                                'height': '50px',
                            }
                        },
                    ],
                    elements=[]
                )
            ],
            className='four columns'
        )
    ],
    className="row",
    style={
        'display': 'none'
    },
)

recommend_feed_layout = html.Div(
    id='recommend-feed',
    className="row",
    children=[
        html.Div(
            id='library',
            children=[
                html.Label('Library'),
                html.Div(
                    id='user-library'
                )
            ],
            className='six columns'
        ),
        html.Div(
            id='recommend-feed-div',
            children=[
                html.Label('Recommendations'),
                dcc.Loading(
                    id='user-recommendations',
                    type='cube'
                )
            ],
            className='six columns'
        ),
    ],
    style={
        'display': 'none'
    },
)

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
                                    html.H2("ArXivNet"),
                                ],
                                className='two columns title',
                            ),
                            html.Div(
                                id='tabs-div',
                                children=[
                                    dcc.Tabs(
                                        id='feed',
                                        style=container_style,
                                        value='Discover',
                                        children=[
                                            dcc.Tab(
                                                label="Discover",
                                                value="Discover",
                                                style=tab_style,
                                                selected_style=selected_style
                                            ),
                                            dcc.Tab(
                                                label='Search',
                                                value='Explore',
                                                style=tab_style,
                                                selected_style=selected_style,
                                            ),
                                            dcc.Tab(
                                                label="Library",
                                                value="Recommend",
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
            explore_feed_layout,
            recommend_feed_layout,
            discover_feed_layout
        ],
        className='page',
    )
])


# -----------------------------------------------------------------------------
# Callbacks

@app.callback(
    Output('filters', 'children'),
    [Input('feed', 'value')]
)
def display_filters(feed: str):
    """ Choose available filters based on the type of feed """
    if feed == 'Explore':
        return [title_filter, author_filter, date_filter, search_button]
    # elif feed == 'Recommend':
    #     return [date_filter, search_button]
    return []


@app.callback(
    [
        Output('explore-feed', 'style'),
        Output('discover-feed', 'style'),
        Output('recommend-feed', 'style'),
    ],
    [Input('feed', 'value')]
)
def choose_feed(feed: str):
    """ Shows / hides feeds based on the user selection """
    if feed == 'Explore':
        return [Hider.show, Hider.hide, Hider.hide]
    elif feed == 'Discover':
        return [Hider.hide, Hider.show, Hider.hide]
    elif feed == 'Recommend':
        return [Hider.hide, Hider.hide, Hider.show]

