deploy.py
=========

.. image:: doc/twemproxy-sentinel-cluster.png

this script will deploy a redis cluster(2-128 instances) in **10 minutes**, with:

- redis
- redis-sentinel
- twemproxy

you can deploy/auto-failover/monitor/migrate and perform rolling-upgrades.

with all best practice from our experience (we use **1TB** of cache on production environment)

try it
------

0. prepare::

    sudo apt-get install git python python-pip
    pip install redis
    pip install -e git://github.com/idning/pcl.git#egg=pcl
    pip install -e git://github.com/kislyuk/argcomplete.git#egg=argcomplete
    git clone https://github.com/idning/redis-mgr.git

1. compile ``redis`` and ``twemproxy`` and put them under ``_binaries/`` dir(you may need ``cp redis-server redis-sentinel``)::

    $ ll _binaries/
    total 19M
    1735820 -rwxr-xr-x 1 ning ning 705K 2014-03-24 19:26 nutcracker
    1735818 -rwxr-xr-x 1 ning ning 5.1M 2014-03-24 19:26 redis-sentinel
    1735819 -rwxr-xr-x 1 ning ning 5.1M 2014-03-24 19:26 redis-server
    1735815 -rwxr-xr-x 1 ning ning 3.8M 2014-03-24 19:26 redis-cli
    1735809 -rwxr-xr-x 1 ning ning  28K 2014-03-24 19:26 redis-check-aof
    1735801 -rwxr-xr-x 1 ning ning 3.7M 2014-03-24 19:26 redis-benchmark

2. choose your config filename::

    export REDIS_DEPLOY_CONFIG=conf && . bin/active

   you can use a private config file ``confconf_private.py`` and do ``export REDIS_DEPLOY_CONFIG=conf_private``

3. edit conf/conf.py

4. make sure you can ssh to target machine without having to input a password (use ``ssh-copy-id``)

5. run::

    $ ./bin/deploy.py cluster0 -h
    $ ./bin/deploy.py cluster0 deploy
    $ ./bin/deploy.py cluster0 start
    $ ./bin/deploy.py cluster0 scheduler --web_port 8008 (run this in screen or somehow on background)

monitor pages
-------------

.. image:: doc/redis-mgr-chart.png

config
------

::

    cluster0 = {
        'cluster_name': 'cluster0',
        'user': 'ning',
        'sentinel':[
            ('127.0.0.5:29001', '/tmp/r/sentinel-29001'),
            ('127.0.0.5:29002', '/tmp/r/sentinel-29002'),
            ('127.0.0.5:29003', '/tmp/r/sentinel-29003'),
        ],
        'redis': [
            # master(host:port, install path)       ,  slave(host:port, install path)
            ('127.0.0.5:20000', '/tmp/r/redis-20000'), ('127.0.0.5:21000', '/tmp/r/redis-21000'),
            ('127.0.0.5:20001', '/tmp/r/redis-20001'), ('127.0.0.5:21001', '/tmp/r/redis-21001'),
            ('127.0.0.5:20002', '/tmp/r/redis-20002'), ('127.0.0.5:21002', '/tmp/r/redis-21002'),
            ('127.0.0.5:20003', '/tmp/r/redis-20003'), ('127.0.0.5:21003', '/tmp/r/redis-21003'),
        ],
        'nutcracker': [
            ('127.0.0.5:22000', '/tmp/r/nutcracker-22000'),
            ('127.0.0.5:22001', '/tmp/r/nutcracker-22001'),
            ('127.0.0.5:22002', '/tmp/r/nutcracker-22002'),
        ],
    }

this will gen ``sentinel``  config::

    sentinel monitor cluster0-20000 127.0.0.5 20000 2
    sentinel down-after-milliseconds  cluster0-20000 60000
    sentinel failover-timeout cluster0-20000 180000
    sentinel parallel-syncs cluster0-20000 1

    sentinel monitor cluster0-20001 127.0.0.5 20001 2
    sentinel down-after-milliseconds  cluster0-20001 60000
    sentinel failover-timeout cluster0-20001 180000
    sentinel parallel-syncs cluster0-20001 1

and ``twemproxy`` config::

    cluster0:
      listen: 127.0.0.5:22000
      hash: fnv1a_64
      distribution: modula
      preconnect: true
      auto_eject_hosts: false
      redis: true
      backlog: 512
      client_connections: 0
      server_connections: 1
      server_retry_timeout: 2000
      server_failure_limit: 2
      servers:
        - 127.0.0.5:20000:1 cluster0-20000
        - 127.0.0.5:20001:1 cluster0-20001

