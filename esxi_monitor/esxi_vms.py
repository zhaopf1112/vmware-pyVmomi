#! /usr/bin/env python
import os
import sys
import yaml
import logging
import logging.handlers
import atexit
import json

from pyVim import connect
from pyVmomi import vmodl

if len(sys.argv) < 3:
    sys.exit(99)
else:
    esxi_ci = sys.argv[1]
    esxi_ip = sys.argv[2]

LOG_FILE = "/var/log/zabbix/esxi_vms.log"
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=20 * 1024 * 1024, backupCount=5)
fmt = "%(asctime)s - [%(filename)s:%(lineno)s] - %(levelname)s - %(message)s "
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
        vms_info = content.rootFolder.childEntity[0].vmFolder.childEntity[:]
        vms_list = []
        for i in vms_info:
            temp = {"{#VMSNAME}": i.name}
            vms_list.append(temp)

        result = {"data": vms_list}
        return True, result
    except vmodl.MethodFault as err:
        msg = "Caught vmodl fault: %s" % err.msg
        logger.exception(msg)
        return False, msg
    except Exception as err:
        msg = "Caught exception: %s" % str(err)
        logger.exception(msg)
        return False, msg

# Start program
if __name__ == "__main__":
    r_, d_ = esxi_perf(esxi_ci, esxi_ip)
    if r_:
        print json.dumps(d_, sort_keys=True, indent=4)
    else:
        sys.exit(1)
