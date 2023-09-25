# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 15:13:58 2022

@author: brice.nguyen
"""
import json
class parser_config:
    def __init__(self,fileName):
        f = open(fileName)
        self.config = json.load(f)
        f.close()
    def getRestoringPatterns(self):
        arr = []
        for i in self.config['restore']:
            for j in i['dbs']:
                arr.append(i['server']+'.'+j)
        return arr
    def getCSV(self):
        return self.config['csv']
    def getInitScripts(self):
        return self.config['initscripts']
    def getServerList(self):
        return self.config['serverlist']
    def getCommitId(self):
        return self.config['commitid']

    def getDriver(self):
        return self.config['driver']
    def getInitDBs(self):
        dbs = {}
        for i in self.config['initstructure']:
            dbs.update({i['server']:[]})
            dbs[i['server']].extend(i['dbs'])
        return dbs
    def getHostBackupDir(self):
        return self.config['host_backup_dir']
    def getConBackupDir(self):
        return self.config['container_backup_dir']
    def getConEnv(self):
        return self.config['container_env']
    def getPreCmd(self):
        return self.config['pre_cmd']
    def getSsbDir(self):
        return self.config['ssb_dir']
    def getVolumeDir(self):
        return self.config['volume_dir']
    def getImage(self):
        return self.config['image_name']
    def getLogDir(self):
        return self.config['log_dir']
    def getRegistry(self):
        return self.config['registry']
    def getSchemaPath(self):
        return self.config['schemapath']
    def getConfigDir(self):
        return self.config['configpath']
    def serverAliases(self):
        return self.config['server_alias']
    def standbyDBs(self):
        return self.config['standby_db']
    def serverAlias(self,aliasName):
        aliases = self.serverAliases()
        try:
            return aliases[aliasName]
        except:
            return None
    def standbyDB(self,serverName,DBName):
        i = serverName+":"+DBName
        standbyDBs = self.standbyDBs()
        try:
            return standbyDBs[i]
        except:
            return None