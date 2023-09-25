# -*- coding: utf-8 -*-
"""
Created on Mon May 23 08:50:23 2022

@author: brice.nguyen
"""
import os
import string
import subprocess as sb
import glob
import datetime

class logCI:
    def __init__(self,serverList,cf):
        logDir = cf.getLogDir() + datetime.datetime.now().strftime('%Y%m%d_%H%M00')
        sb.run(['mkdir','-p',logDir])
        self.logFiles ={}
        for sv in serverList:
            logFile = logDir + os.sep + sv +'.log'
            lf = open(logFile,"w")
            self.logFiles.update({sv:lf})
        logFile = logDir + os.sep +'general.log'
        lf = open(logFile,"w")
        self.logFiles.update({'general':lf})
    def writeLog(self,msg,sv='general'):
        print(msg)
        lFile = self.logFiles[sv]
        print(datetime.datetime.now(),file = lFile)
        print(msg,file = lFile)
    def writeErrLog(self,msg,sv='general'):
        if isinstance(msg, str) == False:
            msg = msg.decode()
        lFile = self.logFiles[sv]
        logs = msg.split('\n')
        try:
            for i in range(len(logs)-1):
                if 'Msg' in logs[i]:
                    print(logs[i],file = lFile)
                    print(logs[i+1],file = lFile)
                    print(logs[i])
                    print(logs[i+1])
        except Exception as e:
            print(e,file = lFile)     
    def close(self):
        for sv in self.logFiles:
            self.logFiles[sv].close()