# -*- coding: utf-8 -*-
"""
Created on Tue Feb 22 09:11:56 2022

@author: brice.nguyen
"""


import docker
import subprocess as sb
import time
import glob
import os
import socket
from configParser import parser_config
class docker_util:
    def __init__(self,cf1,cf2,logs):
        self.listServer = cf2.getServerList()
        self.commitId = cf2.getCommitId()
        self.client = docker.from_env()
        self.networkName = 'sqlCI'+self.commitId
        self.ports = {}
        self.cf1 = cf1
        self.logs = logs
    def createMysqlContainer(self):
        vol = self.gitHostPath + ':' + self.gitHostPath + ':rw'
        con = self.client.containers.run('mysql:8.0.20',environment=['MYSQL_ROOT_PASSWORD=1234AA@PASS'],
                                volumes=[vol],detach=True)   
        return con.attrs['NetworkSettings']['IPAddress']
    def buildImage(self,serverName):
        dockerFileName = 'Dockerfile_'+serverName
        tagName = serverName+':latest'
        self.client.images.build(path='/ci', dockerfile=dockerFileName, tag=tagName,rm=False)
    def execDefaultScripts(self,cons):
        for serverName in self.listServer:
            con = cons[serverName]
            pre_cmd = self.cf1.getPreCmd()
            _cmd = pre_cmd + self.cf1.getConBackupDir() + 'mondb/initmondb.sql"'
            self.logs.writeLog(_cmd,serverName)
            re = con.exec_run(cmd=_cmd,detach=False)
            self.logs.writeErrLog(re.output,serverName)
            print('inited MonDB')
            _cmd = pre_cmd + self.cf1.getConBackupDir() + serverName + '/login.sql"'
            self.logs.writeLog(_cmd,serverName)
            re = con.exec_run(cmd=_cmd,detach=False)
            self.logs.writeErrLog(re.output,serverName)
            print('created login')
            _cmd = pre_cmd + self.cf1.getConBackupDir() + serverName + '/linkedserver.sql"'
            self.logs.writeLog(_cmd,serverName)
            re = con.exec_run(cmd=_cmd,detach=False)  
            self.logs.writeErrLog(re.output,serverName)
            _cmd = pre_cmd + self.cf1.getConBackupDir() + 'mondb/linkedserver.sql"'
            _cmd = _cmd.replace('-i', '-v commitId="'+self.commitId +'" -i' )
            self.logs.writeLog(_cmd,serverName)
            re = con.exec_run(cmd=_cmd,detach=False)
            self.logs.writeErrLog(re.output,serverName)
            print('created linked server')
            if 'dbdist' in serverName:
                _cmd = 'mkdir -m 777 -p /var/opt/mssql/ReplData'
                self.logs.writeLog(_cmd,serverName)
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,serverName)
                _cmd = pre_cmd + self.cf1.getConBackupDir() + serverName+'/createdistributor.sql"'
                self.logs.writeLog(_cmd,serverName)
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,serverName)
                print('inited distributor')            
    def createMssqlContainer(self,serverName,imgName=None):
        backupVolume=[]
        print(serverName,imgName)
        if imgName is None:
            imgName = self.cf1.getImage()
            dataVolume = [self.cf1.getVolumeDir()+ '%s/%s:/var/mssql/:rw'%(self.commitId,serverName)]
            backupVolume = [self.cf1.getHostBackupDir()+':'+self.cf1.getConBackupDir()+':rw',]
        else:
            dataVolume = []
            backupVolume = [self.cf1.getHostBackupDir()+':'+self.cf1.getConBackupDir()+':rw',]
        _hostname = serverName + self.commitId
        _cmd = ''
        _port = self.getPossiblePort()
        self.ports.update({serverName:_port})
        con = None
        re = ''
        try:           
            self.client.images.get(imgName)
            con = self.client.containers.run(imgName
                                         ,environment=self.cf1.getConEnv()
                                         ,volumes=dataVolume + backupVolume
                                         ,ports={'1433/tcp': _port}
                                         ,name=_hostname
                                         ,hostname=serverName
                                         ,network=self.networkName
                                         ,mem_limit='10g'
                                         ,detach=True)

        except docker.errors.ImageNotFound:
            print ('image does not exist')
        except docker.errors.ContainerError:
            self.logs.writeLog('instances for commitId: %s is used' % (self.commitId))
        except Exception as e:
            self.logs.writeLog(e,serverName)
        return con
    def buildImages(self,listServer=None):
        if listServer != None:
            for sv in listServer:
                self.buildImage(sv)
        else:
            for sv in self.listServer:
                self.buildImage(sv)
    def createMssqlContainers(self,listServer=None):
        cons = {}
        try:
            self.client.networks.create(name=self.networkName,driver='bridge',check_duplicate=True)
            msg = 'using network %s' %(self.networkName)
            self.logs.writeLog(msg)
        except:
            msg = 'using network %s' %(self.networkName)
            self.logs.writeLog(msg)
            pass
        if listServer != None:
            for sv in listServer:
                con = self.createMssqlContainer(sv,imgName = self.cf1.getRegistry()+sv)
                cons.update({sv:con})
        else:
            for sv in self.listServer:
                con = self.createMssqlContainer(sv)
                cons.update({sv:con})
        #time.sleep(20)
        for sv in self.listServer:
            s = sb.check_output('docker ps', shell=True)
            s = s.decode()
            _hostname = sv + self.commitId
            while s.find(_hostname) == -1:
                time.sleep(1)
                s = sb.check_output('docker ps', shell=True)
                s = s.decode()
                self.logs.writeLog('waiting for container %s starting' %(cons[sv]),sv)    
            self.logs.writeLog('%s is running on port %d' %(cons[sv],self.ports[sv]))
        return cons
    def getContainers(self):
        cons = {}
        for sv in self.listServer:
            con = self.getContainer(sv,self.commitID)
            cons.update({sv:con})
        return cons
    def getContainer(self, servername,commitID):
        try:
            con = self.client.get(serverName + commitID)
            return con
        except:
            self.logs.writeLog('%s is not exists' %(serverName + commitID))
            return null
    def isPortInUse(self,port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    def getPossiblePort(self):
        for i in range(15401,16401):
            if self.isPortInUse(i) == False:
                return i
    def commitImages(self,cons=None,registryDir=None):
        if cons is None:
            c = self.cons
        else:
            c = cons
        if registryDir is None:
            r = self.cf1.getRegistry()
        else:
            r = registryDir
        for i in self.listServer:
            registry = r + i
            re = c[i].commit(registry,'latest')
            self.logs.writeLog(re,i)
        re = self.dr.client.images.prune(filters={'dangling': True})
        self.logs.writeLog(re)
        return
    def pushImages(self,registryDir=None):
        if registryDir is None:
            r = self.cf1.getRegistry()
        else:
            r = registryDir
        for i in self.listServer:
            registry = r + i
            for line in self.client.api.push(registry, tag= 'latest', stream=True, decode=True):
                if 'Pushing' in line:
                    continue
                self.logs.writeLog(line,i)
        return
    def pullImages(self,registryDir=None):
        if registryDir is None:
            r = self.cf1.getRegistry()
        else:
            r = registryDir
        for i in self.listServer:
            registry = r + i
            re = self.client.api.pull(registry,tag = 'latest')
            self.logs.writeLog(re,i)