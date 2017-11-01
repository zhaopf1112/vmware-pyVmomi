#!/usr/bin/env python
import os
import sys
import yaml
import commands
import logging
import logging.handlers
import atexit
import datetime
import time

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

try:
    esxi_ci = sys.argv[1]
    esxi_ip = sys.argv[2]
except Exception, e:
    print "False, Usage: ", sys.argv[0], "esxi_ci esxi_ip"
    sys.exit(99)

LOG_FILE = "/var/log/esxi.log"
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


def esxi_shutdown(host, ip):
    try:
        logger.debug('Host: %s, IP: %s, Port: %s' % (host, ip, esxi_port))
        esxi_instance = connect.SmartConnect(host=ip, user=esxi_user, pwd=esxi_pass, port=int(esxi_port))
        if not esxi_instance:
            msg = 'Could not connect to the host: %s, %s' % (host, ip)
            logger.error(msg)
            return False, msg
        atexit.register(connect.Disconnect, esxi_instance)

        content = esxi_instance.RetrieveContent()
        object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        l_hosts = object_view.view
        object_view.Destroy()

        vm_objView = content.viewManager.CreateContainerView(content.rootFolder,
                                                             [vim.VirtualMachine],
                                                             True)
        vmList = vm_objView.view
        vm_objView.Destroy()
        for vm in vmList:
            power_state = vm.runtime.powerState

            logger.debug(vm.name + 'powerstate:' + power_state)

            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                logger.debug("powering off vm" + vm.name)
                try:

                    task = vm.PowerOff()
                    logger.debug("vm have poweroffed  " + str(task))
                except vim.fault.InvalidPowerState as err:
                    msg = "Caught vmodl fault: %s" % err.msg
                    logger.exception(msg)
                    return False, msg
            if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
                pass

                #       Enter MaintenanceMode
        try:
            main_mode = l_hosts[0].EnterMaintenanceMode_Task(5)
            logger.debug('EnterMaintenanceMode_Task excuted' + str(main_mode))
        except vim.fault.Timedout as err:
            msg = "Caught vim fault: %s" % err.msg
            logger.exception(msg)
            return False, msg
        time.sleep(30)
        #       Shutdown esxi host
        try:
            shutdown_ = l_hosts[0].ShutdownHost_Task(True)
            logger.debug('shutdown esxi host' + str(shutdown_))
        except vmodl.fault.NotSupported as err:
            msg = "Caught vmodl fault: %s" % err.msg
            logger.exception(msg)
            return False, msg

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
    esxi_shutdown(esxi_ci, esxi_ip)