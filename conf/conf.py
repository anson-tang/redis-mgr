#coding: utf-8
#the port: role: x, cluster_id: x, instance:xx
#       2        0              x           xx

#port standard 1
#redis-master   22xxx
#redis-slave    23xxx
#proxy          24xxx 25xxx(status-port)
#sentinel       29xxx

#port standard 2

#redis-master   2xxx
#redis-slave    3xxx
#proxy          4xxx 5xxx(status-port)
#sentinel       9xxx

#we will generate:
#port
#pidfile
#logfile
#dir

#path in the deploy machine
BINARYS = {
    'REDIS_SERVER_BINS'   : '_binaries/redis-*',
    'REDIS_CLI'           : '_binaries/redis-cli',
    'REDIS_SENTINEL_BINS' : '_binaries/redis-sentinel',
    'NUTCRACKER_BINS'     : '_binaries/nutcracker',
}#TODO: check it

BINARYS['MON_BINS'] = '_binaries/mon';
BINARYS['REDIS_REPLAY_AOF'] = '_binaries/redis-replay-aof'

REDIS_MGR_CHECK_PREFIX = 'redis-mgr-check-'

RDB_SLEEP_TIME = 1

#optional
REDIS_MONITOR_EXTRA = {
    'aof_last_rewrite_time_sec':  (0, 1000),
    'rdb_last_bgsave_time_sec':   (-1, 1000),
    'latest_fork_usec':           (0, 500*1000), #500ms
    'used_memory_peak' :          (0, 8*(2**30)),
    'used_memory' :               (0, 4.6*(2**30)),
    '_slowlog_per_sec' :          (0, 1),
}

NUTCRACKER_MONITOR_EXTRA = {
    'client_connections':  (0, 100000),
    "forward_error_INC":   (0, 1000),   # in every minute
    "client_err_INC":      (0, 1000),   # in every minute
    'in_queue':            (0, 1000),
    'out_queue':           (0, 1000),
}

cluster0 = {
    'cluster_name': 'cluster0',
    'user': 'ning',
    'REDIS_MONITOR_EXTRA': {
        'used_cpu_user':              (0, 1),
        '_slowlog_per_sec':           (0, 10),
    },
    'sentinel':[
        ('127.0.0.5:29001', '/tmp/r/sentinel-29001'),
        ('127.0.0.5:29002', '/tmp/r/sentinel-29002'),
        ('127.0.0.5:29003', '/tmp/r/sentinel-29003'),
    ],
    'redis': [
        # master(host:port, install path)       ,  slave(host:port, install path)
        'cluster0-2000:127.0.0.5:2000:/tmp/r/redis-2000', 'cluster0-2000:127.0.0.5:3000:/tmp/r/redis-3000',
        'cluster0-2001:127.0.0.5:2001:/tmp/r/redis-2001', 'cluster0-2001:127.0.0.5:3001:/tmp/r/redis-3001',
        'cluster0-2002:127.0.0.5:2002:/tmp/r/redis-2002', 'cluster0-2002:127.0.0.5:3002:/tmp/r/redis-3002',
        'cluster0-2003:127.0.0.5:2003:/tmp/r/redis-2003', 'cluster0-2003:127.0.0.5:3003:/tmp/r/redis-3003',
    ],
    'nutcracker': [
        ('127.0.0.5:4000', '/tmp/r/nutcracker-4000'),
        ('127.0.0.5:4001', '/tmp/r/nutcracker-4001'),
    ],
}
