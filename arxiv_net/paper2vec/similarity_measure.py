import pickle
from multiprocessing import Pool, cpu_count

import numpy as np
from scipy.spatial.distance import cosine
from tqdm import tqdm

from arxiv_net.utilities import Config


def measure_similarity(paper: str, embedding: np.array):
    dist = dict()
    for another_paper, another_embedding in tqdm(embeddings.items()):
        if paper == another_paper:
            continue
        dist[another_paper] = cosine(embedding, another_embedding)
    return dist


if __name__ == '__main__':
    
    db = pickle.load(open(Config.ss_db_path, 'rb'))
    embeddings = pickle.load(open(Config.bert_abstract_embed_db_path, 'rb'))

    with Pool(cpu_count()) as p:
        distances = p.starmap(measure_similarity, embeddings.items())
    
    truncate_sim = dict()
    max_sims = 100
    for paper, dist in zip(embeddings, distances):
        truncate_sim[paper] = dict(sorted(dist.items(), key=lambda x: x[1])[-max_sims:])
        
    sim_file = '/home/ubuntu/arxiv-net/arxiv_net/../data/similarities.p'
    with open(sim_file, 'wb') as f:
        pickle.dump(truncate_sim, f)
    
