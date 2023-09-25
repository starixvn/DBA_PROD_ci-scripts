# -*- coding: utf-8 -*-
"""
Created on Sun Aug  1 23:45:56 2021

@author: brice.nguyen
"""
import zipfile
import os
import platform
import shutil
import sys

class extract:
    def __init__(self,zfolder,xfolder):
        try:
            rs = 1
            rs = self.cleanFolder(xfolder)  
            if rs == 0:
                return 0
            rs = self.extractPackage(zfolder,xfolder)
        except Exception as e:
            print(e)
            return 0     
    def creation_date(self,path_to_file):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        """
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime
    
    def cleanFolder(self,folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                return 0
            
    def extractPackage(self,zfolder,xfolder):
        try:
            flist = os.listdir(zfolder)
            flist =  [x for x in flist if x.endswith('.zip')]
            zfile = max(flist,key = lambda x:self.creation_date(os.path.join(zfolder,x)))
            zip = zipfile.ZipFile(os.path.join(zfolder,zfile))
            flist = zip.namelist()
            for f in flist:
                filename = os.path.basename(f)
                if filename.endswith('.sql') or filename.endswith('.config'):
                    if filename.endswith('.sql'):
                        #filename = filename.split('-')[-1].lower()
                        filename = filename.lower()
                    source = zip.open(f)
                    target = open(os.path.join(xfolder,filename.lower()),'wb+')

                    with source, target:
                        shutil.copyfileobj(source, target)
                    source.close()
                    target.close()
                    os.chmod(os.path.join(xfolder,filename), 0o777)
        except Exception as e:
            print(e)
            return 0
        return 1



# if __name__ == "__main__":
#     try:
#         rs = 1
#         zfolder = '\\\\VNRD-RDP-9899\\autoCS\\'
#         xfolder = 'G:\\autoCS\\package\\'
#         rs = cleanFolder(xfolder)  
#         if rs == 0:
#             print(0)
#             sys.exit(1)
#         rs = extractPackage(zfolder,xfolder)
#         print(1)
        
#     except:
#         print(0)
