#! /usr/bin/env python
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

if len(sys.argv) < 4:
    print False, "Usage: %s [esxi_ci] [esxi_ip] [vms_name]" % sys.argv[0]
    sys.exit(99)
else:
    esxi_ci = sys.argv[1]
    esxi_ip = sys.argv[2]
    esxi_vm = sys.argv[3]

LOG_FILE = "/var/log/zabbix/vms_perf.log"
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=20 * 1024 * 1024, backupCount=5)
fmt = "%(asctime)s - %(name)s - [%(filename)s:%(lineno)s] - %(levelname)s - %(message)s "
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('%s-%s' % (esxi_ci, esxi_vm))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

param_yaml = os.path.join(os.path.dirname(__file__), "esxi.yaml").replace('\\', '/')
p_esxi = yaml.load(file(param_yaml, "r"))
esxi_user = p_esxi.get('esxi_user')
esxi_pass = p_esxi.get('esxi_pass')
esxi_port = p_esxi.get('esxi_port')
map_counter = p_esxi.get('vms_counter')


def vms_perf(host, ip, vms):
    try:
        logger.debug('Host: %s, IP: %s, Port: %s' % (host, ip, esxi_port))
        esxi_instance = connect.SmartConnect(host=ip, user=esxi_user, pwd=esxi_pass, port=int(esxi_port))
        if not esxi_instance:
            msg = 'Could not connect to the host: %s, %s' % (host, ip)
            logger.error(msg)
            return False, msg

        atexit.register(connect.Disconnect, esxi_instance)
        content = esxi_instance.RetrieveContent()
        vms_info = content.rootFolder.childEntity[0].vmFolder.childEntity
        o_vms = None
        for vms_ in vms_info:
            if vms_.name == vms:
                o_vms = vms_
        if o_vms is None:
            msg = 'Could not find the VMS: %s' % esxi_vm
            logger.error(msg)
            return False,
        perf_manager = content.perfManager
        ts = datetime.datetime.now() - datetime.timedelta(hours=1)
        te = datetime.datetime.now()

        l_counter = map_counter.keys()
        l_metric = []
        for counter_ in l_counter:
            l_metric.append(vim.PerformanceManager.MetricId(counterId=counter_, instance=""))
        msg = 'entity = %s ' % vms
        logger.debug(msg)

        query = vim.PerformanceManager.QuerySpec(maxSample=1, entity=o_vms, metricId=l_metric, startTime=ts, endTime=te)
        r_query = perf_manager.QueryPerf(querySpec=[query])
        if not r_query:
            msg = 'Can not get perf data!'
            logger.error(msg)
            return False, msg
        r_last = r_query[0]
        ts_ = r_last.sampleInfo[0].timestamp
        ti_ = r_last.sampleInfo[0].interval
        d_perf = {}
        for kv_ in r_last.value:
            id_ = kv_.id.counterId
            v_ = kv_.value[0]
            k_ = map_counter.get(id_)
            logger.debug('CounterID: %s, CounterName: %s, Value: %s, Time: %s, Interval: %s' % (id_, k_, v_, ts_, ti_))
            d_perf.update({"%s.[%s]" % (k_, vms): v_})
        if d_perf:
            return True, d_perf
        else:
            msg = "Perf Data is None"
            logger.error(msg)
            return False, msg
    except vmodl.MethodFault as err:
        msg = "Caught vmodl fault: %s" % err.msg
        logger.exception(msg)
        return False, msg
    except Exception, e:
        msg = "Caught exception: %s" % str(e)
        logger.exception(msg)
        return False, msg


def zbx_send(host_, key_, value_):
    if isinstance(value_, basestring):
        s_value = '"%s"' % value_
    else:
        s_value = '%s' % value_
    cmd = '/usr/bin/zabbix_sender -z 127.0.0.1 -s %s -k %s -o %s' % (host_, key_, s_value)
    s_, o_ = commands.getstatusoutput(cmd)
    if s_:
        logger.warning('%s, %s, %s' % (key_, s_, o_))
    return (False, 5) if s_ else (True, 0)

# Start program
if __name__ == "__main__":
    f_, r_ = vms_perf(esxi_ci, esxi_ip, esxi_vm)
    if not f_:
        print f_, r_
        sys.exit(1)
    else:
        for (k, v) in r_.items():
            f_ &= zbx_send(esxi_ci, k, v)[0]
        if not f_:
            print 'False, zbx_send Failed!'
            sys.exit(2)
        else:
            print 'True, Success'
            sys.exit(0)
