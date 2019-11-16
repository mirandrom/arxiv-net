import importlib
from collections import OrderedDict, defaultdict
from textwrap import dedent

import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import ray
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from tqdm import tqdm

from arxiv_net.app import app
from arxiv_net.assets.style import *

CATEGORIES = ['NLP', 'RL']

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
                                        value='Tab 1',
                                        children=[
                                            dcc.Tab(
                                                label='Tab 1',
                                                value='Tab 1',
                                                style=tab_style,
                                                selected_style=selected_style,
                                            ),
                                            dcc.Tab(
                                                label="Tab 2",
                                                value="Tab 2",
                                                style=tab_style,
                                                selected_style=selected_style
                                            ),
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
                id='static_components',
                children=[
                    
                    html.Div(
                        id='category_div',
                        children=[
                            html.Label('Category:', style={'textAlign': 'center'}),
                            dcc.Dropdown(
                                id='category',
                                options=[{'label': c, 'value': c} for c in CATEGORIES],
                                value=CATEGORIES[0]
                            )
                        ],
                        style={'display': 'none'},
                        className='two columns',
                    ),
                    html.Div(
                        id='search_div',
                        children=[
                            html.Label('Search by title:',
                                       style={'textAlign': 'center'}),
                            dcc.Input(
                                id='search',
                                placeholder='Attention Is All You Need',
                                type='text',
                                value='Attention Is All You Need',
                                style={'width': '100%', 'textAlign': 'center'}
                            )
                        ],
                        style={'display': 'none'},
                        className='two columns',
                    ),
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
        Input('button', 'n_clicks')
    ],
    [
        State('button', 'children'),
        State('section', 'value'),
    ],
)
def RL(
    clicks,
    button_state,
    section,
):
    if not clicks:
        raise PreventUpdate
    if button_state == 'Stop':
        raise PreventUpdate
    
    if section == 'Tab 1':
        return html.P("hello")
    elif section == 'Tab 2':
        return html.P("world")
    else:
        raise ValueError(f'Unknown section {section}')



