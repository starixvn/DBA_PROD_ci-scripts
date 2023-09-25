# -*- coding: utf-8 -*-

import sys
import os
import docker
sys.path.append('/ci/python/config')
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
class execPackage_nodependency:
    def __init__(self,cf1,zfolder,xfolder,commitId,preCmd):
        self.commitId = commitId
        self.preCmd = preCmd
        self.client =docker.from_env()
        self.zfolder = zfolder
        self.xfolder = xfolder
        self.cf1 = cf1
    def execScripts(self):
        rs = extract(self.zfolder,self.xfolder)
        cf = self.getConfigs_script()
        for c in cf:
            if self.cf1.serverAlias(c['server']):
                c['server'] = self.cf1.serverAlias(c['server'])
            self.execScript(c)
            sDB = self.cf1.standbyDB(c['server'],c['db'])
            if sDB is None:
                return
            for s in sDB:
                c['server'] = s.split(':')[0]
                c['db'] = s.split(':')[1]
                self.execScript(c)
                
    def getConfigs_script(self):
        cf = []
        flist = os.listdir(self.xfolder)
        for f in flist:
            filename = os.path.basename(f)
            if filename.endswith('.config') and 'deploy-order' in filename:
                with open(os.path.join(self.xfolder,f),"rb") as lns:
                    for ln in lns:
                        ln = ln.decode('utf8','ignore')
                        ln = ''.join(x.lower() for x in ln if x in string.printable)
                        ln = ln.split('-')
                        server = ln[0].lower()
                        ln = ln[1].split(':')
                        db = ln[0].lower()
                        scr = os.path.join(self.xfolder,ln[1].strip()+'.sql').lower()
                        cf.append({'server':server,'db':db,'script':scr})
                print(cf)
                return cf
    def execScript(self,config):
        server = config['server']
        db = config['db']
        scr = config['script'].replace('/ci/', '/var/')
        con = self.client.containers.get(server+self.commitId)
        _cmd = self.preCmd+ scr +'"'
        _cmd = _cmd.replace('-d master', '-d '+db)
        print(_cmd,server)        
        re = con.exec_run(cmd=_cmd,detach=False)
 
        
    def execSPs(self):
        rs = extract(self.zfolder,self.xfolder)
        cf = []
        flist = os.listdir(self.xfolder)
        for f in flist:
            filename = os.path.basename(f)
            if filename.endswith('.sql'):
                fpart = filename.split('-')
                server = fpart[2].lower()
                db = fpart[3].lower()
                scr = os.path.join(self.xfolder,f).lower()
                cf.append({'server':server,'db':db,'script':scr})
               
        for c in cf:
            sDB = self.cf1.standbyDB(c['server'],c['db'])
            
            if self.cf1.serverAlias(c['server']):
                c['server'] = self.cf1.serverAlias(c['server'])
            self.execSP(c)
            
            if sDB is None:
                continue
            for s in sDB:
                c['server'] = s.split(':')[0]
                c['db'] = s.split(':')[1]
                self.execSP(c)
            print(c)
            print(sDB)
                
    def execSP(self,config):
        server = config['server']
        db = config['db']
        scr = self.adjustSP(config)
        try:
            con = self.client.containers.get(server+self.commitId)
            
            _cmd = self.preCmd+ scr +'"'
            _cmd = _cmd.replace('-d master', '-d '+db)
            print(_cmd,server)        
            re = con.exec_run(cmd=_cmd,detach=False)
            print(re)
        except Exception as e:
            print(e)
    def adjustSP(self,config):
        server = config['server']
        db = config['db']
        scr = config['script']
        spName = ''
        with open(scr,'rb') as lns:
            fileRS = scr.replace('.sql','') + '_adjust.sql'
            with open(fileRS,"w") as ls:
                for ln in lns:
                    ln = ln.decode('utf8','ignore')
                    ln = ''.join(x for x in ln if x in string.printable)
                    if ('create function' in ln.lower()) or ('create procedure' in ln.lower()):
                        spName = ln.split()[-1]
                        spName = spName.replace('[','')
                        spName = spName.replace(']','')
                        
                        if spName == '':
                            print('can\'t get the sp/function name')
                            return
                        _cmd = self.preCmd+ 'print object_id(\''+spName +'\')"'
                        _cmd = _cmd.replace('-d master', '-d '+db)
                        _cmd = _cmd.replace('-i ','-q ')
                        try:
                            con = self.client.containers.get(server+self.commitId)
                            print(_cmd,server)        
                            re = con.exec_run(cmd=_cmd,detach=False)
                            print(re)
                        except Exception as e:
                            print(e)
                            break
                        if re.output == b' \n':
                            ls.write(ln)
                        else:
                            ls.write(ln.replace('CREATE', 'ALTER'))
                    else:
                        ls.write(ln)
        lns.close()
        ls.close()
        fileRS = fileRS.replace('/ci/', '/var/')
        return fileRS
            
            