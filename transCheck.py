#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, json, time
import datetime, pytz
import argparse


def execCmd(cmd):  
    r = os.popen(cmd)  
    text = r.read()  
    r.close()  
    return text 

def writeHtml(id, region, js):  
    dstPath='./data/'+args.id+'_'+args.region+'.html'
    f=open(dstPath,'w',encoding='utf-8')
    tz=pytz.timezone('Asia/Shanghai')
    time_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    time_ts=datetime.datetime.now().timestamp()
    styleA='style="background-color:rgb(214, 58, 58)"'
    f.write('<p><span> ID= '+js['id']+' ----- Region= '+js['region']+' ----- UpdateTime= '+time_str+'</span><span style="color:red;" id="%s"></span></p>'%(id+region))
    f.write('<script language="javascript">function %s() {document.getElementById("%s").innerHTML = "    距上次更新："+Math.round(new Date().getTime()/1000-%d)+"秒  若过大请检查是否有后台监控掉线";}setInterval(%s,1000);</script>'
            %(id+region.replace('-','_'),id+region,time_ts,id+region.replace('-','_')))
    f.write('''<table style="border:3px #cccccc solid;" cellpadding="10" border='1'>
               <tr><td>实例状态</td><td>实例名</td><td>IP地址</td>
               <td>创建时间</td><td>流量限制</td><td>已用流量</td>
               </tr>''')
    for instance in js['instances']:
        ts = instance['createdAt']
        dt = pytz.datetime.datetime.fromtimestamp(ts, tz)
        f.write('<tr><td %s>%s</td><td>%s</td><td>%s</td> \
               <td>%s</td><td>%s</td><td>%s</td> \
               </tr>'%(styleA if instance['state']!='running'else'', instance['state'],instance['name'],instance['ipv4']
               ,dt.strftime('%Y-%m-%d %H:%M:%S'),instance['totalTraffic'],instance['usedTraffic'] if 'usedTraffic' in instance else 'None'))
    f.write('</table><p></p><p></p>')           
    f.close()


def updateJson(id, region, instance, usedTraffic):
    # 打开json文件
    dstPath='./data/'+args.id+'_'+args.region+'.json'
    f=open(dstPath,'r',encoding='utf-8') 
    js=json.loads(f.read())
    jsInstances=js['instances']
    f.close()
    # 更新json文件中的数值
    for index,jsInstance in enumerate(jsInstances):
        if jsInstance['name']==instance['name']:
            jsInstances[index].update({
                'usedTraffic':usedTraffic
            })
    # 将改动写回json文件，并更新Html
    js['instances']=jsInstances
    f = open(dstPath,'w',encoding='utf-8')
    f.write(json.dumps(js))
    f.close()
    writeHtml(id, region, js)


def initJson(id, region, instances):
    #初始化json文件
    if not os.path.exists('./data'):
        os.mkdir('./data')
    dstPath='./data/'+args.id+'_'+args.region+'.json'
    if not os.path.exists(dstPath):
        f=open(dstPath,'w',encoding='utf-8')
        f.write('{"id": "%s", "region": "%s", "instances": []}'%(id, region))
        f.close()
    #将不带流量信息的instances信息写入json文件, 并删除json文件中过期的信息
    f=open(dstPath,'r',encoding='utf-8') 
    js=json.loads(f.read())
    jsInstances=js['instances']
    f.close()
    # ①将instances写入json文件
    for instance in instances:
        inserted={
            'state': instance['state']['name'],
            'name': instance['name'],
            'createdAt': instance['createdAt'],
            'ipv4': instance['publicIpAddress'] if instance['state']['name'] == 'running' else 'None',
            'totalTraffic': instance['networking']['monthlyTransfer']['gbPerMonthAllocated']
        }
        if instance['name'] not in map(lambda x:x['name'],jsInstances):
            jsInstances.append(inserted)
        else:
            index=list(map(lambda x:x['name'],jsInstances)).index(instance['name'])
            jsInstances[index].update(inserted)
    # ②删除json文件中已经失效的实例
    for jsInstance in jsInstances:
        if jsInstance['name'] not in map(lambda x:x['name'],instances):
            jsInstances.remove(jsInstance)
    # ③将改动写回json文件，并更新Html
    js['instances']=jsInstances
    f = open(dstPath,'w',encoding='utf-8')
    f.write(json.dumps(js))
    f.close()
    writeHtml(id, region, js)
            