the name ``cluster0-20000`` is named by the orig master,
if slave uses a different port, the server ``host:port``  of ``cluster0-20000`` can be ``127.0.0.5:20000`` or ``127.0.0.5:21000``

usage
-----

choose your config filename::

    export REDIS_DEPLOY_CONFIG=conf && . bin/active

::

    ning@ning-laptop:~/idning-github/redis-mgr$ ./bin/deploy.py cluster0 -h
    usage: deploy.py [-h] [-v] [-o LOGFILE] clustername op [cmd [cmd ...]]

    positional arguments:
      clustername           cluster0
      op                    migrate src dst : migrate a redis instance to another machine
                            web_server [port]: None
                            deploy          : deploy the binarys and config file (redis/sentinel/nutcracker) in this cluster
                            start           : start all instance(redis/sentinel/nutcracker) in this cluster
                            stop            : stop all instance(redis/sentinel/nutcracker) in this cluster
                            printcmd        : print the start/stop cmd of instance
                            status          : get status of all instance(redis/sentinel/nutcracker) in this cluster
                            log             : show log of all instance(redis/sentinel/nutcracker) in this cluster
                            rediscmd cmd    : run redis command against all redis instance, like 'INFO, GET xxxx'
                            mastercmd cmd   : run redis command against all redis Master instance, like 'INFO, GET xxxx'
                            rdb             : do rdb in all redis instance,
                            aof_rewrite     : do aof_rewrite in all redis instance
                            randomkill      : random kill master every mintue (for test failover)
                            sshcmd cmd      : ssh to target machine and run cmd
                            reconfigproxy   : sync the masters list from sentinel to proxy
                            failover        : catch failover event and update the proxy configuration
                            nbench [cnt]    : run benchmark against nutcracker
                            mbench [cnt]    : run benchmark against redis master
                            stopbench       : you will need this for stop benchmark
                            live_master_mem : monitor used_memory_human:1.53M of master
                            live_master_qps : monitor instantaneous_ops_per_sec of master
                            live_nutcracker_request : monitor nutcracker requests/s
                            live_nutcracker_forward_error : monitor nutcracker forward_error/s
                            live_nutcracker_inqueue : monitor nutcracker forward_error/s
                            live_nutcracker_outqueue : monitor nutcracker forward_error/s
                            live_overview [cnt]: overview monitor info of the cluster (from statlog file)
                            history [cnt]   : history monitor info of the cluster
                            upgrade_nutcracker : None
                            log_rotate      : log_rotate for nutcracker.
                            scheduler       : start following threads:
      cmd                   the redis/ssh cmd like "INFO"



these commands will affect the online running cluster status:

- start                 (only if master/slave connection is not running)
- stop                  (will ask for confirmation)
- reconfigproxy         (only if proxy config is out of date)
- randomkill            (will start it later)
- migrate

start cluster::

    $ ./bin/deploy.py cluster0 deploy

    $ ./bin/deploy.py cluster0 start
    2013-12-26 14:47:47,385 [MainThread] [NOTICE] start redis
    2013-12-26 14:47:47,622 [MainThread] [INFO] [redis:127.0.0.5:20000] start ok in 0.23 seconds
    2013-12-26 14:47:47,848 [MainThread] [INFO] [redis:127.0.0.5:21000] start ok in 0.22 seconds
    2013-12-26 14:47:48,099 [MainThread] [INFO] [redis:127.0.0.5:20001] start ok in 0.24 seconds
    2013-12-26 14:47:48,369 [MainThread] [INFO] [redis:127.0.0.5:21001] start ok in 0.27 seconds
    2013-12-26 14:47:50,788 [MainThread] [NOTICE] start sentinel
    2013-12-26 14:47:51,186 [MainThread] [INFO] [sentinel:127.0.0.5:29001] start ok in 0.39 seconds
    2013-12-26 14:47:51,452 [MainThread] [INFO] [sentinel:127.0.0.5:29002] start ok in 0.26 seconds
    2013-12-26 14:47:51,820 [MainThread] [INFO] [sentinel:127.0.0.5:29003] start ok in 0.35 seconds
    2013-12-26 14:47:51,820 [MainThread] [NOTICE] start nutcracker
    2013-12-26 14:47:52,082 [MainThread] [INFO] [nutcracker:127.0.0.5:22000] start ok in 0.26 seconds
    2013-12-26 14:47:52,364 [MainThread] [INFO] [nutcracker:127.0.0.5:22001] start ok in 0.28 seconds
    2013-12-26 14:47:52,573 [MainThread] [INFO] [nutcracker:127.0.0.5:22002] start ok in 0.21 seconds
    2013-12-26 14:47:52,573 [MainThread] [NOTICE] setup master->slave
    2013-12-26 14:47:52,580 [MainThread] [INFO] setup [redis:127.0.0.5:20000]->[redis:127.0.0.5:21000]
    2013-12-26 14:47:52,580 [MainThread] [INFO] [redis:127.0.0.5:21000] /home/ning/idning-github/redis/src/redis-cli -h 127.0.0.5 -p 21000 SLAVEOF 127.0.0.5 20000
    OK
    ...

