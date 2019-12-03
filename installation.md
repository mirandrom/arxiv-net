`sudo pip3.7 install git+https://github.com/timesong/redisgraph-py.git@master`

# Install Redis
Follow this tutorial to install Redis:
https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-redis-on-ubuntu-16-04

https://stackoverflow.com/questions/56562627/failed-to-start-redis-in-memory-data-store

#  Install RedisGraph module
Install Linux dependencies
`apt-get install build-essential cmake m4 automake peg libtool autoconf`

Clone the repo
`git clone --recurse-submodules https://github.com/RedisGraph/RedisGraph.git`


Build a binary (this may take a minute)
`cd RedisGraph && make`

TODO: check if this is actually working


Update your redis config to make RedisGraph load on redis start
```
export REDISGRAPH_PATH=pwd
echo 'loadmodule $REDISGRAPH_PATH/src/redisgraph.so' >> echo $(redis-cli info | grep config_file | cut -d : -f 2)
```

LAUNCH REDIS WITH:
``