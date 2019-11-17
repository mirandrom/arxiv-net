from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import numpy as np
import pandas as pd
import os
import pickle
from pathlib import Path
from arxiv_net.utilities import Config


def generate_embedding(
    embed_db_path: Path, iterations, perplexity, pca_dim, learning_rate
):
    embed_db = pickle.load(embed_db_path.open("rb"))
    arxiv_ids = list(embed_db.keys())
    embeds = np.array([embed_db[i] for i in arxiv_ids])

    print("Running PCA")
    nb_col = embeds.shape[1]
    pca = PCA(n_components=min(nb_col, pca_dim))
    data_pca = pca.fit_transform(embeds)

    print("Running TSNE")
    tsne = TSNE(
        n_components=3,
        n_iter=iterations,
        learning_rate=learning_rate,
        perplexity=perplexity,
        random_state=1337,
    )
    tsne_embeds = tsne.fit_transform(data_pca)

    print("Saving results")
    tsne_embeds_df = pd.DataFrame(tsne_embeds, columns=["x", "y", "z"])
    tsne_embeds_df.index = arxiv_ids
    # TODO: add extra meta data for coloring and shit

    tsne_embeds_path = embed_db_path.with_name(embed_db_path.name.replace(".p", "_tsne.csv"))
    tsne_embeds_df.to_csv(tsne_embeds_path)

    print(f"{tsne_embeds_path} has been generated.")


if __name__ == '__main__':
        iterations = 500
        perplexity=50
        pca_dim = 50
        learning_rate=100
        generate_embedding(Path(Config.bert_abstract_embed_db_path),
                           iterations,
                           perplexity,
                           pca_dim,
                           learning_rate)