run cmd on each master::

    $ ./bin/deploy.py cluster0 mastercmd 'get "hello"'
    2013-12-24 13:51:39,748 [MainThread] [INFO] [RedisServer:127.0.0.5:20000]: get "hello"
    [RedisServer:127.0.0.5:20000] xxxxx
    2013-12-24 13:51:39,752 [MainThread] [INFO] [RedisServer:127.0.0.5:20001]: get "hello"
    [RedisServer:127.0.0.5:20001]
    2013-12-24 13:51:39,756 [MainThread] [INFO] [RedisServer:127.0.0.5:20002]: get "hello"
    [RedisServer:127.0.0.5:20002]
    2013-12-24 13:51:39,760 [MainThread] [INFO] [RedisServer:127.0.0.5:20003]: get "hello"
    [RedisServer:127.0.0.5:20003] world

dump rdb for every redis instance::

    $ ./bin/deploy.py cluster0 rdb

monitor qps/memory::

    $ ./bin/deploy.py cluster0 mq
    2013-12-24 14:21:05,841 [MainThread] [INFO] start running: ./bin/deploy.py -v cluster0 mq
    2013-12-24 14:21:05,842 [MainThread] [INFO] Namespace(cmd=None, logfile='log/deploy.log', op='mq', target='cluster0', verbose=1)
    20000 20001 20002 20003
        6     5     5     6
        6     6     5     6
        6     6     5     6
     4741     6     6     6
    33106     5     5     6
    46639     8     7     7
    42265     6     5     7

run benchmark::

    $ ./bin/deploy.py cluster_offline0 bench
    $ ./bin/deploy.py cluster_offline0 mbench

modify config::

    $ ./bin/deploy.py cluster_offline0 mastercmd ' CONFIG GET save' -v
    $ ./bin/deploy.py cluster_offline0 mastercmd 'CONFIG SET save "10000 1000000"' -v

enable auto-complete
--------------------

::

    export REDIS_DEPLOY_CONFIG=conf

    pip install argcomplete
    $ . ./bin/active

    ning@ning-laptop ~/idning-github/redis-mgr$ ./bin/deploy.py cluster0 r<TAB>
    randomkill     rdb            reconfigproxy  rediscmd


gen_conf
--------

on ``bin/gen_conf.py`` use this ::

    BASEDIR = '/tmp/r'
    HOSTS = [
            '127.0.1.1',
            '127.0.1.2',
            '127.0.1.3',
            '127.0.1.4',
            ]
    MASTER_PER_MACHINE = 2
    SLAVE_PORT_INCREASE = 10000

it will gen the deploy.py config like this:

.. image:: doc/twemproxy-sentinel-cluster.png

migrate redis instance
----------------------

if we have 32 masters in 16 machines

1. expansion: move 2*32 instances on 16 machines to 32/64 machines (larger memory)
2. maintenance: one of the machines is down, we have to move data to another machine.

steps:

- pre_check,
- force_src_be_slave,
- deploy_dst,
- add_dst_as_slave,
- cleanup,
- sentinel_reset,
- update_config,

