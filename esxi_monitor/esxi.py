#!/usr/bin/env python
import os
import sys
import yaml
import commands
import logging
import logging.handlers
import atexit
import datetime

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

try:
    esxi_ci = sys.argv[1]
    esxi_ip = sys.argv[2]
except Exception, e:
    print "False, Usage: ", sys.argv[0], "esxi_ci esxi_ip"
    sys.exit(99)

LOG_FILE = "/var/log/zabbix/esxi.log"
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=20 * 1024 * 1024, backupCount=5)
fmt = "%(asctime)s - %(name)s - [%(filename)s:%(lineno)s] - %(levelname)s - %(message)s "
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger(esxi_ci)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

param_yaml = os.path.join(os.path.dirname(__file__), "esxi.yaml").replace('\\', '/')
p_esxi = yaml.load(file(param_yaml, "r"))
esxi_user = p_esxi.get('esxi_user')
esxi_pass = p_esxi.get('esxi_pass')
esxi_port = p_esxi.get('esxi_port')
map_counter = p_esxi.get('map_counter')


def esxi_perf(host, ip):
    try:
        logger.debug('Host: %s, IP: %s, Port: %s' % (host, ip, esxi_port))
        esxi_instance = connect.SmartConnect(host=ip, user=esxi_user, pwd=esxi_pass, port=int(esxi_port))
        if not esxi_instance:
            msg = 'Could not connect to the host: %s, %s' % (host, ip)
            logger.error(msg)
            return False, msg

        atexit.register(connect.Disconnect, esxi_instance)
        content = esxi_instance.RetrieveContent()
        # search_index = content.searchIndex
        # esxi_ = search_index.FindByDnsName(ip, vmSearch=False)
        # logger.debug(esxi_)
        object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        l_hosts = object_view.view
        object_view.Destroy()
        if not l_hosts:
            msg = 'Host: %s, IP: %s, Can not get entity!' % (host, ip)
            logger.error(msg)
            return False, msg
        else:
            esxi_ = l_hosts[0]
            msg = 'Host: %s, IP: %s, entity = %s !' % (host, ip, esxi_)
            logger.debug(msg)

        perf_manager = content.perfManager
        ts = datetime.datetime.now() - datetime.timedelta(hours=1)
        te = datetime.datetime.now()

        l_counter = map_counter.keys()
        l_metric = []
        for counter_ in l_counter:
            l_metric.append(vim.PerformanceManager.MetricId(counterId=counter_, instance=""))
        query = vim.PerformanceManager.QuerySpec(maxSample=1, entity=esxi_, metricId=l_metric, startTime=ts, endTime=te)
        r_query = perf_manager.QueryPerf(querySpec=[query])

        r_perf = {}
        if not r_query:
            msg = 'Host: %s, IP: %s, Can not get perf data!' % (host, ip)
            logger.error(msg)
            return False, msg
        r_last = r_query[0]
        ts_ = r_last.sampleInfo[0].timestamp
        ti_ = r_last.sampleInfo[0].interval
        for kv_ in r_last.value:
            id_ = kv_.id.counterId
            v_ = kv_.value[0]
            logger.debug('CountID: %s, Value: %s, TimeStamp: %s, Interval: %s' % (id_, v_, ts_, ti_))
            r_perf.update({map_counter.get(id_): v_})

        if r_perf:
            # logger.debug(r_perf)
            return True, r_perf
        else:
            msg = "Host: %s, IP: %s, Perf Data is None" % (host, ip)
            return False, msg
    except vmodl.MethodFault as err:
        msg = "Caught vmodl fault: %s" % err.msg
        logger.exception(msg)
        return False, msg
    except Exception as err:
        msg = "Caught exception: %s" % str(err)
        logger.exception(msg)
        return False, msg


def zbx_send(name, key, value):
    if isinstance(value, basestring):
        s_value = '"%s"' % value
    else:
        if not value:
            value = 0
        s_value = '%s' % value
    cmd = '/usr/bin/zabbix_sender -z 127.0.0.1 -s %s -k %s -o %s' % (name, key, s_value)
    s_, o_ = commands.getstatusoutput(cmd)
    if s_:
        logger.warning('%s, %s, %s' % (key, s_, o_))
    return (False, 5) if s_ else (True, 0)

# Start program
if __name__ == "__main__":
    f_, r_ = esxi_perf(esxi_ci, esxi_ip)
    if f_:
        for (k, v) in r_.items():
            f_ &= zbx_send(esxi_ci, k, v)[0]
        if not f_:
            print 'False, zbx_send Failed!'
            sys.exit(2)
        else:
            print 'True, Success'
            sys.exit(0)
    else:
        print 'False, %s' % r_
        sys.exit(1)
