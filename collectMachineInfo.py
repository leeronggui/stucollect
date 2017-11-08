#!/usr/bin/env python
# coding=utf-8  
import salt.client as sc  
import time
import urllib
import httplib
import json
  
baseInfo = {
"idc_name": "NULL", 
"hostname": "NULL",
"os": "NULL",
"brand": "NULL",
"model": "NULL",
"cpu_num": "NULL",
"cpu_model": "NULL",
"memory": "NULL",
"disk_info": "NULL",
"total_disk": "NULL",
"network_num": "NULL",
"network_model": "NULL", 
"sys_kernel_version": "NULL",
"sn_num": "NULL",
"ip_address": "NULL",
"isVirtual": "NULL" , 
"update_time": "NULL"
} 

class HttpClient():
    def get(self, server, port, location, value={}):
        self.server = server
        self.port = port
        self.location = location
        self.value = value
        data = urllib.urlencode(self.value)
        url = self.location + '?' + data
        # print url
        try:
            httpclient = httplib.HTTPConnection(self.server, self.port,timeout=50)
            httpclient.request('GET', url)
            response = httpclient.getresponse()
            return response.read()
        except Exception as e:
            print e
        finally:
            if httpclient:
                httpclient.close()

    def post(self, server, port, location, value):
        self.server = server
        self.port = port
        self.location = location
        self.value = value
        headers = {"Content-type": "application/json", "Accept": "text/json"}
        #params = urllib.urlencode(self.value)
        params = self.value
        try:
            httpclient = httplib.HTTPConnection(self.server, self.port, timeout=5)
            httpclient.request('POST', self.location, params, headers=headers)
            response = httpclient.getresponse()
            return response.read()
        except Exception as e:
            print e
        finally:
            if httpclient:
                httpclient.close()

###salt调用  
local = sc.LocalClient()  
###目标主机指定  
tgt = "10.6.1.12"  
#tgt = "10.6.1.139"  

###获取grains，disk信息
grains = local.cmd(tgt, "grains.items")
#diskusage = local.cmd(tgt, "disk.usage")
diskusage = local.cmd(tgt, "disk.usage")
def getDiskInfo():
    disk = 0
    try:
        for ip in diskusage.keys():
            for key in diskusage[ip]:
                if "/dev/" in  diskusage[ip][key]['filesystem']:
                    disk = disk + int(diskusage[ip][key]['available']) 
    except Exception as e:
        print e
    disk = disk / 1024 / 1024
    diskG = str(disk) + "G"
    baseInfo['total_disk'] = diskG

def getBaseInfo():
    try:
        for i in grains.keys():  
            ###去掉127.0.0.1这个地址
            baseInfo["hostname"] = grains[i]["nodename"]
            baseInfo["idc_name"] = baseInfo["hostname"].split('-')[0]
            #os = grains[i]['osfinger']
            baseInfo["os"] = grains[i]["os"] + ' ' + grains[i]["osrelease"]
            baseInfo["brand"] = grains[i]['manufacturer']
            baseInfo["model"] = grains[i]['productname']
            baseInfo["cpu_num"] = grains[i]['num_cpus']
            baseInfo["cpu_model"] = grains[i]['cpu_model']
            baseInfo["memory"] = grains[i]['mem_total'] / 1024 + 1
            baseInfo["sys_kernel_version"] = grains[i]['kernelrelease']
            baseInfo["sn_num"] = grains[i]['serialnumber']
            for ipv4 in grains[i]["ipv4"]:
                if ipv4 == "127.0.0.1":
                    continue
                else:
                    baseInfo["ip_address"] = ipv4
            if grains[i]["virtual"] == "physical":
                baseInfo["isVirtual"] = 1
                if "lo" in grains[i]['ip_interfaces'].keys():
                    network_num = len(grains[i]['ip_interfaces']) - 1
                    baseInfo["network_num"] = network_num
            elif grains[i]["virtual"] == "xen":
                baseInfo["isVirtual"] = 0
            baseInfo["update_time"] =  int(time.time())
            return 0
    except Exception, e:  
        print "Exception:", e  

getBaseInfo()
getDiskInfo()
H = HttpClient()
baseInfo_json = json.JSONEncoder().encode(baseInfo)
#print baseInfo_json
print H.post("211.159.165.47", 14320, "/api/v1/serveradd/", baseInfo_json)
