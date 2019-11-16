import time
from dataclasses import dataclass
from typing import List, Dict

import requests


@dataclass
class SsTopic:
    """
    Data class for Semantic Scholar topics
    """
    topic: str
    topicId: str
    url: str


@dataclass
class SsAuthor:
    authorId: str
    name: str
    url: str


@dataclass
class SsReference:
    """
    Data class for Semantic Scholar reference
    """
    arxivId: str
    authors: List[str]
    doi: str
    intent: List[str]
    isInfluential: bool
    paperId: str
    title: str
    url: str
    venue: str
    year: int


@dataclass
class SsArxivPaper:
    """
    Data class for arxiv paper object returned by Semantic Scholar API
    """
    abstract: str
    arxivId: str
    authors: List[SsAuthor]
    citationVelocity: int
    citations: List[SsReference]
    doi: str
    influentialCitationCount: int
    paperId: str
    references: List[SsReference]
    title: str
    topics: List[SsTopic]
    url: str
    venue: str
    year: int


def get_data(arxiv_id: str, to_dataclass: bool = False):
    t = 5
    r = requests.get(
        f"http://api.semanticscholar.org/v1/paper/arXiv:{arxiv_id}")
    if not r.ok:
        if r.status_code == 429:
            print(f"Error 429: sleeping for {t} seconds")
            time.sleep(t)
            t *= 2
        if r.status_code == 404:
            print(f"Error 404 with reason: {r.reason}")
            pass
    else:
        r = r.json()
        if to_dataclass:
            return _to_dataclass(r)
        else:
            return r


def _to_dataclass(r: Dict):
    r["authors"] = [SsAuthor(**x) for x in r["authors"]]
    r["citations"] = [SsReference(**x) for x in r["citations"]]
    r["references"] = [SsReference(**x) for x in r["references"]]
    r["topics"] = [SsTopic(**x) for x in r["topics"]]
    return SsArxivPaper(**r)
