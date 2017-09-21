#!/usr/bin/env python
import sys
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim 

esxi_ci = sys.argv[1]
esxi_ip = sys.argv[2]
esxi_user='xxx'
esxi_pass='xxx'
esxi_port=443


def esxi_perf(host, ip):
    esxi_instance = connect.SmartConnect(host=ip, user=esxi_user, pwd=esxi_pass, port=int(esxi_port))
    content = esxi_instance.RetrieveContent()
    #print content

    zz =  content.rootFolder.childEntity[0].datastore[1]
    print zz.name
    #print zz.browser
    #print zz.info
    
    #object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    #print object_view
    #l_hosts = object_view.view
    #print l_hosts

    #print content
    #object_view = content.virtualDiskManager.VirtualDiskSpec()
    #print object_view
    
if __name__ == "__main__":
    esxi_perf(esxi_ci, esxi_ip)

