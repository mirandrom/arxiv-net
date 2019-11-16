import dash
import dash_cytoscape as cyto
import dash_html_components as html

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        userPanningEnabled=False,
        userZoomingEnabled=False,
        autolock=True,
        layout={'name': 'grid', 'padding': 100},
        style={'width': '100%', 'height': '400px', 'border': '1px solid black'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    # The default curve style does not work with certain arrows
                    'curve-style': 'bezier'
                }
            },
            {
                'selector': '#onetwo',
                'style': {
                    'source-arrow-shape': 'triangle',
                    'tooltip': 'tooltips!'
                }
            },
            {
                'selector': '#one',
                'style': {
                    'shape': 'rectangle',
                    'text-valign': 'center',
                    'width': 'label',
                    'content': 'hi\nbye',
                    'height': 'label',
                    'padding': 5
                }
            }
        ],
        elements=[
            {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 50, 'y': 50}},
            {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 50, 'y': 100}},
            {'data': {'id': 'three', 'label': 'Node 3'}, 'position': {'x': 0, 'y': 100}},
            {'data': {'id': 'four', 'label': 'Node 4'}, 'position': {'x':   0, 'y': 50}},
            {'data': {'id': 'five', 'label': 'Node 5'}, 'position': {'x': 60, 'y': 0}},
            {'data': {'id': 'onetwo', 'source': 'one', 'target': 'two'}}
        ]
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)