import dash
import dash_cytoscape as cyto
import dash_html_components as html
import pickle
from arxiv_net.utilities import Config
import datetime

DB = pickle.load(open(Config.ss_db_path, 'rb'))
ARCHIVEDB = pickle.load(open(Config.db_path, 'rb'))

# Get papers
papers = list(DB.items())
papers_subset = []

# Get first ten papers
subset_size = 10
i = 0
while i < subset_size:
    papers_subset.append(papers[i])
    i += 1

# Get random papers
papers_subset[0] = papers[111]
papers_subset[1] = papers[1111]
papers_subset[2] = papers[121]
papers_subset[3] = papers[311]
papers_subset[4] = papers[99]
papers_subset[5] = papers[81]
papers_subset[6] = papers[411]
papers_subset[7] = papers[1211]
papers_subset[8] = papers[1611]
papers_subset[9] = papers[331]

nodes = []
edges = []
years = []
parent_nodes = []
seconds_in_year = 31622400
x = 0
# Get list of years
for paper_id, paper in papers_subset:

    date = ARCHIVEDB[paper_id]['published']
    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')

    if date.year not in years:
        years.append(date.year)
        parent_nodes.append({
            'data': {'id': date.year, 'label': date.year},
            'classes': 'parent_node'
        })

#TEST
years.append(2012)
years.append(2017)
#TEST END
years.sort(reverse=True)
print(years)

# Generate Nodes and Edges
total_height = 1000
number_of_sections = len(years)
section_height = total_height/number_of_sections
for paper_id, paper in papers_subset:
    date = ARCHIVEDB[paper_id]['published']
    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    date_start_of_year = datetime.datetime(date.year, 1, 1)
    seconds_difference = (date - date_start_of_year).total_seconds()
    normalized_date = (seconds_difference/seconds_in_year)
    year_index = years.index(date.year)
    y = round(normalized_date * section_height) + section_height * year_index
    # print(y)
    # print(date)
    nodes.append({
        'data': {'id': paper_id, 'label': str(date.year) + paper.title[:30], 'parent': date.year},
        'position': {'x': x, 'y': y},
        'classes': 'node'
    })
    x += 50
    for reference in paper.references:
        if reference.paperId in papers_subset:
            edges.append({'data': {'id': reference.paperId + "." + paper_id, 'source': reference.paperId, 'target': paper_id}})



# Declare sizing variables
max_width = 500




# Add testing values

parent_nodes.append({
    'data': {'id': '2017', 'label': '2017'},
    'classes': 'parent_node'
})

parent_nodes.append({
    'data': {'id': '2012', 'label': '2012'},
    'classes': 'parent_node'
})

y = round(0.5 * section_height) + section_height * 1

nodes.append({
    'data': {'id': 'test', 'label': 'test', 'parent': '2017'},
    'position': {'x': 160, 'y': y}
})

nodes.append({
    'data': {'id': 'test', 'label': 'test', 'parent': '2012'},
    'position': {'x': 160, 'y': y}
})

# edges.append({'data': {'id': 'test', 'source': nodes[0]['data']['id'], 'target':  nodes[6]['data']['id']}})


# print(nodes)
print(edges)
# print(years)


# Setup App

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        userPanningEnabled=False,
        userZoomingEnabled=False,
        autolock=True,
        layout={'name': 'grid', 'padding': 40, 'fit': True},
        style={'width': '500px', 'height': '500px', 'border': '1px solid black'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'shape': 'circle',
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
            },
            {
                'selector': '.parent_node',
                'style': {
                    'shape': 'rectangle',
                    'text-halign': 'left',
                    'text-margin-x': -1,
                    'font-size': 14,
                    'min-width': '400px',
                    'min-height': '250px',
                }
            },
            {
                'selector': '.node',
                'style': {
                    'background-color': 'white',
                    'border-width': '2px',
                    'border-color': 'green',
                    'shape': 'circle',
                }
            },
            {
                'selector': '.main_node',
                'style': {
                    'background-color': 'white',
                    'border-width': '2px',
                    'width': '50px',
                    'height': '50px',
                }
            },
        ],
        elements=parent_nodes+nodes+edges
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)