#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, time
from sys import path
import argparse

def execCmd(cmd):
    r = os.popen(cmd)  
    text = r.read()  
    r.close()  
    return text 

if __name__ == '__main__':
    #参数解析
    parser = argparse.ArgumentParser(description='Merge html files to Index.html')
    parser.add_argument('path',type=str, help='html files path')
    args=parser.parse_args()
    while True:
        f=open('./index.html','w',encoding='utf-8')
        f.write('<!DOCTYPE html><head><meta charset="UTF-8"></head><html><body>')
        f.close()
        execCmd('cat ' + '"%s"/*.html >> ./index.html'%(args.path))
        execCmd('echo "</body></html>" >> ./index.html')
        time.sleep(60)


        