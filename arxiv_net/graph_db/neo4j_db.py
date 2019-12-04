import json
from collections import defaultdict
from functools import reduce

from neo4jrestclient.client import GraphDatabase, Node
from tqdm import tqdm

from arxiv_net import SS_CORPUS_PATH

URI = "bolt://localhost:7687"
USER = 'neo4j'
PASS = '2tsRXwBGFV3KYu9'

gdb = GraphDatabase("http://localhost:7474/db/data/", USER, PASS)

QUERIES = {
    "top_authored": """
        MATCH (p:Paper)
        WITH p, SIZE((:Author)-[:AUTHORS]->(p)) as authorCnt
        ORDER BY authorCnt DESC LIMIT 10
        RETURN p.title, authorCnt
    """,
    "top_cited": """
        MATCH (p:Paper) WHERE p.title IS NOT NULL
        WITH p, SIZE((:Paper)-[:CITES]->(p)) as citationCnt
        ORDER BY citationCnt DESC LIMIT 10
        RETURN p.title, citationCnt             
    """,
    "papers_about": """
        MATCH (p:Paper)-[:IS_ABOUT]->(t:Topic {topic_id: 'Reinforcement learning'}) 
        RETURN p, t
    """,
}


def populate_gdb():
    # Placeholders for relationships to be created
    relationships = defaultdict(lambda: defaultdict(set))

    # Read in a part of corpus
    # f = open(SS_CORPUS_PATH / 's2-corpus-178')
    f = open(SS_CORPUS_PATH / 's2-corpus-01')

    # Create a transaction object
    tx = gdb.transaction(for_query=True)

    # Create indices to speed up MERGE
    tx.append("CREATE INDEX ON :Paper(id)")
    tx.append("CREATE INDEX ON :Author(author_id)")
    tx.append("CREATE INDEX ON :Topic(topic_id)")
    tx.commit()

    # Iteratively add papers to the graph
    pbar = tqdm()
    i = 0
    res = list()

    while True:
        pbar.update(1)
        i += 1
        if i % 1000 == 0:
            print("EXECUTING")
            res += tx.commit()
            tx = gdb.transaction(for_query=True)
        if i == 10000:
            break

        paper = f.readline()
        if not paper:
            break
        paper = json.loads(paper)
        paper_id = paper['id']

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

        # Make sure that special symbols are removed from abstract and title
        replace = [('"', '*'), ("'", '*'), ("\\", '(bs)'), ("/", '(fs)')]
        for k in ('paperAbstract', 'title'):
            paper[k] = reduce(lambda s, p: s.replace(*p), [paper[k]] + replace)

        # Add / update Paper node
        q = "MERGE (p:Paper {id: {id}}) SET p = {props} RETURN p.id, p"
        tx.append(q, params={"id": paper_id, "props": paper},
                  returns=(str, Node))

        # Create Topic -> Author relationship
        for topic in topics:
            q = "MERGE (t:Topic {topic_id: {id}}) RETURN t.topic_id, t"
            tx.append(q, params={"id": topic}, returns=(str, Node))
            relationships[paper_id]["IS_ABOUT"].add(topic)

        # Add Author -> Paper relationship
        for author in authors:
            if not author['ids']:
                continue
            assert len(author['ids']) == 1
            author_id = author['ids'][0]

            props = {'name': author['name'], 'author_id': author_id}

            q = "MERGE (a:Author {author_id: {id}}) " \
                "SET a = {props} " \
                "RETURN a.author_id, a"
            tx.append(q, params={"id": author_id, "props": props},
                      returns=(str, Node))
            relationships[author_id]["AUTHORS"].add(paper_id)

        # Add Paper -> Citation or Paper -> Reference relationship
        for is_ref, neighbour_id in zip([0 for _ in references] +
                                        [1 for _ in citations],
                                        references + citations):
            relation = 'REFERENCES' if is_ref else 'CITES'
            q = "MERGE (p:Paper {id: {id}}) RETURN p.id, p"
            tx.append(q, params={"id": neighbour_id}, returns=(str, Node))
            relationships[paper_id][relation].add(neighbour_id)

    print('COMMITING')
    res += tx.commit()
    nodes = {r[0][0]: r[0][1] for r in res}

    with gdb.transaction():
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

    print('DONE CREATING RELATIONSHIPS')
    f.close()


if __name__ == '__main__':
    populate_gdb()