if __name__ == '__main__':
    #参数解析
    parser = argparse.ArgumentParser(description='AWS Lightsail traffic check tools:')
    parser.add_argument('id',type=str, help='AWS_ACCESS_KEY_ID')
    parser.add_argument('key',type=str, help='AWS_SECRET_ACCESS_KEY')
    parser.add_argument('region',type=str, help='AWS_REGION')
    parser.add_argument('--traffic',type=int, help='Debug: Use this traffic setting as the upper limit, in MByte')
    args=parser.parse_args()
    #设置awscli环境变量
    os.environ['AWS_ACCESS_KEY_ID']=args.id
    os.environ['AWS_SECRET_ACCESS_KEY']=args.key
    os.environ['AWS_DEFAULT_REGION']=args.region
    #流量判断, 月初开始
    while True:
        jsonInstances = json.loads(execCmd("aws lightsail get-instances"))
        instances = jsonInstances.get("instances")
        #初始化Json文件，写入与流量无关的信息
        initJson(args.id,args.region,instances)
        for instance in instances:
            instanceStatus = instance.get("state").get("name")
            if instanceStatus != "running":
                continue
            #计算流量
            instanceName = instance.get("name")
            instanceTransfer = instance.get("networking").get("monthlyTransfer").get("gbPerMonthAllocated")
            startTime = int(datetime.datetime.timestamp(datetime.datetime(datetime.date.today().year, datetime.date.today().month, day=1)))
            nowTime = int(datetime.datetime.timestamp(datetime.datetime.now()))
            jsonNetworkIn = json.loads(execCmd("aws lightsail get-instance-metric-data --instance-name %s " \
                                                "--metric-name NetworkIn --period 2700000  " \
                                                "--start-time %d --end-time %d " \
                                                "--unit Bytes --statistics Sum"%(instanceName,startTime,nowTime)))
            jsonNetworkOut = json.loads(execCmd("aws lightsail get-instance-metric-data --instance-name %s " \
                                                "--metric-name NetworkOut --period 2700000  " \
                                                "--start-time %d --end-time %d " \
                                                "--unit Bytes --statistics Sum"%(instanceName,startTime,nowTime)))
            NetworkAllBytes=0
            if jsonNetworkIn.get("metricData") != [] and jsonNetworkOut.get("metricData") != []:
                NetworkInBytes = int(jsonNetworkIn.get("metricData")[0].get("sum"))
                NetworkOutBytes = int(jsonNetworkOut.get("metricData")[0].get("sum"))
                NetworkAllBytes = NetworkInBytes + NetworkOutBytes
            #更新json文件中的流量信息    
            updateJson(args.id, args.region, instance, NetworkAllBytes/1073741824.0)
            #判断流量是否超限
            print("实例名称: %s"%(instanceName))
            print("已使用: ", NetworkAllBytes/1073741824, "GB")
            print("限制: ", instanceTransfer, "GB")
            #Debug Mode
            if args.traffic != None:
                print('Debug Mode: The limit has been set to ',args.traffic, 'MB!')
                instanceTransferBytes=args.traffic*1048576
            else:
                instanceTransferBytes=instanceTransfer*1073741824
            if NetworkAllBytes > instanceTransferBytes:
                execCmd("aws lightsail stop-instance --instance-name %s"%(instanceName))
                print("流量超限已关机")
            else:
                print("安全")
        #暂停一段时间
        print("sleep 30s conut")
        time.sleep(30)
