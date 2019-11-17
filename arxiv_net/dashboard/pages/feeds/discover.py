from pathlib import Path

import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from arxiv_net.dashboard.server import app
from arxiv_net.utilities import Config
from arxiv_net.dashboard import DB, DB_ARXIV
import dash_core_components as dcc
from collections import Counter


embed_db_path = Path(Config.bert_abstract_embed_db_path)
embeds_tsne_csv_path = embed_db_path.with_name(embed_db_path.name.replace(".p", "_tsne.csv"))
TSNE_CSV = pd.read_csv(embeds_tsne_csv_path, dtype=str, names=["arxiv_id", "x", "y", "z"], skiprows=1)
TSNE_CSV["Category"] = [DB_ARXIV[i]["arxiv_primary_category"]["term"] if i in DB_ARXIV else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["CitationVelocity"] = [DB[i].citationVelocity if i in DB else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["InfluentialCitationCount"] = [DB[i].influentialCitationCount if i in DB else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["Topics"] = [[t.topic for t in DB[i].topics] if i in DB else [] for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["Year"] = [int(DB_ARXIV[i]["published"][:4]) if i in DB_ARXIV else None for i in TSNE_CSV['arxiv_id']]
TSNE_CSV["Title"] = [f"[{i}] {DB[i].title}" if i in DB else None for i in TSNE_CSV['arxiv_id']]


__all__ = ['display_3d_scatter_plot', 'display_click_abstract']


# Discovery feed callbacks

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
    tsne_df = TSNE_CSV.loc[(TSNE_CSV["Category"] == category) &
                           (TSNE_CSV["Year"] <= end) &
                           (TSNE_CSV["Year"] >= start)].sort_values("CitationVelocity")

    topics = sum(tsne_df["Topics"].tolist(), [])
    top_10_topics = [t for t,_ in Counter(topics).most_common(10)]

    axes = dict(title="", showgrid=True, zeroline=False,
                showticklabels=False)
    layout = go.Layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(xaxis=axes, yaxis=axes, zaxis=axes),
        legend_orientation="h",
        autosize=True
    )
    data = []
    for topic in top_10_topics:
        topic_df = tsne_df[tsne_df["Topics"].apply(lambda x: topic in x)]
        scales_col = "InfluentialCitationCount"
        scales_scale = 10
        scales_max = topic_df[scales_col].max() + 1
        scales = [x/scales_max for x in (topic_df[scales_col] + 1).to_list()]
        scales = [max(scales_scale * x, 3) for x in scales]
        scatter = go.Scatter3d(
            name=topic,
            x=topic_df["x"],
            y=topic_df["y"],
            z=topic_df["z"],
            text=topic_df["Title"],
            textposition="top center",
            # showlegend=False,
            mode="markers",
            marker_size=scales,
            # marker_color=tsne_df["InfluentialCitationCount"],
            # marker=dict(size=3, color="#3266c1", symbol="circle"),
            marker=dict(size=3, symbol="circle"),
        )
        data.append(scatter)

    figure = go.Figure(data=data, layout=layout)
    return figure


@app.callback(
    Output("div-plot-click-abstract", "children"),
    [Input("graph-3d-plot-tsne", "clickData"),
     Input("discover-categories", "value")],
)
def display_click_abstract(clickData, dataset):
    if clickData:
        arxiv_id = clickData["points"][0]["text"].split("]")[0][1:]
        abstract = DB[arxiv_id].abstract
        title = DB[arxiv_id].title
        url = DB[arxiv_id].url
        print(abstract)
        return [dcc.Markdown(f"[{title}]({url})"),
                dcc.Markdown(abstract)]
    else:
        return [ dcc.Markdown(""),
                 dcc.Markdown("###### Click a data point on the scatter plot to display its corresponding abstract.")]
