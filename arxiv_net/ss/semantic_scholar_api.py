import requests
import time
from dataclasses import dataclass, field
from typing import List


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


def get_data(arxiv_id):
    r = requests.get(f"http://api.semanticscholar.org/v1/paper/arXiv:{arxiv_id}")
    if not r.ok:
        if r.status_code == 429:
            # TODO: sanity check this
            # rate limit
            time.sleep(10)
        if r.status_code == 404:
            print(f"Error 404 with reason: {r.reason}")
            pass
    else:
        r = r.json()
        r["authors"] = [SsAuthor(**x) for x in r["authors"]]
        r["citations"] = [SsReference(**x) for x in r["citations"]]
        r["references"] = [SsReference(**x) for x in r["references"]]
        r["topics"] = [SsTopic(**x) for x in r["topics"]]
        return SsArxivPaper(**r)

