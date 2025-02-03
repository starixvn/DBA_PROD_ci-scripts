# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('/ci/python/config')
sys.path.append('/ci/python/package')
sys.path.append('/ci/python/building')
sys.path.append('/ci/python/running')
sys.path.append('/ci/python/preparing_resource')
import time
import datetime
from configParser import parser_config
from runningENV import Env
from log import logCI
from extract import extract
import string
class execPackage:
    def __init__(self,zfolder,xfolder,cf1,cf2,logs,env):
        self.logs = logs
        self.zfolder = zfolder
        self.xfolder = xfolder
        self.env = env
    def execScripts(self):
        rs = extract(self.zfolder,self.xfolder)
        if rs == 0:
            self.logs.writeErrLog('extract fail \n zipFolder: %s \n extractFolder: %s' %(self.zfolder,self.xfolder))
        cf = self.getConfigs_script()
        for c in cf:
            self.execScript(c)
    def getConfigs_script(self):
        cf = []
        flist = os.listdir(self.xfolder)
        for f in flist:
            filename = os.path.basename(f)
            if filename.endswith('.config') and 'deploy-order' in filename:
                with open(f,"r") as lns:
                    for ln in lns:
                        ln = ln.decode('utf8','ignore')
                        ln = ''.join(x for x in ln if x in string.printable)
                        ln = ln.split('-')
                        server = ln[0]
                        ln = ln[1].split[':']
                        db = ln[0]
                        scr = ln[1]
                        cf.append({'server':server,'db':db,'script':scr})
                print(cf)
                return cf
    def execScript(self,config):
        server = config['server']
        db = config['db']
        scr = config['script']
        con = self.env.cons[server]
        _cmd = self.cf1.getPreCmd()+ scr +'"'
        _cmd = _cmd.replace('-d master', '-d '+db)
        self.logs.writeLog(_cmd,server)        
        re = con.exec_run(cmd=_cmd,detach=False)
        self.logs.writeErrLog(re.output,server)