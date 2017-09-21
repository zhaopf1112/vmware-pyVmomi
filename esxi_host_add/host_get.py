#!/usr/local/bin/python 
#coding:utf-8 
  
import json 
import urllib2 
from urllib2 import URLError 
import sys 
import xlrd
  
class ZabbixTools: 
    def __init__(self): 
        self.url = 'xxx' 
        self.header = {"Content-Type":"application/json"} 

          
    def user_login(self): 
        data = json.dumps({ 
                           "jsonrpc": "2.0", 
                           "method": "user.login", 
                           "params": { 
                                      "user": "xxx", 
                                      "password": "xxx" 
                                      }, 
                           "id": 0 
                           }) 
          
        request = urllib2.Request(self.url, data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
      
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Auth Failed, please Check your name and password:", e.code 
        else: 
            response = json.loads(result.read())
            result.close() 
            self.authID = response['result'] 
            return self.authID 
          
    def host_get(self,hostName): 
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"host.get", 
                           "params":{ 
                                     "output":["hostid","name"], 
                                     "filter":{"host":hostName} 
                                     }, 
                           "auth":self.user_login(), 
                           "id":1, 
                           }) 
          
        request = urllib2.Request(self.url, data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
      
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            if hasattr(e, 'reason'): 
                print 'We failed to reach a server.' 
                print 'Reason: ', e.reason 
            elif hasattr(e, 'code'): 
                print 'The server could not fulfill the request.' 
                print 'Error code: ', e.code 
        else: 
            response = json.loads(result.read())
            result.close() 
            print "Number Of %s: " % hostName, len(response['result']) 
            lens=len(response['result']) 
            if lens > 0:
                return response['result'][0]['name']
            else:
                return ""
if __name__ == "__main__": 
    test = ZabbixTools() 
 
    f=open("host_need_add_oy.csv","w")
    workbook = xlrd.open_workbook('oy.xlsx')
    for row in xrange(workbook.sheets()[0].nrows):
        hostname=workbook.sheets()[0].cell(row,0).value
        
        hostname=hostname.strip()
 
        hostnameGet=test.host_get(hostname)
        if hostnameGet.strip()=='':
            print "%s can not find on zabbix server !\n" % hostnameGet
            f.write(str(hostname) + "\r\n")
            
        else:
            print "%s have exist !\n" % hostnameGet
    f.close()

