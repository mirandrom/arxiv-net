from pathlib import Path

import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from arxiv_net.dashboard.server import app
from arxiv_net.utilities import Config
from arxiv_net.dashboard import DB, DB_ARXIV

embed_db_path = Path(Config.bert_abstract_embed_db_path)
embeds_tsne_csv_path = embed_db_path.with_name(embed_db_path.name.replace(".p", "_tsne.csv"))
TSNE_CSV = pd.read_csv(embeds_tsne_csv_path, dtype=str)
TSNE_CSV["Topic"] = [DB_ARXIV[i]["arxiv_primary_category"]["term"] if i in DB_ARXIV else None for i in TSNE_CSV['Unnamed: 0']]
TSNE_CSV["CitationVelocity"] = [DB[i].citationVelocity if i in DB else None for i in TSNE_CSV['Unnamed: 0']]
TSNE_CSV["Year"] = [int(DB_ARXIV[i]["published"][:4]) if i in DB_ARXIV else None for i in TSNE_CSV['Unnamed: 0']]
TSNE_CSV["Title"] = [DB[i].title if i in DB else None for i in TSNE_CSV['Unnamed: 0']]


__all__ = ['display_3d_scatter_plot']


@app.callback(
    Output("graph-3d-plot-tsne", "figure"),
    [
        Input("discover-categories", "value"),
        Input("slider-discover-year", "value"),
    ],
)
def display_3d_scatter_plot(
        category,
        year_range,
):
    start, end = year_range
    tsne_df = TSNE_CSV.loc[(TSNE_CSV["Topic"] == category) &
                           (TSNE_CSV["Year"] <= end) &
                           (TSNE_CSV["Year"] >= start)].sort_values("CitationVelocity")

    axes = dict(title="", showgrid=True, zeroline=False,
                showticklabels=False)
    layout = go.Layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(xaxis=axes, yaxis=axes, zaxis=axes),
    )

    scatter = go.Scatter3d(
        name=str(tsne_df.index),
        x=tsne_df["x"],
        y=tsne_df["y"],
        z=tsne_df["z"],
        text=tsne_df["Title"],
        textposition="middle center",
        showlegend=False,
        mode="markers",
        marker=dict(size=3, color="#3266c1", symbol="circle"),
    )

    figure = go.Figure(data=[scatter], layout=layout)
    return figure