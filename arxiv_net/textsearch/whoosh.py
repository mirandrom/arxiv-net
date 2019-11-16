from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser

from arxiv_net import ROOT_DIR
from arxiv_net.utilities import Config

from tqdm import tqdm
import os.path
import pickle

index_dir = (ROOT_DIR.parent / "data/index").absolute()


def build_index():
    schema = Schema(arxiv_id=ID(stored=True), title=TEXT, abstract=TEXT)
    if not os.path.exists(index_dir):
        print(f"Couldn't find index directory '{index_dir}', creating it now.")
        os.mkdir(index_dir)
    print(f"Creating index in {index_dir}")
    ix = create_in(index_dir, schema)
    writer = ix.writer()

    print("Loading database of papers.")
    db = pickle.load(open(Config.ss_db_path, 'rb'))
    print("Indexing papers.")
    for id, data in tqdm(db.items()):
        writer.add_document(title=data.title, abstract=data.abstract,
                            arxiv_id=id)
    print("Committing index (this might take a while...).")
    writer.commit()
    print("Done.")


def get_index():
    return open_dir(index_dir)


def search_index(query: str, field: str, index):
    parser = QueryParser(field, index.schema)
    parsed_query = parser.parse(query)
    with index.searcher() as searcher:
        return [r['arxiv_id'] for r in searcher.search(parsed_query)]





