import sys
sys.path.append('/ci/python/config')
sys.path.append('/ci/python/building')
sys.path.append('/ci/python/running')
sys.path.append('/ci/python/preparing_resource')
from dockerUtil import docker_util
class Env:
    def __init__(self,cf1,cf2,logs):
        self.listServer = cf2.getServerList()
        self.commitId = cf2.getCommitId()
        self.dr = docker_util(cf1,cf2,logs)
        self.ports = {}
        self.cons = {}
        self.cf1 = cf1
        self.cf2 = cf2



    def runENV(self):
        self.dr.pullImages()
        self.dr.createMssqlContainers(self.listServer)
        