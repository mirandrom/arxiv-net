import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output

from arxiv_net.dashboard import DASH_DIR, LOOKBACKS, TOPICS
from arxiv_net.dashboard.assets.style import *
from arxiv_net.dashboard.dashboard import Hider
from arxiv_net.dashboard.pages.feeds.explore import DASH
from arxiv_net.dashboard.server import app

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
                        dcc.Graph(id="graph-3d-plot-tsne",
                                  style={"height": "98vh"})
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
                html.Button('show search feed', id='hide-button'),
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
                    layout={'name': 'preset', 'padding': 40, 'fit': True},
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
                                'source-arrow-shape': 'triangle',
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
                                'border-color': 'pink',
                                'shape': 'circle',
                            }
                        },
                        {
                            'selector': '.main_node',
                            'style': {
                                'background-color': 'white',
                                'border-width': '2px',
                                'border-color': '#0FA0CE',
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
                                        value='Discover',
                                        children=[
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

