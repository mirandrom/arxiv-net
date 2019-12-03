import json
import pickle
from collections import defaultdict
from typing import Dict

import redis
from neo4jrestclient.client import GraphDatabase, Node
from redisgraph import Node as rNode
from tqdm import tqdm

from arxiv_net import SS_CORPUS_PATH
from arxiv_net.ss.semantic_scholar_api import SsArxivPaper, _asdict
from arxiv_net.utilities import Config

URI = "bolt://localhost:7687"
USER = 'neo4j'
PASS = '2tsRXwBGFV3KYu9'

gdb = GraphDatabase("http://localhost:7474/db/data/", USER, PASS)
# rdb = redis.StrictRedis()

# TODO: load from disk
existing_papers = set()
existing_authors = set()
needs_update = set()

NodeID = str
NodeProperties = dict
Relationship = str
Label = str
# labels = {'Author', 'Paper', 'Topic'}
# nodes: Dict[Label, Dict[NodeID, NodeProperties]] = {l: {} for l in labels}

def populate_gdb():
    # Placeholders for nodes / relationships / labels to be created

    relationships = defaultdict(lambda: defaultdict(set))
    
    # Read in a part of corpus
    f = open(SS_CORPUS_PATH / 's2-corpus-000')
    # f = open(SS_CORPUS_PATH / 'sample-S2-records')
    
    # Create a transaction object
    tx = gdb.transaction(for_query=True)
    
    # Iteratively add papers to the graph
    pbar = tqdm()
    i = 0
    res = list()
    while True:
        pbar.update(1)
        i += 1
        if i % 2000 == 0:
            print("EXECUTING")
            res += tx.commit()
            tx = gdb.transaction(for_query=True)
        if i == 20000:
            break
        
        paper = f.readline()
        if not paper:
            break
        paper = json.loads(paper)
        paper_id = paper['id']
        
        # if rdb.sismember('papers', paper_id) and not rdb.sismember('unidentified_papers', paper_id):
        #     continue
        
        # Ignore papers that are not identifiable
        if not paper['doi']:
            continue
        
        # Ignore papers that do not have abstracts (useless for NLP)
        if not paper['paperAbstract']:
            continue
        
        # Extract information relevant for construction relationships
        authors = paper.pop('authors')
        references = paper.pop('outCitations')
        citations = paper.pop('inCitations')
        topics = paper.pop('entities')
        
        # Remove unnecessary info
        paper.pop('pdfUrls')
        paper.pop('sources')
        
        # Replace weird single quotation mark from S2 with an empty string
        paper = dict(filter(
            lambda x: len(x[1]) != 0 if isinstance(x[1], str) else 1,
            paper.items()
        ))
        
        # Make sure that inner quotes are removed from abstract:
        paper['paperAbstract'] = paper['paperAbstract'].replace('"',
                                                                '*').replace(
            "'", '*').replace("\\", '(bs)').replace("/", '(fs)')
        paper['title'] = paper['title'].replace('"', '*').replace("'",
                                                                  '*').replace(
            "\\", '(bs)').replace("/", '(fs)')
        
        # Add / update Paper node
        s = rNode(paper_id, None, 'Paper', paper).toString()
        if paper_id in needs_update:
            q = f"MATCH (p: Paper) WHERE p.id = '{paper_id}' SET p={s} RETURN p.id, p"
            tx.append(q, returns=(str, Node))
            needs_update.remove(paper_id)
        else:
            tx.append(f"CREATE (p: Paper {s}) RETURN p.id, p", returns=(str, Node))
            existing_papers.add(paper_id)
        
        # Add Author -> Paper relationship
        for author in authors:
            if not author['ids']:
                continue
            assert len(author['ids']) == 1
            author_id = author['ids'][0]
            
            if author_id not in existing_authors:
                s = rNode(author_id, None, 'Author',
                          {'name': author['name'], 'author_id': author_id}
                          ).toString()
                tx.append(f"CREATE (a: Author {s}) RETURN a.author_id, a",
                          returns=(str, Node))
                existing_authors.add(author_id)
            else:
                tx.append(
                    f"MATCH (a: Author) WHERE a.author_id = '{author_id}' RETURN a.author_id, a",
                    returns=(str, Node))
            
            relationships[author_id]["AUTHORS"].add(paper_id)
        
        # Add Paper -> Citation or Paper -> Reference relationship
        for is_ref, neighbour_id in zip([0 for _ in references] +
                                        [1 for _ in citations],
                                        references + citations):
            relation = 'REFERENCES' if is_ref else 'CITES'
            if neighbour_id not in existing_papers:
                tx.append("CREATE (p: Paper {id: {id}}) RETURN p.id, p",
                          params={'id': neighbour_id},
                          returns=(str, Node))
                existing_papers.add(neighbour_id)
                needs_update.add(neighbour_id)
            else:
                tx.append(
                    f"MATCH (p: Paper) WHERE p.id = '{neighbour_id}' RETURN p.id, p",
                    returns=(str, Node))
            
            relationships[paper_id][relation].add(neighbour_id)
    
    print('COMMITING')
    res += tx.commit()
    nodes = {r[0][0]: r[0][1] for r in res}
    
    deferred = set()
    # TODO: check why this silently fails
    with gdb.transaction() as tx:
        for node_id, relationship in tqdm(relationships.items()):
            node = nodes[node_id]
            for relation, relative in relationship.items():
                if relation == 'AUTHORS':
                    rel = nodes[relative.pop()]
                    node.relationships.create(relation, rel)
                    # node.relationships.create(relation, rel, tx='hack')
                else:
                    for relative_id in relative:
                        rel = nodes[relative_id]
                        node.relationships.create(relation, rel)
                        # node.relationships.create(relation, rel, tx='hack')
                    # node.relationships.create(relation, rel)
                    # if rel is None:
                    #     if rel in existing_papers:
                    #         # Already added previously
                    #         tx.append()
                    #
                    #     else:
                    #         # Means we have not added citation during this
                    #         # sample. However, if the node exists we will
                    #         # encounter it later so we can defere the addition of
                    #         # relationship for now.
                    #         pass
    
    f.close()


