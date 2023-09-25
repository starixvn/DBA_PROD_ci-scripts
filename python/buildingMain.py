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
    configFile1 = ''
    configFile2 = ''
    try:
        configFile1 = sys.argv[1]   #running config
        configFile2 = sys.argv[2]   #schema config
    except:
        print('need config file to run')
        return
    cf1 = parser_config(configFile1)
    cf2 = parser_config(configFile2)

    #listServer,commitId, neededBuild,volumeDir
    serverList = cf2.getServerList()
    commitId = cf2.getCommitId()
    neededBuild = False
    volumeDir = cf1.getVolumeDir()
    driver = cf1.getDriver()
    re = ''
    logs = logCI(serverList, cf1)
    
    env = buildEnv(neededBuild,cf1,cf2,logs)
    env.startENV()
    env.buildSSB()
    
#set up replication     
    env.buildReplication()
#create images
    env.dr.commitImages()
    env.dr.pushImages()
    logs.close()
    return

if __name__ == "__main__":
    print(str(datetime.datetime.now())+': begin')
    main()
    print(str(datetime.datetime.now())+': end')
    