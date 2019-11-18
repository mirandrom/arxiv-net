import argparse

import redis

# DB = pickle.load(open(Config.ss_ref_db_path, 'rb'))

_redis = redis.StrictRedis()


# for paper_id, paper in tqdm(DB.items()):
#     if isinstance(paper, dict):
#         paper = _to_dataclass(paper)
#     _redis.set(paper_id, pickle.dumps(paper))
#     for author in paper.authors:
#         _redis.sadd(author.name, paper_id)
#     for topic in paper.topics:
#         _redis.sadd(topic.topic, paper_id)
#     _redis.sadd(paper.title, paper_id)

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
    
    