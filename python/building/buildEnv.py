import sys
sys.path.append('/ci/python/config')
sys.path.append('/ci/python/building')
sys.path.append('/ci/python/running')
sys.path.append('/ci/python/preparing_resource')
from dockerUtil import docker_util
import subprocess as sb
import os
from adjustConfig import modifyLogin,modifyLinkedServer,modifyReplication,modifyAgentJob
from schemaBuild import schema_build
import glob
import time, datetime
from mssql_util import mssql_util
class buildEnv:
    def __init__(self, neededBuild,cf1,cf2,logs):
        self.listServer = cf2.getServerList()
        self.serverList = self.listServer
        self.commitId = cf2.getCommitId()
        self.neededBuild = neededBuild
        self.volumeDir=cf1.getVolumeDir()
        self.dr = docker_util(cf1,cf2,logs)
        self.ports = {}
        self.cons = {}
        self.cf1 = cf1
        self.cf2 = cf2
        self.logs = logs
    def getENV(self):
        if self.checkExistsENV() == 0:
            return None
        else:
            return self
    def checkExistsENV(self):
        self.dr.getContainers()
    def prepareENV(self):
        #create/check needed directory
        for i in self.listServer:
            dir = self.volumeDir + self.commitId + os.sep + i
            try:
                sb.run(['mkdir','-p',dir])
                sb.run(['chmod','777',dir])
                sb.run(['rm -rf *.cer'],shell=True,cwd=self.cf1.getSsbDir())
                for root, subdirs, files in os.walk(self.cf1.getHostBackupDir()):
                    for j in range(len(subdirs)):
                        os.rename(os.path.join(root,subdirs[j]),os.path.join(root,subdirs[j]).lower())
                        subdirs[j] = subdirs[j].lower()
                    for file in files:
                        os.rename(os.path.join(root.lower(), file), os.path.join(root.lower(), file).lower())
                
            except Exception as e:
                self.logs.writeLog(e,i)
            
            destPath = self.cf1.getHostBackupDir()+i
            #check conditions
            try:
                files = glob.glob(self.cf1.getConfigDir()+i+os.sep + 'loginid'+'/create-loginid*')
                files = sorted(files,reverse=True)
                file = files[0]
                modifyLogin(file,destPath)
            except Exception as e:
                self.logs.writeLog("not exists any file in "+self.cf1.getConfigDir()+i+os.sep + 'loginid',i)
            try:
                files = glob.glob(self.cf1.getConfigDir()+i+os.sep + 'linkedserver'+'/*_create-linkedserver_*')
                files = sorted(files,reverse=True)
                file = files[0]
                modifyLinkedServer(file,destPath)
            except Exception as e:
                self.logs.writeLog("not exists any file in "+self.cf1.getConfigDir()+i+os.sep +  'linkedserver',i)
            try:
                files = glob.glob(self.cf1.getConfigDir()+i+os.sep + 'replication'+'/*replication_20*')
                files = sorted(files,reverse=True)
                file = files[0]
                modifyReplication(file,self.listServer,self.commitId,destPath)
            except Exception as e:
                self.logs.writeLog("not exists any file in "+self.cf1.getConfigDir()+i+os.sep +  'replication',i)
            try:
                files = glob.glob(self.cf1.getConfigDir()+i+ os.sep + 'agentjob'+'/*agentjob_20*')
                files = sorted(files,reverse=True)
                file = files[0]
                modifyAgentJob(file,destPath)
            except Exception as e:
                self.logs.writeLog("not exists any file in "+self.cf1.getConfigDir()+i+os.sep +  'agentjob',i)
        return
    def startENV(self):
        self.prepareENV()
        if self.neededBuild == 1:
            self.dr.buildImages()
        self.cons = self.dr.createMssqlContainers()
        time.sleep(30)
        self.dr.execDefaultScripts(self.cons)
        self.ports = self.dr.ports
        dbs = self.cf2.getInitDBs()
        print(datetime.datetime.now())
        self.restoreDBs()
        for sv in dbs:
            if sv not in self.listServer:
                continue
            schema = schema_build(sv, self.cf2.getSchemaPath(), self.cons[sv], dbs, self.logs)
            schema.initSV()
            
    def buildSSB(self):
        for i in self.listServer:
            if i == 'dbcust':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbcust_int_setting_conversation.sql"'
                self.logs.writeLog(_cmd,i)        
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'dbtrans':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbtrans_int_setting_conversation.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'db054':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db054_int_setting_conversation.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'db052':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db052_int_setting_conversation.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'db061':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db061_int_setting_conversation.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
        #create certificates
        for i in self.listServer:
            if i == 'dbcust':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbcust.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'dbtrans':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbtrans.sql"'
                self.logs.writeLog(_cmd,i)        
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'db054':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db054.sql"'
                self.logs.writeLog(_cmd,i)        
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i == 'db052':
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db052.sql"'
                self.logs.writeLog(_cmd,i)         
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)

        #add another servers' certificate
        for i in self.listServer:
            if i in ('dbcust',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbcust_2.sql"'
                self.logs.writeLog(_cmd,i)         
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('dbtrans',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbtrans_2.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db054',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db054_2.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db052',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db052_2.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
           
        #ssb-re-create-product-assembly
        for i in self.listServer:
            if i in ('dbtrans',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbtrans_recreate_product_assembly.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db054',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db054_recreate_product_assembly.sql"'
                self.logs.writeLog(_cmd,i)         
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db052',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db052_recreate_product_assembly.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db061',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db061_recreate_product_assembly.sql"'
                self.logs.writeLog(_cmd,i)         
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
        #renew conversations
        for i in self.listServer:
            if i in ('dbcust',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbcust_renew_conversation.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('dbtrans',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_dbtrans_renew_conversation.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db052',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db052_renew_conversation.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db054',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db054_renew_conversation.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
            if i in ('db061',):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+'/var/backup/ssb/ssb_db061_renew_conversation.sql"'
                self.logs.writeLog(_cmd,i)          
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
    def buildReplication(self):
        for i in self.listServer:
            if i in ('dbcust','dbtrans','db02'):
                con = self.cons[i]
                _cmd = self.cf1.getPreCmd()+ self.cf1.getConBackupDir() +i+'/createpublisher.sql"'
                self.logs.writeLog(_cmd,i)       
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
                _cmd = self.cf1.getPreCmd() + self.cf1.getConBackupDir() + i + '/replication.sql"'
                self.logs.writeLog(_cmd,i)           
                re = con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,i)
    def restoreDBs(self):
        for i in self.cf2.getRestoringPatterns():
            tmp = i.split('.')
            tmp[0] = tmp[0].lower()
            if tmp[0] not in self.serverList:
                continue
            con = self.cons[tmp[0]]
            msSQL = mssql_util(self.commitId, self.cf1.getDriver(), tmp[0], 'mondb', 'sa', '1234AA@PASS',str(self.ports[tmp[0]]))
            sql = msSQL.restoreDBcmd(tmp[0],tmp[1])
            if sql:
                _cmd = '/opt/mssql-tools/bin/sqlcmd -S . -U sa -P 1234AA@PASS -d mondb -Q "'+ sql+'"'
                self.logs.writeLog(_cmd,tmp[0])
                con.exec_run(cmd=_cmd,detach=True)
    
    
    ##wait for restoring done
        for i in self.cf2.getRestoringPatterns():
            tmp = i.split('.')
            tmp[0] = tmp[0].lower()
            if tmp[0] not in self.serverList:
                continue
            msSQL = mssql_util(self.commitId, self.cf1.getDriver(), tmp[0], 'mondb', 'sa', '1234AA@PASS',str(self.ports[tmp[0]]))
            cur = msSQL.connectDB()
            time.sleep(120)
            doneRestore = cur.execute("SELECT count(1) FROM sys.dm_exec_requests WHERE command IN ('RESTORE DATABASE')")
            isRestoring = doneRestore.fetchone()[0]
            while isRestoring:
                msg = 'waiting restore %s on %s' % (tmp[1],tmp[0])
                self.logs.writeLog(msg,tmp[0])
                time.sleep(120)
                doneRestore = cur.execute("SELECT count(1) FROM sys.dm_exec_requests WHERE command IN ('RESTORE DATABASE')")
                isRestoring = doneRestore.fetchone()[0]
            msg = 'done restore %s on %s' % (tmp[1],tmp[0])
            self.logs.writeLog(msg,tmp[0])
        time.sleep(10)          
    def stopENV(self):
        return 1
    def cleanUpEnv(self):
        return 1
        