usage::

    $ ./bin/deploy.py cluster0 migrate cluster0-22000:127.0.0.5:23000:/tmp/r/redis-23000 cluster0-22000:127.0.0.5:50015:/tmp/r/redis-50015
    ...
    2014-02-27 19:21:58,667 [MainThread] [INFO] deploy [redis:127.0.0.5:50015]
    2014-02-27 19:21:59,774 [MainThread] [INFO] [redis:127.0.0.5:50015] start ok in 0.19 seconds
    2014-02-27 19:21:59,775 [MainThread] [NOTICE] add_dst_as_slave
    2014-02-27 19:21:59,790 [MainThread] [INFO] [redis:127.0.0.5:50015] /home/ning/idning-github/redis/src/redis-cli -h 127.0.0.5 -p 50015 SLAVEOF 127.0.0.5 22000
    OK
    2014-02-27 19:21:59,801 [MainThread] [INFO] [redis:127.0.0.5:50015]: {'used_memory': '342432', 'master_link_status': 'down', 'slave_repl_offset': '-1'}
    2014-02-27 19:22:00,811 [MainThread] [INFO] [redis:127.0.0.5:50015]: {'used_memory': '342464', 'master_link_status': 'down', 'slave_repl_offset': '-1'}
    2014-02-27 19:22:01,820 [MainThread] [INFO] [redis:127.0.0.5:50015]: {'used_memory': '363456', 'master_link_status': 'up', 'slave_repl_offset': '5998625'}
    2014-02-27 19:22:01,821 [MainThread] [NOTICE] cleanup
    2014-02-27 19:22:02,156 [MainThread] [INFO] [redis:127.0.0.5:23000] stop ok in 0.11 seconds
    2014-02-27 19:22:02,156 [MainThread] [NOTICE] sentinel_reset
    2014-02-27 19:22:02,165 [MainThread] [NOTICE] update_config
    2014-02-27 19:22:02,166 [MainThread] [INFO] AppendConfig:cluster0['migration'] = []
    2014-02-27 19:22:02,166 [MainThread] [INFO] AppendConfig:cluster0['migration'].append('cluster0-22000:127.0.0.5:23000:/tmp/r/redis-23000=>cluster0-22000:127.0.0.5:50015:/tmp/r/redis-50015')

this command will modify the conf.py::

    cluster0['migration'] = []
    cluster0['migration'].append('cluster0-22000:127.0.0.5:23000:/tmp/r/redis-23000=>cluster0-22000:127.0.0.5:50015:/tmp/r/redis-50015')

the "migration" section will auto load on next run::

    $ ./bin/deploy.py cluster0 status
    2014-02-27 19:24:24,815 [MainThread] [NOTICE] start running: ./bin/deploy.py -v cluster0 status
    2014-02-27 19:24:24,820 [MainThread] [NOTICE] status redis
    2014-02-27 19:24:24,825 [MainThread] [INFO] [redis:127.0.0.5:22000] uptime 29815 seconds
    2014-02-27 19:24:24,831 [MainThread] [INFO] [redis:127.0.0.5:50015] uptime 145 seconds
    ...
    2014-02-27 19:24:24,893 [MainThread] [NOTICE] status master-slave
    cluster0-22000 [redis:127.0.0.5:22000] <- 127.0.0.5:50015
    cluster0-22001 [redis:127.0.0.5:22001] <- 127.0.0.5:23001
    cluster0-22002 [redis:127.0.0.5:22002] <- 127.0.0.5:23002
    cluster0-22003 [redis:127.0.0.5:22003] <- 127.0.0.5:23003

mon as supervisor of twemproxy
------------------------------

mon: https://github.com/visionmedia/mon

this is optional for redis-mgr:

1. compile mon and put it in ``_binaries/``.
2. add config::

    BINARYS['MON_BINS'] = '_binaries/mon';

3. ./bin/deploy.py cluster0 upgrade_nutcracker

Dependencies
============

- `pcl <https://github.com/idning/pcl>`_
- `redis-py <https://github.com/andymccurdy/redis-py>`_ (<=2.9.0)
- `argcomplete <https://github.com/kislyuk/argcomplete>`_ (optional)
- `mon <https://github.com/visionmedia/mon>`_ (optional)
- if you are using python 2.7.3, you will need `this patch <http://bugs.python.org/msg158754>`_ to disable noise from threading

Authors
=======

- @idning
- @cen-li

TODO
====

1. scheduler for many clusters, we will need it! (we can use a shell script)
2. monitor ``SLOW LOG``
3. #live monitor for nutcracker
4. #nc to get nutcracker status will fail in background::

      nohup ./bin/deploy.py cluster0 scheduler  &

   we use telnetlib instead
5. #migrate of redis instance
6. #migrate data over cluster.
7. #a live command for cluster overview info(qps, mem, hit-rate)
8. make start cmd reentrant(slaveof cmd)
9. add ``max-mem`` config. on migration, makesure the max-mem config the same.
10. #upgrade nutcracker instance, support --filter
11. #add check_proxy_cfg

Graph
=====

- redis
    - mlive_mem
    - mlive_qps
- twemproxy
    - nlive_request
    - nlive_forward_error
    - nlive_inqueue
    - nlive_outqueue

- for cluster and for each instance
- support more than one cluster.
- do not need database
