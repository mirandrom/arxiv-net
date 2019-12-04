Installing |project_name|
=========================

|project_name| requires Python 3.7+ and is available on MacOS and Linux.

Neo4j
-----

Installation and launching instructions for ubuntu can be found
`here <https://datawookie.netlify.com/blog/2016/09/installing-neo4j-on-ubuntu-16.04/>`_


Latest stable version
---------------------

You can install the latest stable version of |project_name| as follows.

.. code-block:: bash

    git clone https://github.com/amr-amr/arxiv-net.git
    pip install arxiv-net # use -e flag if you are a developer


RedisGraph (Experimental)
-------------------------

`sudo pip3.7 install git+https://github.com/timesong/redisgraph-py.git@master`

Install Redis
#############

Follow `this <https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-redis-on-ubuntu-16-04>`_
tutorial to install Redis:

Install RedisGraph module
#########################

Install Linux dependencies

.. code-block:: bash

    apt-get install build-essential cmake m4 automake peg libtool autoconf

Clone the repo

.. code-block:: bash

    git clone --recurse-submodules https://github.com/RedisGraph/RedisGraph.git`


Build a binary (this may take a minute)

.. code-block:: bash

    cd RedisGraph && make

TODO: check if this is actually working

Update your redis config to make RedisGraph load on redis start

.. code-block:: bash

    export REDISGRAPH_PATH=pwd
    echo 'loadmodule $REDISGRAPH_PATH/src/redisgraph.so' >> echo $(redis-cli info | grep config_file | cut -d : -f 2)








