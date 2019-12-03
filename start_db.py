import argparse
import pickle

import redis
from redisgraph import Node, Edge, Graph
from tqdm import tqdm

from arxiv_net.graph_db.queries import Queries
from arxiv_net.ss.semantic_scholar_api import SsArxivPaper, _asdict
from arxiv_net.utilities import Config

redis_con = redis.StrictRedis()
redis_graph = Graph('arxiv', redis_con)


# DB = pickle.load(open(Config.ss_ref_db_path, 'rb'))

# for paper_id, paper in tqdm(DB.items()):
#     if isinstance(paper, dict):
#         paper = _to_dataclass(paper)
#     _redis.set(paper_id, pickle.dumps(paper))
#     for author in paper.authors:
#         _redis.sadd(author.name, paper_id)
#     for topic in paper.topics:
#         _redis.sadd(topic.topic, paper_id)
#     _redis.sadd(paper.title, paper_id)


def populate_graph(graph_name, redis_con):
    # Load movies entities
    movies = {}
    
    papers = pickle.load(open(Config.db_path, 'rb'))
    
    for arxiv_id in papers:
        if redis_graph.query(Queries.exists(arxiv_id)):
            print(arxiv_id)
        
        number_of_actors_query = QueryInfo(
            query="""MATCH (n:actor) RETURN count(n) as actors_count""",
        )
        
        Node()
        
        if arxiv_id not in ss_db:
            ss_data = ss.get_data(arxiv_id)
            if ss_data is not None:
                ss_db[arxiv_id] = ss_data
                num_added_total += 1
        
        if num_added_total % 100 == 0:
            print(
                'Saving database with %d papers to %s' % (
                    len(ss_db), Config.ss_db_path))
            safe_pickle_dump(ss_db, Config.ss_db_path)
    
    with open(
        os.path.dirname(os.path.abspath(__file__)) + '/resources/movies.csv',
        'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            title = row[0]
            genre = row[1]
            votes = int(row[2])
            rating = float(row[3])
            year = int(row[4])
            
            node = Node(label="movie", properties={'title' : title,
                                                   'genre' : genre,
                                                   'votes' : votes,
                                                   'rating': rating,
                                                   'year'  : year})
            movies[title] = node
            redis_graph.add_node(node)
    
    # Load actors entities
    actors = {}
    today = date.today()
    
    with open(
        os.path.dirname(os.path.abspath(__file__)) + '/resources/actors.csv',
        'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            name = row[0]
            yearOfBirth = int(row[1])
            movie = row[2]
            age = today.year - yearOfBirth
            
            if name not in actors:
                node = Node(label="actor",
                            properties={'name': name, 'age': age})
                actors[name] = node
                redis_graph.add_node(node)
            
            if movie in movies:
                edge = Edge(actors[name], "act", movies[movie])
                redis_graph.add_edge(edge)
    
    redis_graph.commit()
    redis_graph.call_procedure("db.idx.fulltext.createNodeIndex", "actor",
                               "name")
    
    return (actors, movies)


def start_db(host: str = 'localhost',
             port: int = 6379,
             ):
    return redis.StrictRedis(host, port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost',
                        help='redis host ip')
    parser.add_argument('--port', type=int, default=6379,
                        help='redis host ip')
    parser.add_argument('--search-query', type=str,
                        default='cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML',
                        help='query used for arxiv API. See http://arxiv.org/help/api/user-manual#detailed_examples')
    parser.add_argument('--start-index', type=int, default=8000,
                        help='0 = most recent API result')
    parser.add_argument('--max-index', type=int, default=30000,
                        help='upper bound on paper index we will fetch')
    parser.add_argument('--results-per-iteration', type=int, default=2000,
                        help='passed to arxiv API')
    parser.add_argument('--wait-time', type=float, default=5.0,
                        help='lets be gentle to arxiv API (in number of seconds)')
    parser.add_argument('--break-on-no-added', type=int, default=0,
                        help='break out early if all returned query papers are already in db? 1=yes, 0=no')
    args = parser.parse_args()
    
    papers = pickle.load(open(Config.db_path, 'rb'))
    SS = pickle.load(open(Config.ss_db_path, 'rb'))
    
    # TODO: use numerical ids for papers
    
    for arxivId in tqdm(list(papers)[:10]):
        # TODO: change to paperId
        result = redis_graph.query(
            f"MATCH (n: Paper) WHERE id(n)='{arxivId}' RETURN n")
        
        if result.is_empty():
            # start a thread that scrapes SS and adds to DB
            # paper = get_data(arxiv_id=arxivId)
            
            # Pre-fill from existing DB
            paper = SS.get(arxivId)
            if isinstance(paper, SsArxivPaper):
                paper = _asdict(paper)
            
            # Happens sometimes
            if paper is None:
                continue
            
            # Add the node to the graph
            paperId = paper.pop('paperId')
            authors = paper.pop('authors')
            references = paper.pop('references')
            citations = paper.pop('citations')
            topics = paper.pop('topics')
            if len(paper['venue']) == 0:
                paper.pop('venue')
                
            # TODO: assert that `paper` is flat
            node = Node(paperId, None, 'Paper', paper)
            redis_graph.add_node(node)
            
            # Add Author -> Paper relationship
            for author in authors:
                author_id = author.pop('authorId')
                author_node = redis_graph.query(
                    f"MATCH (n: Author) WHERE id(n)='{author_id}' RETURN n")
                if author_node.is_empty():
                    # Create author node
                    author_node = Node(author_id, None, 'Author', author)
                    redis_graph.add_node(author_node)
                
                # Attach author to the paper
                redis_graph.add_edge(Edge(author_node, 'AUTHORS', node))
            
            # Add Paper -> Citation or Paper -> Reference relationship
            for is_ref, neighbour in zip([0 for _ in references] +
                                         [1 for _ in citations],
                                         references + citations):
                # Identify the reference / citation node
                neighbour_id = neighbour.pop('paperId')
                a_id = neighbour['arxivId']
                
                # # Do not add it yet if we have it in the list
                # # TODO: change to paperId
                # if other['arxivId'] in papers:
                #     continue
                
                neighbour = redis_graph.query(
                    f"MATCH (n: Paper) WHERE id(n)='{neighbour_id}' RETURN n")
                if neighbour.is_empty():
                    # Get the paper from SS
                    # neighbour = get_data(s2id=neighbour_id)
                    
                    neighbour = SS.get(a_id)
                    if isinstance(neighbour, SsArxivPaper):
                        neighbour = _asdict(neighbour)
                    if neighbour is None:
                        continue
                    
                    neighbour_props = dict(filter(
                        lambda x: isinstance(x[1], str)
                                  and x[0] != 'paperId'
                                  and len(x[1]) != 0,  # empty venues,
                        neighbour.items()
                    ))
                    neighbour = Node(neighbour_id, None, 'Paper',
                                     neighbour_props)
                    redis_graph.add_node(neighbour)
                
                # Add relationship
                relation = 'REFERENCES' if is_ref else 'CITES'
                redis_graph.add_edge(Edge(node, relation, neighbour))
            
            for topics in topics:
                pass

            redis_graph.commit()
