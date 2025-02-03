import sys
sys.path.append('/ci/python/config')
sys.path.append('/ci/python/package')
sys.path.append('/ci/python/building')
sys.path.append('/ci/python/running')
sys.path.append('/ci/python/preparing_resource')
import time
import datetime
from configParser import parser_config
from execScripts_nodependency import execPackage_nodependency
from execScripts import execPackage
from buildEnv import buildEnv
from log import logCI
def main():
    configFile1 = ''
    configFile2 = ''
    try:
        configFile1 = sys.argv[1]
        configFile2 = sys.argv[2]
        zfolder = sys.argv[3]
        xfolder = sys.argv[4]
        #execType = sys.argv[5]
    except:
        print('need config file to run')
        return
    cf1 = parser_config(configFile1)
    cf2 = parser_config(configFile2)
    logs = logCI(cf2.getServerList(), cf1)
    env = buildEnv(0,cf1,cf2,logs)
    env.getEnv()
    execP = execPackage(zfolder,xfolder,cf1,cf2,logs,env)

if __name__ == "__main__":
    print(str(datetime.datetime.now())+': begin')
    main()
    print(str(datetime.datetime.now())+': end')
    