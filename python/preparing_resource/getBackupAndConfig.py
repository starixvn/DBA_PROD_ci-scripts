# -*- coding: utf-8 -*-

import sys
sys.path.append('/ci/python/config')
sys.path.append('/ci/python/building')
sys.path.append('/ci/python/running')
sys.path.append('/ci/python/preparing_resource')

from buildEnv import buildEnv
from configParser import parser_config
from transferFile import SSHConnection
from mssql_util import mssql_util
from log import logCI
import time
import datetime
def main():
    
    cf2 = parser_config('D:\\vnTeam\\Brice\\customerArchive.config')
    local_dir1 = 'G:\\MidTerm\\SB\\'
    local_dir2 = 'G:\\MidTerm\\SB_ReplicatedDB\\Backup\\'
    local_dir_config = 'G:\\MidTerm\\ConfigFile\\'
    remote_dir1 = '/ci/backup/'
    transfer = SSHConnection('10.2.27.125', 'vnteam', '1qaz@WSX')
    for i in cf2.getRestoringPatterns():
        tmp = i.split('.')
        if tmp[0] in ['db052','db053']:
            local_dir = local_dir2 + tmp[0] + '\\'
        elif tmp[0] in ['db061','db062']:
            local_dir = local_dir2 + 'db06' + '\\'
        else:
            local_dir = local_dir1
        remote_dir = remote_dir1 + tmp[0]+'/'
        transfer.putBK(i, local_dir, remote_dir)
    for i in cf2.getServerList():
        remote_dir = remote_dir1 + i+'/'
        transfer.putConfig(i,local_dir_config,remote_dir)