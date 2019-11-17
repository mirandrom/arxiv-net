import os
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set

from tqdm import tqdm

from arxiv_net.utilities import Config

DASH_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

DB = pickle.load(open(Config.ss_db_path, 'rb'))
DB_ARXIV = pickle.load(open(Config.db_path, 'rb'))
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

for paper_id, paper in tqdm(DB.items()):
    if paper is None:
        # TODO (Andrei): why are there None's?
        continue
    for author in paper.authors:
        AUTHORS[author.name].add(paper_id)
    for topic in paper.topics:
        TOPICS[topic.topic].add(paper_id)
    TITLES[paper.title].add(paper_id)
