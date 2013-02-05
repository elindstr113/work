#!/usr/bin/python2

import pyodbc
import sys
import re
import netrc

def SaveFile(fileName, fileData):

    fullPath = '/media/temp/Python/' + fileName
    print("Saving " + fullPath)
    outputFile = open(fullPath,'wb')
    outputFile.write(fileData)
    outputFile.close()


def GetFileFromDatabase(fileList):

    secrets = netrc.netrc()
    MPUid, account, MPPwd = secrets.authenticators("MP")
    dbConnection = pyodbc.connect("DSN=MPProd;UID=" + MPUid + ";PWD=" + MPPwd)
    dbCursor = dbConnection.cursor()

    listOfFileIds = fileList.split(',')

    for fileId in listOfFileIds:
        dbCursor.execute("SET TEXTSIZE 2147483647 SELECT P.vcFileName, F.imgFile, F.imgFileOriginal, F.imgRevisions FROM tblFCFileProps P JOIN IGIFCNTR.FileCenter.dbo.tblFCFiles F ON P.intFileId=F.intFileId WHERE P.intFileId=" + fileId)
        dbRow = dbCursor.fetchone()

        if (dbCursor.rowcount==0):
            print("No records found.")

        else:
            fileName = dbRow.vcFileName
            imgFile = dbRow.imgFile
            imgFileOriginal = dbRow.imgFileOriginal
            imgRevisions = dbRow.imgRevisions

            fileExtension = ""
            if (fileName.find(".")):
                fileExtension = "." + fileName.split(".")[-1:][0]

            if (imgFile != None):
                SaveFile(fileId + fileExtension, imgFile)

            if (imgFileOriginal != None):
                SaveFile(fileId + "-Customer" + fileExtension, imgFileOriginal)

            if (imgRevisions != None):
                SaveFile(fileId + ".zip", imgRevisions)

    dbCursor.close()
    dbConnection.close()


if (__name__=='__main__'):

    if (len(sys.argv) == 2):
        FileId = str(int("0" + re.sub("\D","",sys.argv[1])))
        fileList = sys.argv[1]
        if (FileId != "0"):
            GetFileFromDatabase(fileList)

    else:
        print ("Usage:  getfile.py nnnnn (where nnnnnn = file id)")
