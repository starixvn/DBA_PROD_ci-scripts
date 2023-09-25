# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 22:25:13 2022

@author: brice.nguyen
"""

import paramiko
import glob
import os
########################################################################
class SSHConnection(object):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, host, username, password, port=22):
        """Initialize and setup connection"""
        self.sftp = None
        self.sftp_open = False
        
        # open SSH Transport stream
        self.transport = paramiko.Transport((host, port))
        
        self.transport.connect(username=username, password=password)
        
    #----------------------------------------------------------------------
    def _openSFTPConnection(self):
        """
        Opens an SFTP connection if not already open
        """
        if not self.sftp_open:
            self.sftp = paramiko.SFTPClient.from_transport(self.transport,window_size=22770)
            self.sftp_open = True
    
    #----------------------------------------------------------------------
    def get(self, remote_path, local_path=None):
        """
        Copies a file from the remote host to the local host.
        """
        self._openSFTPConnection()        
        self.sftp.get(remote_path, local_path)        
            
    #----------------------------------------------------------------------
    def put(self, local_path, remote_path=None):
        """
        Copies a file from the local host to the remote host
        """
        self._openSFTPConnection()
        self.sftp.put(local_path, remote_path)
        
    #----------------------------------------------------------------------
    def putBK(self,pattern,local_dir, remote_dir):
        bakfiles = glob.glob(local_dir + pattern+'*.bak')
        bakfiles = sorted(bakfiles, reverse=True)
        bakfile = bakfiles[0]
        h, bakfileName = os.path.split(bakfile)
        print (bakfile,remote_dir+bakfileName)
        if self.checkExists(remote_dir+bakfileName):
            return
        try:
            self.put(bakfile,remote_dir+bakfileName)
        except:
            bakfile =bakfiles[1]
            self.put(bakfile,remote_dir+bakfileName)
            return
        diffiles = glob.glob(local_dir + pattern+'*.dif')
        if len(diffiles)==0:
            return
        diffiles = sorted(diffiles, reverse=True)
        diffile = diffiles[0]
        h, diffilename = os.path.split(diffile)
        if os.path.getctime(diffile) > os.path.getctime(bakfile):
            print (diffile,remote_dir+diffilename)
            try:
                self.put(diffile,remote_dir+diffilename)
            except:
                pass
            
    #----------------------------------------------------------------------
    def putConfig(self,server,local_dir, remote_dir):
        cnf = ['LoginID','LinkedServer','AgentJob']
        for i in cnf:
            files = glob.glob(local_dir + server+'\\'+i+'\\*.sql')
            file  = sorted(files)[-1]
            h,fileName = os.path.split(file)
            self.put(file,remote_dir+fileName)
            
    #----------------------------------------------------------------------
    def checkExists(self,path):
        self._openSFTPConnection()
        try:
            self.sftp.stat(path)
            return True
        except:
            return False

    #----------------------------------------------------------------------

    def close(self):
        """
        Close SFTP connection and ssh connection
        """
        if self.sftp_open:
            self.sftp.close()
            self.sftp_open = False
        self.transport.close()
