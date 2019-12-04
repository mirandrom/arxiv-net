GraphDB
*******

Why graph DB?
=============

Structure
=========

Nodes
-----

Papers
######

Papers have the following properties:

* paperId
* arxivId
* title
* abstract
* year
* venue
* doi
* url
* citationVelocity
* influentialCitationCount


Authors
#######
* author_id
* name

Topics
######
* topic_id

Relationships
-------------

* REFERENCES (from `Paper` to `Paper`)
* CITES (from `Paper` to `Paper`)
* AUTHORS (from `Author` to `Paper`)
* IS_ABOUT (from `Paper` to `Topic`)