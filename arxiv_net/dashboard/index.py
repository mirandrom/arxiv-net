import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from arxiv_net.dashboard.app import app
from arxiv_net.dashboard.pages import arxiv_dash

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

index_page = html.Div([
    dcc.Link('arxiv_dash', href='/arxiv_dash'),
    html.Br(),
])


# Update the index
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/arxiv_dash':
        return arxiv_dash.layout
    else:
        return index_page  # You could also return a 404 "URL not found" page here


if __name__ == '__main__':
    app.run_server(host='localhost', port=1337, debug=True)
