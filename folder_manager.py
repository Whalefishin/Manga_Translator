import os
import shutil
from datetime import datetime 

class FolderManager():
    def __init__(self, args):
        self.mainTempFolder = os.path.join(args.result_root_dir, args.result_name)
        if args.overwrite and os.path.exists(self.mainTempFolder):
            shutil.rmtree(self.mainTempFolder)
        self.intitFolderEnv()
        self.downloadPath = "gallery-dl/"

    def intitFolderEnv(self):
        self.setMainTempFolder()
        self.createDir([self.oriFolder, self.textOnlyFolder, self.inpaintedFolder, \
                        self.transalatedFolder, self.OCR_folder])

        
    def setMainTempFolder(self):
        # self.mainTempFolder  = "tmp/" + datetime.now().strftime("%Y%m%d%H%M%S")+"/"
        self.oriFolder         = os.path.join(self.mainTempFolder, 'ori')
        self.textOnlyFolder    = os.path.join(self.mainTempFolder, 'text_only')
        self.inpaintedFolder   = os.path.join(self.mainTempFolder, 'inpainted')
        self.OCR_folder        = os.path.join(self.mainTempFolder, 'OCR')
        self.transalatedFolder = os.path.join(self.mainTempFolder, 'translated')

    def createDir(self, listPath):
        for filePath in listPath:
            if not os.path.exists(filePath):
                os.makedirs(filePath)

    def removeDir(self, listPath):
        for filePath in listPath:
            if os.path.exists(filePath):
                shutil.rmtree(filePath)


    def get_download_path(self,):
        """Returns the default downloads path for linux or windows"""
        if os.name == 'nt':
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            return location
        else:
            return os.path.join(os.path.expanduser('~'), 'downloads')

    def copyFilesToFolder(self, fileList, tempFolder):
        for filename in fileList:
            shutil.copy(filename, tempFolder)
            
    
    def saveFileAndRemove(self,mangaName):
        #save as zip file
        shutil.make_archive(mangaName, 'zip', self.transalatedFolder)
        
        namePadding=""
        i=0
        while os.path.exists(os.path.join(self.get_download_path(),mangaName+namePadding+".zip")):
            i+=1
            namePadding="("+str(i)+")"
            
        zipFile=mangaName+namePadding+".zip"    
        os.rename(mangaName+".zip", zipFile) 
        
        shutil.move(zipFile, self.get_download_path())
        self.removeDir([self.mainTempFolder])
        
        return os.path.join(self.get_download_path(), zipFile)
        

    def sendInfo(self,title,image,pages):
        pass

if __name__ == "__main__":
    folderManager=FolderManager()
    print( folderManager.get_download_path())