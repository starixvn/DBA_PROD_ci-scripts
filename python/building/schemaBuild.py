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
import multiprocessing

class schema_build:
    def __init__(self,server, schemaPath,con,dbs,logs,_cmd = '/opt/mssql-tools/bin/sqlcmd -S . -U sa -P 1234AA@PASS -i '):
        self.con = con
        self.dbs = dbs
        self.cmd = _cmd
        self.server = server
        self.schemaPath = schemaPath + server + os.sep
        self.logs = logs
    def adjustCreateDB(self,file,dbpath):
        with open(file,'rb') as lns:
            h, fileName = os.path.split(file)
            db = fileName[:len(fileName)-4]
            fileRS = h + os.sep + db+'_adjust.sql'
            checkDupFile = []
            dup = 1
            with open(fileRS,"w") as ls:
                ls.write('use master\n')
                ls.write('go\n')
                ls.write("if db_id('"+db+"') is not null\n")
                ls.write('begin\n')
                ls.write('ALTER DATABASE '+db+' SET SINGLE_USER WITH ROLLBACK IMMEDIATE;\n')
                ls.write('DROP DATABASE '+db+'\n')
                ls.write('end\n')
                ls.write('go\n')
                for ln in lns:
                    ln = ln.decode('utf8','ignore')
                    ln = ''.join(x for x in ln if x in string.printable)
                    if 'READ_ONLY' in ln:
                        continue
                    if 'use ['+db.lower()+']' in ln.lower():
                        continue
                    p = ln.split(',')
                    for i in range(len(p)):
                        if ' FILENAME = ' in p[i]:
                            fn = p[i].split('\\')[-1]
                            if fn not in checkDupFile:
                                checkDupFile.append(fn)
                            else:
                                fn = str(dup)+'_'+fn
                                dup += 1
                            p[i] = " FILENAME = N'" + dbpath + fn                       
                        if ' SIZE = ' in p[i]:
                            if '.ldf' in ln.lower():
                                p[i] = ' SIZE = 20MB'
                            else:
                                p[i] = ' SIZE = 512KB'
                            
                    ln = ','.join([str(x) for x in p])
                    ls.write(ln)
        ls.close()
        lns.close()
    def adjustCreateTB(self,file,db):
        with open(file,'rb') as lns:
            h, fileName = os.path.split(file)
            tb = fileName[:len(fileName)-4]
            fileRS1 = h + os.sep + tb+'_adjust1.sql'
            fileRS2 = h + os.sep + tb+'_adjust2.sql'
            checkDupFile = []
            writeTo = 1
            ls2 = open(fileRS2,'w')
            with open(fileRS1,"w") as ls1:
                ls1.write('use '+db+'\n')
                ls1.write('go\n')
                ls1.write('SET ANSI_NULLS ON\n')
                ls1.write('go\n')
                ls1.write('SET QUOTED_IDENTIFIER ON\n')
                ls1.write('go\n')
                ls2.write('use '+db+'\n')
                ls2.write('go\n')
                ls2.write('SET ANSI_NULLS ON\n')
                ls2.write('go\n')
                ls2.write('SET QUOTED_IDENTIFIER ON\n')
                ls2.write('go\n')
                c =0
                for ln in lns:
                    if c <6:
                        c = c+1
                        continue
                    ln = ln.decode('utf8','ignore')
                    ln = ''.join(x for x in ln if x in string.printable)
                    if 'CREATE TABLE' in ln:
                        writeTo = 1
                    elif writeTo == 1 and ln == 'GO':
                        ls1.write('GO\n')
                        writeTo = 2
                    if writeTo == 1:
                        ls1.write(ln)
                    elif writeTo == 2:
                        ls2.write(ln)
                            
        ls1.close()
        ls2.close()
        lns.close()
    def createDB(self,dbName):       
        file = self.schemaPath + dbName + os.sep + dbName+'_adjust.sql'
        file = file.replace('/ci', '/var')
        _cmd = self.cmd + file
        self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
        try:
            re = self.con.exec_run(cmd=_cmd,detach=False)
            self.logs.writeErrLog(re.output,self.server)
        except Exception as e:
            self.logs.writeLog('execution was failed: '+ _cmd,self.server)
            self.logs.writeLog(e,self.server)
    def createAssemblies(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'assemblies' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def createPartitionFuncs(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'partitionfunctions' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def createPartitionSCs(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'partitionschemes' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def createSPs(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'storedprocedures' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
                
    def createTBs(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'tables' + os.sep
        for file in sorted(glob.glob(d+'tables_adjust*.sql')):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
                
    def createFuncs(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'userdefinedfunctions' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
                
    def createUsers(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'users' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def createViews(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'views' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def createUDTs(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'userdefinedtabletypes' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def createSSB(self,dbName):
        d = self.schemaPath + dbName + os.sep + 'servicebroker' + os.sep
        for file in glob.glob(d+'*.sql'):
            file = file.replace('/ci', '/var')
            _cmd = self.cmd + file
            self.logs.writeLog(str(datetime.datetime.now()) + ' start: '+_cmd,self.server)
            try:
                re = self.con.exec_run(cmd=_cmd,detach=False)
                self.logs.writeErrLog(re.output,self.server)
            except Exception as e:
                self.logs.writeLog ('execution was failed: '+ _cmd,self.server)
                self.logs.writeLog(e,self.server)
    def initDB(self,dbName):
        file = self.schemaPath + dbName + os.sep + dbName + '.sql'
        dbpath = '/var/opt/mssql/data/' + dbName + os.sep
        self.adjustCreateDB(file, dbpath)
        tbFile = self.schemaPath + dbName + os.sep + 'tables' +os.sep + 'tables.sql'
        self.adjustCreateTB(tbFile,dbName)
        self.createDB(dbName)
        print(datetime.datetime.now())
        print('created DBs')        
        self.createUsers(dbName)
        self.createUDTs(dbName)  
        self.createPartitionFuncs(dbName)
        self.createPartitionSCs(dbName)
        self.createTBs(dbName)
        self.createAssemblies(dbName)
        self.createFuncs(dbName)
        self.createViews(dbName)
        self.createSPs(dbName)
        self.createSSB(dbName)
        print(datetime.datetime.now())
        print('created Users, tables, functions,views, sps')  
        
    def initSV(self):
        iDBs = []
        for dbName in self.dbs[self.server]:
            iDBs.append(multiprocessing.Process(target=self.initDB,args=[dbName,]))
        for i in iDBs:
            i.start()
        for i in iDBs:
            i.join()