# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 16:21:02 2022

@author: brice.nguyen
"""
import os
import string
def modifyLogin(file,destPath):
    with open(file,'rb') as lns:
        fileRS = destPath + os.sep + 'login.sql'
        with open(fileRS,"w") as lg:
            for ln in lns:
                ln = ln.decode('utf8','ignore')
                ln = ''.join(x for x in ln if x in string.printable)
                if ('FROM WINDOWS' in ln) or ('DBA_Script_Instance_Object' in ln) or ('MS_PolicyTsqlExecutionLogin' in ln) or ('MS_PolicyEventProcessingLogin' in ln) or ('distributor_admin' in ln):
                    continue
                ln = ln.replace('[SQLSTATE 01000]', '')
                # if 'dbdist01' in fileName:
                #     print(ln)
                p = ln.split(',')
                for i in range(len(p)):
                    if 'DEFAULT_DATABASE' in p[i]:
                        p[i] = ' DEFAULT_DATABASE = [master]'                        
                ln = ','.join([str(x) for x in p])
                lg.writelines(ln)
    lns.close()
    lg.close()
        
def modifyLinkedServer(file,destPath):
    with open(file,'rb') as lns:
        fileRS = destPath + os.sep + 'linkedserver.sql'
        with open(fileRS,"w") as ls:
            for ln in lns:
                ln = ln.decode('utf8','ignore')
                ln = ''.join(x for x in ln if x in string.printable)
                if 'master.dbo.sp_addlinkedserver' in ln.split() \
                or '\x00m\x00a\x00s\x00t\x00e\x00r\x00.\x00d\x00b\x00o\x00.\x00s\x00p\x00_\x00a\x00d\x00d\x00l\x00i\x00n\x00k\x00e\x00d\x00s\x00e\x00r\x00v\x00e\x00r\x00' in ln.split() :
                    ls.writelines(ln)
    ls.close()
    lns.close()
def modifyAgentJob(file,destPath):
    with open(file,'rb') as lns:
        fileRS = destPath + os.sep + 'agentjob.sql'
        with open(fileRS,"w") as ls:
            for ln in lns:
                ln = ln.decode('utf8','ignore')
                ln = ''.join(x for x in ln if x in string.printable)
                if '@enabled=1' in ln.split():
                    ln = ln.replace('@enabled=1', '@enabled=0')
                ls.writelines(ln)
    ls.close()
    lns.close()
    
def modifyReplication(file,listServer,commitId,destPath):
    with open(file,'rb') as lns:
        fileRS = destPath + os.sep + 'replication.sql'
        with open(fileRS,"w") as ls:
            for ln in lns:
                skip = 0
                ln = ln.decode('utf8','ignore')
                ln = ''.join(x for x in ln if x in string.printable)
                if ('sp_adddistributor' in ln) or ('sp_replicationdboption' in ln) or ("@publication = N'DBTrans_OneCasino'" in ln) or ('IntgTransDB' in ln):
                    continue    
                if 'Change_to_sa_plus_1_Password' in ln:
                    ln = ln.replace('Change_to_sa_plus_1_Password', '1234AA@PASS')
                pattern = "@subscriber_security_mode = 1"
                rePattern = "@subscriber_security_mode = 0, @subscriber_login = N'sa', @subscriber_password = '1234AA@PASS'"
                ln = ln.replace(pattern, rePattern)
                if "@subscriber =" in ln:
                    skip = 1
                for server in listServer:
                    pattern = "@subscriber = N'%s'" % (server.upper())
                #     rePattern = "@subscriber = N'%s'" % (server+commitId)
                    if pattern in ln:
                #         ln = ln.replace(pattern, rePattern)
                        skip =0
                        break
                if skip ==0:
                    ls.writelines(ln)
    ls.close()
    lns.close()