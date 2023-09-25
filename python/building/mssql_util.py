# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 14:21:47 2022

@author: brice.nguyen
"""

import pyodbc
#import logging
import os
import glob
import time,datetime
import threading
import multiprocessing
from schemaBuild import schema_build

class mssql_util:
    def __init__(self,commitId,driver, server, database, uid,pwd,port):
        self.commitID = commitId
        self.driver = driver
        self.server = server
        self.database = database
        self.uid = uid
        self.pwd = pwd
        self.port = port
        self.info = 'DRIVER='+driver+';SERVER=localhost,'+port+';DATABASE='+database+';UID='+uid+';PWD='+ pwd+';TrustServerCertificate=YES'
        #self.cnn = pyodbc.connect(self.info, autocommit=True)
        #self.cur = self.cnn.cursor()
        #self.isRestored = 0
        logFileName = commitId+'.log'
        #self.log = logging.basicConfig(filename=logFileName, format='%(asctime)s | %(levelname)s | %(message)s', encoding='utf-8', level=logging.DEBUG)
    def connectDB(self):
        cnn = pyodbc.connect(self.info, autocommit=True)
        cur = cnn.cursor()
        return cur
    def prepareRestoreDB(self,backupFile=None,restorePath=None):
        restoreDBName = ''
        sql = ''
        sql += 'exec vnDBA_autoCS_restoreDB @restoreDBName'
        return sql
    def restoreDB(self,serverName,dbName):
        cur = self.connectDB()
        restorePath='/var/mssql/%s/' %(dbName)
        fullBKFile,difBKFile = self.findBK(serverName,dbName)
        fullBKFile = fullBKFile.replace('/ci/', '/var/')
        difBKFile = difBKFile.replace('/ci/', '/var/')
        #difBKFile = ''
        if len(fullBKFile) == 0:
            return
        sql = "SET NOCOUNT ON;exec vnDBA_autoCS_restoreDB @restoreDBName = '%s', @restorePath = '%s', @fullBKPath = '%s', @diffBKPath = '%s'" %(dbName,restorePath,fullBKFile,difBKFile)
        cur.execute(sql)
        #while self.cur.nextset():
        #    time.sleep(30)
        #sql = "SET NOCOUNT ON;exec vnDBA_autoCS_restoreDB @restoreDBName = ?, @restorePath = ?, @fullBKPath = ?, @diffBKPath = ?"
        #param = (dbName,restorePath,fullBKFile,difBKFile)
        #self.cur.execute(sql,param)
        print(sql)
        return cur
    def restoreDBcmd(self,serverName,dbName):
        cur = self.connectDB()
        restorePath='/var/mssql/%s/' %(dbName)
        fullBKFile,difBKFile = self.findBK(serverName,dbName)
        fullBKFile = fullBKFile.replace('/ci/', '/var/')
        difBKFile = difBKFile.replace('/ci/', '/var/')
        #difBKFile = ''
        if len(fullBKFile) == 0:
            return
        sql = "SET NOCOUNT ON;exec vnDBA_autoCS_restoreDB @restoreDBName = '%s', @restorePath = '%s', @fullBKPath = '%s', @diffBKPath = '%s'" %(dbName,restorePath,fullBKFile,difBKFile)
        return sql 

    def initDBs(self,cf1,con,serverName,dbNames,logs):
        schemaPath = cf1.getHostBackupDir() + serverName + os.sep + 'schema' + os.sep
        schema = schema_build(serverName, schemaPath, con, dbNames,logs)
        for dbName in dbNames:
            file = schemaPath + dbName + os.sep + dbName + '.sql'
            dbpath = '/var/opt/mssql/data/' + dbName + os.sep
            schema.adjustCreateDB(file, dbpath)
            tbFile = schemaPath + dbName + os.sep + 'tables' +os.sep + 'tables.sql'
            schema.adjustCreateTB(tbFile,dbName)
        schema.createDBs()
        print(datetime.datetime.now())
        print('created DBs')        
        schema.createUsers()
        schema.createUDTs()  
        schema.createPartitionFuncs()
        schema.createPartitionSCs()
        schema.createTBs()
        schema.createAssemblies()
        schema.createFuncs()
        schema.createViews()
        schema.createSPs()
        schema.createSSB()
        print(datetime.datetime.now())
        print('created Users, tables, functions,views, sps')  
        
    def initSVs(self,cf1,cons,dbs,logs):
        iDBs = []
        for sv in dbs:
            iDBs.append(multiprocessing.Process(target=self.initDBs,args=(cf1,cons[sv],sv,dbs[sv],logs,)))
        for i in iDBs:
            i.start()
        for i in iDBs:
            i.join()
        
    def restoreDBs(self,commitID,patterns,serverList,ports):
        msSQLs =[]
        for i in patterns:
            tmp = i.split('.')
            if tmp[0].lower() not in serverList:
                continue           
            msSQLs.append(mssql_util(commitID, self.driver, tmp[0], 'mondb', 'sa', '1234AA@PASS',str(ports[tmp[0]])))
        for msSQL in msSQLs:    
            msSQL.restoreDB(tmp[0],tmp[1])
        slept = 0
        for msSQL in msSQLs:
            while msSQL.cur.nextset():
                if slept >= 3600:
                    break
                time.sleep(30)
                slept += 30
        for msSQL in msSQLs:    
            msSQL.close()
    def findBK(self,serverName,dbName):
        bkDir = '/ci/backup/%s/'%(serverName)
        for file in os.listdir(bkDir):
            os.renames(bkDir+file, bkDir+file.lower())
        pattern = serverName + '.' + dbName
        bakfiles = glob.glob(bkDir + pattern+'*.bak')
        if len(bakfiles)==0:
            return '',''
        bakfiles = sorted(bakfiles, reverse=True)
        bakfile = bakfiles[0]
        
        diffiles = glob.glob(bkDir + pattern+'*.dif')
        if len(diffiles)==0:
            return bakfile,''
        diffiles = sorted(diffiles, reverse=True)
        diffile = diffiles[0]
        return bakfile,diffile
    def close(self,cur):
        cur.close()
        del cur