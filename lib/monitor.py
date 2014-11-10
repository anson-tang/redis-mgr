#!/usr/bin/env python
#coding: utf-8

from utils import *

PWD = os.path.dirname(os.path.realpath(__file__))

class Monitor():
    def _live_nutcracker(self, what, format_func = lambda x:x):
        for i in xrange(1000):
            if i%10 == 0:
                header = common.to_blue(' '.join(['%5s' % s.args['port'] for s in self.all_nutcracker]))
                print header

            def get_v(s):
                try:
                    info = s._info_dict()[self.args['cluster_name']]
                    if what not in info:
                        return '-'
                    return format_func(info[what])
                except:
                    return 'xxx'

            print ' '.join([ '%5s' % get_v(s) for s in self.all_nutcracker]) + '\t' + common.format_time(None, '%X')
            sys.stdout.flush()

            time.sleep(1)

    def _live_redis(self, what, format_func = lambda x:x):
        masters = self._active_masters()
        for i in xrange(1000):
            if i%10 == 0:
                old_masters = masters
                masters = self._active_masters()

                old_masters_list = [str(m) for m in old_masters]
                masters_list = [str(m) for m in masters]

                if masters_list == old_masters_list:
                    header = common.to_blue(' '.join(['%5s' % s.args['port'] for s in masters]))
                else:
                    header = common.to_red(' '.join(['%5s' % s.args['port'] for s in masters]))
                print header
            def get_v(s):
                try:
                    info = s._info_dict()
                    if what not in info:
                        return '-'
                    return format_func(info[what])
                except:
                    return 'xxx'
            print ' '.join([ '%5s' % get_v(s) for s in masters]) + '\t' + common.format_time(None, '%X')
            sys.stdout.flush()

            time.sleep(1)

    def live_master_mem(self):
        '''
        monitor used_memory_human:1.53M of master
        '''
        def format(s):
            if strstr(s, 'M'):
                return re.sub('\.\d+', '', s) # 221.53M=>221M
            else:
                return s
        self._live_redis('used_memory_human', format)

    def live_master_qps(self):
        '''
        monitor instantaneous_ops_per_sec of master
        '''
        self._live_redis('instantaneous_ops_per_sec')

    def live_master_slowlog(self):
        '''
        monitor slowlog/second of master
        '''
        def format(s):
            return '%.1f' % s
        self._live_redis('_slowlog_per_sec', format)

    def live_nutcracker_request(self):
        '''
        monitor nutcracker requests/s
        '''
        self._live_nutcracker('requests_INC')

    def live_nutcracker_forward_error(self):
        '''
        monitor nutcracker forward_error/s
        '''
        self._live_nutcracker('forward_error_INC')

    def live_nutcracker_client_error(self):
        '''
        monitor nutcracker client_error/s
        '''
        self._live_nutcracker('client_err_INC')

    def live_nutcracker_inqueue(self):
        '''
        monitor nutcracker forward_error/s
        '''
        self._live_nutcracker('in_queue')

    def live_nutcracker_outqueue(self):
        '''
        monitor nutcracker forward_error/s
        '''
        self._live_nutcracker('out_queue')

    def live_overview(self, cnt=1000):
        '''
        overview monitor info of the cluster (from statlog file)
        '''
        statlog = None
        for i in range(cnt):
            if statlog != self.__get_statlog_filepath(time.time()):
                statlog = self.__get_statlog_filepath(time.time())
                fin = file(statlog)
                fin.seek(0, 2)
                time.sleep(60)
                continue

            line = fin.readline()
            self.__print_statlog_line(line)

            time.sleep(60)

    def __parse_statlog_line(self, line):
        ret = {}
        try:
            js = common.json_decode(line)
        except Exception, e:
            print 'badline'
            return

        ret['timestr'] = js['timestr']
        def sum_redis(what):
            val = 0
            for k,v in js['infos'].items():
                if k.startswith('[redis') and v['role'] == 'master' and what in v:
                    #print k, v['instantaneous_ops_per_sec']
                    val += int(v[what])
            return val

        def sum_proxy(what):
            val = 0
            for k,v in js['infos'].items():
                if not k.startswith('[nut') :
                    continue

                v = v[self.args['cluster_name']]
                if what in v:
                    val += int(v[what])
            return val

        ret['qps'] = sum_redis('instantaneous_ops_per_sec')
        ret['mem'] = sum_redis('used_memory')/1024/1024
        ret['slow'] = sum_redis('_slowlog_per_sec')
        ret['forward_error'] = sum_proxy('forward_error_INC')
        return ret

    def __print_statlog_line(self, line):
        ret = self.__parse_statlog_line(line)
        print TT('$timestr ${qps}q/s ${mem}MB ${slow} ${forward_error}', ret)
        sys.stdout.flush()

    def history(self, cnt=1):
        '''
        history monitor info of the cluster
        '''
        cnt = int(cnt)
        files = glob.glob('data/%s/statlog.*'% self.args['cluster_name'])
        files.sort()
        for f in files[-cnt:]:
            for line in file(f):
                try:
                    self.__print_statlog_line(line)
                except:
                    print 'badline'

    def history_hourly(self, cnt=24):
        '''
        history monitor info of the cluster
        '''
        cnt = int(cnt)
        files = glob.glob('data/%s/statlog.*'% self.args['cluster_name'])
        files.sort()
        for f in files[-cnt:]:
            for line in file(f):
                try:
                    self.__print_statlog_line(line)
                    break
                except:
                    print 'badline'

    def history_daily(self, start=''):
        '''
        history monitor info of the cluster
        '''
        if not start:
            start = common.format_time(time.time()-3600*24, '%Y%m%d')
        start = parse_time(start, '%Y%m%d')
        end = parse_time(common.format_time(None, '%Y%m%d'), '%Y%m%d')   #today

        logging.notice('history_daily %s-%s' %(start, end))

        for d in range(start, end, 3600*24):
            sum_err = 0
            for t in range(d, d+3600*24, 3600):
                timestr = common.format_time_to_hour(t)
                filename = 'data/%s/statlog.%s' % (self.args['cluster_name'], timestr)

                for line in file(filename):
                    try:
                        stat = self.__parse_statlog_line(line)
                        err = int(stat['forward_error'])
                        if err > 0:
                            sum_err += err
                    except:
                        print 'badline'
            print common.format_time_to_hour(d)[:-2], sum_err

    def _monitor(self):
        '''
        - redis
            - connected_clients
            - mem
            - rdb_last_bgsave_time_sec:0
            - aof_last_rewrite_time_sec:0
            - latest_fork_usec
            - slow log
            - hitrate
            - master_link_status:down
        - nutcracker
            - all config of nutcracker is the same
            - forward_error
            - server_err
            - in_queue/out_queue

        save this to a file , in one line:
        {
            'ts': xxx,
            'timestr': xxx,
            'cluster': xxx,
            'infos': {
                '[redis:host:port]': {info}
                '[redis:host:port]': {info}
                '[nutcracker:host:port]': {info}
            },
        }
        '''
        now = time.time()

        infos = {}
        for r in self.all_redis + self.all_sentinel + self.all_nutcracker:
            infos[str(r)] = r._info_dict()
        self._check_warning(infos)

        ret = {
            'ts': now,
            'timestr': common.format_time_to_min(now),
            'cluster': self.args['cluster_name'],
            'infos': infos,
        }

        fout = file(self.__get_statlog_filepath(now), 'a+')
        print >> fout, my_json_encode(ret)
        fout.close()
        timeused = time.time() - now
        logging.notice("monitor @ ts: %s, timeused: %.2fs" % (common.format_time_to_min(now), timeused))

    def __get_statlog_filepath(self, now):
        DIR = os.path.join(PWD, '../data/%s' % self.args['cluster_name'])
        STAT_LOG = os.path.join(DIR, 'statlog.%s' % (common.format_time(now, '%Y%m%d%H'), ))
        common.system('mkdir -p %s' % DIR, None)
        return STAT_LOG

    def _check_warning(self, infos):
        def match(val, expr):
            if type(expr) == set:
                return val in expr
            _min, _max = expr
            return _min <= float(val) <= _max

        def check_redis(node, info):
            if not info or 'uptime_in_seconds' not in info:
                logging.warn('%s is down' % node)
                logging.error('%s is down' % node)
            now = time.time()
            redis_spec = {
                    'connected_clients':          (0, 1000),
                    'used_memory_peak' :          (0, 6*(2**30)),
                    'rdb_last_bgsave_time_sec':   (0, 1000),
                    'aof_last_rewrite_time_sec':  (0, 1000),
                    'latest_fork_usec':           (0, 500*1000), #500ms
                    'master_link_status':         set(['up']),
                    'rdb_last_bgsave_status':     set(['ok']),
                    'rdb_last_save_time':         (now-50*60*60, now),
                    #- hit_rate
                    #- slow log
                }
            if 'REDIS_MONITOR_EXTRA' in dir(conf):
                redis_spec.update(conf.REDIS_MONITOR_EXTRA)
            if 'REDIS_MONITOR_EXTRA' in self.args:
                redis_spec.update(self.args['REDIS_MONITOR_EXTRA'])

            for k, expr in redis_spec.items():
                if k in info and not match(info[k], expr):
                    logging.warn('%s.%s is:\t %s, not in %s' % (node, k, info[k], expr))

        def check_nutcracker(node, info):
            '''
            see NutCracker._info_dict() for fields
            '''
            if not info or 'uptime' not in info:
                logging.warn('%s is down' % node)
                logging.error('%s is down' % node)
                return

            nutcracker_cluster_spec = {
                    'client_connections':  (0, 10000),
                    "forward_error_INC":   (0, 1000),  # in every minute
                    "client_err_INC":      (0, 1000),  # in every minute
                    'in_queue':            (0, 1000),
                    'out_queue':           (0, 1000),
            }
            if 'NUTCRACKER_MONITOR_EXTRA' in dir(conf):
                nutcracker_cluster_spec.update(conf.NUTCRACKER_MONITOR_EXTRA)
            if 'NUTCRACKER_MONITOR_EXTRA' in self.args:
                nutcracker_cluster_spec.update(self.args['NUTCRACKER_MONITOR_EXTRA'])

            #got info of this cluster
            info = info[self.args['cluster_name']]
            for k, expr in nutcracker_cluster_spec.items():
                if k in info and not match(info[k], expr):
                    logging.warn('%s.%s is:\t %s, not in %s' % (node, k, info[k], expr))


        for node, info in infos.items():
            if strstr(node, 'redis'):
                check_redis(node, info)
            if strstr(node, 'nutcracker'):
                check_nutcracker(node, info)

    #def monitor(self):
        #'''
        #a long time running monitor task, write WARN log on bad things happend
        #'''
        #while True:
            #self._monitor()
            #time.sleep(60)

    def check_proxy_config(self):
        '''
        check if all proxy has same config
        '''
        base = self.all_nutcracker[0].get_config()
        for n in self.all_nutcracker[1:]:
            c = n.get_config()
            if c != base:
                logging.warn('config not same: %s vs %s' % (self.all_nutcracker[0], n))
                logging.error('config not same: %s vs %s' % (self.all_nutcracker[0], n))
                logging.debug(base)
                logging.debug(c)

    def slowlog(self):
        '''
        for all redis master, show slow_log in 60 seconds (return 10 at most)
        '''

        def check(n):
            CNT = 10
            conn = redis.Redis(n.args['host'], n.args['port'])
            ret = conn.execute_command('SLOWLOG', 'GET', CNT)
            now = time.time()
            for s in ret:
                t = s[1]
                if now - t < 60: #  slowlog in 60 seconds
                    print s[1], s[2], ' '.join(s[3])

        for n in self._active_masters():
            logging.info('checking: %s' % n)
            check(n)

    def check_kv(self):
        '''
        one all porxy, get/set keys and check
        '''

        @common.retryv2(Exception, tries=4, delay=0.5, backoff=1, logfun=logging.debug)
        def docheck(host, port):
            conn = redis.Redis(host, port)
            prefix = conf.REDIS_MGR_CHECK_PREFIX

            kv = {}
            for i in range(100):
                k = prefix+str(i)
                kv[k] = int(conn.incr(k))

            for i in range(100):
                k = prefix+str(i)
                if kv[k] + 1 != int(conn.incr(k)):
                    logging.warn('check_kv inc not correct: %s' % k)
                    return False
            return True

        def check(host, port):
            try:
                return docheck(host, port)
            except Exception, e:
                logging.warn('check_kv got exception : %s' % e)
                return False

        for n in self.all_nutcracker:
            logging.debug('checking: %s' % n)
            if not check(n.args['host'], n.args['port']):
                logging.warn("check_kv got exception on %s" % n)
                logging.error("check_kv got exception on %s" % n)

    def log_rotate(self):
        '''
        log_rotate for nutcracker.
        '''
        t = common.format_time(None, '%Y%m%d%H')
        for m in self.all_nutcracker[:1]:
            cmd = 'mv log/nutcracker.log log/nutcracker.log.%s' % t
            m._sshcmd(cmd)
            cmd = "pkill -HUP -f '^%s'" % m.args['runcmd']
            m._sshcmd(cmd)

            log_keep_min = 60 * 24 * 2
            cmd = "find log/ -name 'nutcracker.log.2*' -amin +%d 2>/dev/null | xargs rm -f 2>/dev/null 1>/dev/null" % log_keep_min
            m._sshcmd(cmd)

    def _supervisor(self):
        '''
        supervisor for proxy (every 5 seconds)
        this is useless now!!
        '''
        while True:
            try:
                for m in self.all_nutcracker:
                    if not m._alive():
                        logging.warning("%s down, restart it" % m)
                        m.start(timeout=5)
            except Exception, e:
                logging.warn('we got exception: %s on _supervisor task' % e)
                logging.exception(e)
            time.sleep(5)

    def scheduler(self, rdb_hour = 8):
        '''
        start following threads:
            - failover
            - cron of monitor
            - cron of rdb
            - graph web server at default port
        '''
        web_port = self.cmdline.web_port
        thread.start_new_thread(self.failover, ())
        thread.start_new_thread(self._web_server, (int(web_port), ))
        #thread.start_new_thread(self._supervisor, ())                      #this can not work with reconfigproxy

        cron = crontab.Cron()
        cron.add('* * * * *'   , self._monitor)                             # every minute

        cron.add('0,10,20,30,40,50 * * * *'   , self.check_proxy_config, use_thread=True)  # every 10 minute, (check_proxy_config may hang, so we use thread)
        cron.add('* * * * *'   , self.check_kv, use_thread=True)            # every minute, (check_kv may use more than 1 minute, so we use thread)

        cron.add('59 * * * *', self.log_rotate, use_thread=True)            # every hour (log_rotate)

        cron_time = '0 %s * * *' % rdb_hour
        cron.add(cron_time, self.rdb, use_thread=True)                      # every day

        cron_time = '27 %s * * *' % rdb_hour
        cron.add(cron_time, self.aof_rewrite, use_thread=True)              # every day


        cron.run()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
