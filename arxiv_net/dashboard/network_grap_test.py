import dash
import dash_cytoscape as cyto
import dash_html_components as html
import pickle
from arxiv_net.utilities import Config

DB = pickle.load(open(Config.ss_db_path, 'rb'))

# Get papers
papers = list(DB.items())
papers_subset = []
subset_size = 10
i = 0
while i < subset_size:
    papers_subset.append(papers[i])
    i += 1
nodes = []
edges = []
years = []
x = 0
y = 100

for paper_id, paper in papers_subset:
    if paper.year not in years:
        years.append(paper.year)

    nodes.append({
        'data': {'id': paper_id, 'label': paper.title[:50]},
        'position': {'x': x, 'y': y}
    })
    x += 50
    for reference in paper.references:
        if reference.paperId in papers_subset:
            edges.append({'data': {'id': reference.paperId + "." + paper_id, 'source': reference.paperId, 'target': paper_id}})


# years.sort()

print(nodes)
print(edges)
print(years)
# Setup App

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        userPanningEnabled=False,
        userZoomingEnabled=False,
        autolock=True,
        layout={'name': 'grid', 'padding': 10},
        style={'width': '60%', 'height': '800px', 'border': '1px solid black'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'shape': 'rectangle',
                    'text-valign': 'center',
                    'padding': 3,
                    'content': 'data(label)',
                    'text-wrap': 'wrap',
                    'text-max-width': '12px',
                    'font-size': 5
                }
            },
            {
                'selector': 'edge',
                'style': {
                    # The default curve style does not work with certain arrows
                    'curve-style': 'bezier',
                    'source-arrow-shape': 'triangle',
                    'color': 'black',
                    'font-size': 8
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
        elements=nodes+edges
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)