if __name__ == '__main__':
    populate_gdb()
    exit(0)
    
    papers = pickle.load(open(Config.db_path, 'rb'))
    SS = pickle.load(open(Config.ss_db_path, 'rb'))
    
    for arxivId in tqdm(list(papers)[:1000]):
        # TODO: change to paperId
        q = f"MATCH (n: Paper) WHERE id(n)='{arxivId}' RETURN n"
        result = gdb.query(q, returns=Node)
        
        if result.elements:
            continue
        
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
        paperId = paper['paperId']
        authors = paper.pop('authors')
        references = paper.pop('references')
        citations = paper.pop('citations')
        topics = paper.pop('topics')
        if len(paper['venue']) == 0:
            paper.pop('venue')
        # TODO: assert that `paper` is flat
        
        node = gdb.nodes.create(**paper)
        node.labels.add('Paper')
        
        # Add Author -> Paper relationship
        for author in authors:
            author_id = author['authorId']
            q = f"MATCH (a: Author) WHERE a.author_id='{author_id}' RETURN a"
            author_node = gdb.query(q, returns=node)
            if not author_node.elements:
                # Create author node
                author_node = gdb.nodes.create(**author)
                author_node.labels.add('Author')
                
                # author_node = Node(author_id, None, 'Author', author)
                # author_node = db.run(
                #     f"CREATE (a: Author {author_node.toString()}) "
                #     f"RETURN a"
                # ).data()
            
            # Attach author to the paper
            gdb.relationships.create(author_node, "AUTHORS", node)
        
        # Add Paper -> Citation or Paper -> Reference relationship
        for is_ref, neighbour in zip([0 for _ in references] +
                                     [1 for _ in citations],
                                     references + citations):
            # Identify the reference / citation node
            neighbour_id = neighbour['paperId']
            a_id = neighbour['arxivId']
            
            # # Do not add it yet if we have it in the list
            # # TODO: change to paperId
            # if other['arxivId'] in papers:
            #     continue
            
            q = f"MATCH (p: Paper) WHERE p.paperId='{neighbour_id}' RETURN p"
            neighbour = gdb.query(q, returns=Node)
            if not neighbour.elements:
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
                neighbour = gdb.nodes.create(**neighbour_props)
                neighbour.labels.add('Paper')
            else:
                neighbour = neighbour[0][0]
            
            # Add relationship
            relation = 'REFERENCES' if is_ref else 'CITES'
            gdb.relationships.create(neighbour, relation, node)
        
        for topics in topics:
            pass
