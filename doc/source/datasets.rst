Datasets
********

Semantic Scholar Corpus
=======================

To begin, identify the directory in which the data would be stored and set the
environment variable that maps to it.

.. code-block:: bash

    export SS_CORPUS_DIR=/media/$USER/SS_corpus

Sample
------
For a sample of the corpus download, extract and unzip the file

.. code-block:: bash

    cd $SS_CORPUS_DIR
    wget https://s3-us-west-2.amazonaws.com/ai2-s2-research-public/open-corpus/2019-11-01/sample-S2-records.gz
    unzip sample-S2-records.gz && rm sample-S2-records.gz


Full Corpus
-----------
To download full Semantic Scholar corpus make sure aws-cli is installed

.. code-block:: bash

    pip install aws-cli

Start the resumable download

.. code-block:: bash

    aws s3 sync --no-sign-request s3://ai2-s2-research-public/open-corpus/2019-11-01/ data_dir

Unzip the data files

.. code-block:: bash

    gunzip data_dir/*.gz
    rm data_dir/*.gz  # Remove archived files to free the space

.. note::
    Full instructions on how to download the corpus and its description
    can be found `here <https://api.semanticscholar.org/corpus/download>`_.




