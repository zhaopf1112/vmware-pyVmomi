#!/usr/bin/env python
import sys
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim 
import json
import datetime
import sys
esxi_ci = sys.argv[1]
esxi_ip = sys.argv[2]
esxi_user='xxx'
esxi_pass='xxx'
esxi_port=443


def esxi_info(host, ip):
    esxi_instance = connect.SmartConnect(host=ip, user=esxi_user, pwd=esxi_pass, port=int(esxi_port))
    content = esxi_instance.RetrieveContent()
    #print content
    
    disk_info =  content.rootFolder.childEntity[0].datastore[1]
    #print disk_info.name  #disk info 
    ci_code =  content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0].name
    print 'hostname:',ci_code
    #os_type = content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0].
    #file_object = open('vmhostinfo.txt, 'w')
    #file_object = open('vmhostinfo.txt', 'w')
    vmhost_info = content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0].summary
    #print >>file_object,vmhost_info
    #file_object.close()
    os_type = vmhost_info.config.product.fullName
    print 'os_name:',os_type
    #print vmhost_info
    hardware_info = vmhost_info.hardware
    print 'cpu.core:', hardware_info.numCpuCores
    print 'cpu.HTLogicalNum:',hardware_info.numCpuThreads
    print 'cpu.num:',hardware_info.numCpuPkgs
    print 'cpu.model:',hardware_info.cpuModel
    print 'mem.size:',str(hardware_info.memorySize/1024/1024) + 'MB'
    #file_object = open('numericSensorInfo', 'w')
    #ss = content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0].summary.runtime.healthSystemRuntime.systemHealthInfo.numericSensorInfo
    ss = content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0].summary.runtime.healthSystemRuntime.hardwareStatusInfo.storageStatusInfo

    disk_capicaty = 0
    raid1 = 'raid:'
    phy_disk = 'diskinfo:'

    for i in ss:
      if 'RAID' in i.name:
        raid1+=i.name+";"
        disk_ = int(i.name.split(':')[2].replace('GB','').strip())
        disk_capicaty += disk_
      elif 'Data Disk' in i.name:
        phy_disk+=i.name+";"
    print 'disk.totalSize:'+ str(disk_capicaty) + 'GB'
    print phy_disk
    print raid1 
 
    uptime_ = vmhost_info.quickStats.uptime
    print 'uptime:',str(int(uptime_)/60/60/24) + 'days'


 
    #content = esxi_instance.RetrieveContent()
    #object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    #l_hosts = object_view.view
    #object_view.Destroy()
    #esxi_ = l_hosts[0]
    #print esxi_
        




    
if __name__ == "__main__":
    esxi_info(esxi_ci, esxi_ip)

