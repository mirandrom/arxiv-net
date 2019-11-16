from arxiv_net.paper2vec import bert_as_service
from arxiv_net.utilities import Config, safe_pickle_dump
import pickle

BATCH_SIZE = 256

bert_as_service.run_server()
bc = bert_as_service.run_client()

db = pickle.load(open(Config.db_path, 'rb'))
try:
    bert_title_embed_db = pickle.load(open(Config.bert_title_embed_db_path, 'rb'))
except Exception as e:
    print('error loading bert title embed database:')
    print(e)
    print('starting from an empty database')
    bert_title_embed_db = {}

ids = list(db.keys())
for i in range(len(ids) // BATCH_SIZE):
    ids_batch = ids[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
    embeds_batch = bc.encode([db[id]["title"] for id in ids_batch])
    for id, embed in zip(ids_batch, embeds_batch):
        bert_title_embed_db[id] = embed
    print('Saving database with %d papers to %s' % (
            len(bert_title_embed_db), Config.bert_title_embed_db_path))
    safe_pickle_dump(bert_title_embed_db, Config.bert_title_embed_db_path)