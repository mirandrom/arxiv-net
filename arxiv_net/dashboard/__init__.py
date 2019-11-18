import os
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Set, Dict

import redis
from tqdm import tqdm

from arxiv_net.ss.semantic_scholar_api import _to_dataclass, SsArxivPaper
from arxiv_net.utilities import Config

DASH_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


class RedisDB(dict):
    
    def __init__(self):
        self._redis = redis.StrictRedis()
        self.keys = self._redis.keys()
        super().__init__()
    
    def __getitem__(self, item):
        return pickle.loads(self._redis.get(item))
    
    def __setitem__(self, key, value):
        self._redis.set(key, pickle.dumps(value))
    
    def __contains__(self, item):
        return item in self.keys
    
    def items(self):
        for key in self.keys:
            value = self[key]
            yield key.decode(), value
    
    def values(self):
        for key in self.keys:
            value = self[key]
            yield value


# DB = AUTHORS = TOPICS = TITLES = RedisDB()
print('Loading SS DB')
DB = pickle.load(open(Config.ss_ref_db_path, 'rb'))
print('Loading ArXiv DB')
DB_ARXIV = pickle.load(open(Config.db_path, 'rb'))
print('Loading Similarities')
SIMILARITIES = pickle.load(open(Config.sim_path, 'rb'))

# Indexing db, should be done asynchronously while fetching from SS
PaperID = Title = AuthorName = Topic = str
AUTHORS: Dict[AuthorName, Set[PaperID]] = defaultdict(set)
TOPICS: Dict[Topic, Set[PaperID]] = defaultdict(set)
TITLES: Dict[Title, Set[PaperID]] = defaultdict(set)

LOOKBACKS = [
    'This Week', 'This Month', 'This Year',
    # 'Filter By Year (Callback Popup)'
]

print('Indexing db with authors, titles and topics')
for paper_id, paper in tqdm(DB.items()):
    if paper is None:
        # TODO (Andrei): why are there None's?
        continue
    if isinstance(paper, dict):
        paper = SsArxivPaper(**paper)
        DB[paper_id] = paper
    for author in paper.authors:
        AUTHORS[author.name].add(paper_id)
    for topic in paper.topics:
        TOPICS[topic.topic].add(paper_id)
    TITLES[paper.title].add(paper_id)
