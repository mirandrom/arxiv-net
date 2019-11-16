import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from arxiv_net.dashboard.app import app
from arxiv_net.dashboard.assets.style import *
from arxiv_net.ss.semantic_scholar_api import SsArxivPaper

# TODO: autocomplete

KEYWORDS = ['NLP', 'RL']
LOOKBACKS = ['This Week', 'This Month', 'This Year', 'Filter By Year (Callback Popup)']

layout = html.Div([
    html.Div(
        children=[
            html.Div(
                id='header',
                children=[
                    html.Div(
                        [
                            html.Div(
                                id='title_div',
                                children=[
                                    html.H2("arXiv NET"),
                                ],
                                className='two columns title',
                            ),
                            html.Div(
                                id='tabs_div',
                                children=[
                                    dcc.Tabs(
                                        id='section',
                                        style=container_style,
                                        value='Explore',
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
                            html.Div(
                                id='button_div',
                                children=[
                                    html.Button('Clickbait', id='button'),
                                ],
                                className='one column custom_button',
                            ),
                        ],
                        className='row'
                    ),
                ],
                className='header'
            ),
            
            html.Div(
                id='static-components',
                children=[
                    html.Div(
                        id='search',
                        children=[
                            html.Div(
                                id='keyword-div',
                                children=[
                                    html.Label('Keyword:',
                                               style={'textAlign': 'center'}),
                                    dcc.Dropdown(
                                        id='keyword',
                                        options=[{'label': c, 'value': c} for c
                                                 in KEYWORDS],
                                        value=KEYWORDS[0]
                                    )
                                ],
                                style={'display': 'block'},
                                className='two columns',
                            ),
                            html.Div(
                                id='title-div',
                                children=[
                                    html.Label('Title:',
                                               style={'textAlign': 'center'}),
                                    dcc.Input(
                                        id='title',
                                        placeholder='Attention Is All You Need',
                                        type='text',
                                        value='Attention Is All You Need',
                                        style={'width'    : '100%',
                                               'textAlign': 'center'}
                                    )
                                ],
                                style={'display': 'block'},
                                className='two columns',
                            ),
                            html.Div(
                                id='author-div',
                                children=[
                                    html.Label('Author:',
                                               style={'textAlign': 'center'}),
                                    dcc.Input(
                                        id='author',
                                        placeholder='Richard Sutton',
                                        type='text',
                                        value='David Silver',
                                        style={'width'    : '100%',
                                               'textAlign': 'center'}
                                    )
                                ],
                                style={'display': 'block'},
                                className='two columns',
                            ),
                            html.Div(
                                id='date-div',
                                children=[
                                    html.Label('Published:',
                                               style={'textAlign': 'center'}),
                                    dcc.Dropdown(
                                        id='date',
                                        options=[{'label': c, 'value': c} for c
                                                 in LOOKBACKS],
                                        value=LOOKBACKS[0]
                                    )
                                ],
                                style={'display': 'block'},
                                className='two columns',
                            ),
                        ]
                    )
                
                ],
                className='row'
            ),
            
            html.Div(
                id='dynamic_components',
                children=[
                    html.Div(
                        id='main-page',
                        children=[
                            dcc.Loading(id='dispaly-main-page', type='cube')
                        ],
                        style={
                            'textAlign' : 'center',
                            'fontFamily': 'Avenir',
                        },
                    ),
                ],
                className='row',
            ),
            html.Br(),
            dcc.Link('To HOME', href='/'),
        ],
        className='page',
    )
])


@app.callback(
    Output('display-main-page', 'children'),
    [
        Input('button', 'n_clicks'),
        Input('author', 'value'),
        Input('title', 'value'),
        Input('keyword', 'value'),
    ],
    [
        State('button', 'children'),
        State('section', 'value'),
    ],
)
def display_feed(
    clicks,
    button_state,
    section,
):
    if not clicks:
        raise PreventUpdate
    if button_state == 'Stop':
        raise PreventUpdate
    
    if section == 'Recommend':
        return recommendation_feed()
    elif section == 'Explore':
        return exploration_feed()
    else:
        raise ValueError(f'Unknown section {section}')




def exploration_feed() -> html.Ul:
    return html.Ul(
    )

def recommendation_feed() -> html.Ul:
    return html.Ul(
        html.Li(
            SsArxivPaper
        )
        
    )
    