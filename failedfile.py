#!/usr/bin/python2
#Added to GitHub 2013-02-05

import pyodbc
import sys
import re
import netrc

def SaveFile(fileName, fileData):

    fullPath = '/media/Redistill/' + fileName
    print("Saving " + fullPath)
    outputFile = open(fullPath,'wb')
    outputFile.write(fileData)
    outputFile.close()


def GetFileFromDatabase(fileList):

    secrets = netrc.netrc()
    username, account, password = secrets.authenticators("MP")
    dbConnection = pyodbc.connect("DSN=MPProd;UID=" + username + ";PWD=" + password)
    dbCursor = dbConnection.cursor()

    listOfFileIds = fileList.split(',')

    for fileId in listOfFileIds:
        dbCursor.execute("SET TEXTSIZE 2147483647 SELECT imgFileOriginal FROM IGIFCNTR.FileCenter.dbo.tblFCFiles WHERE intFileId=" + fileId)
        dbRow = dbCursor.fetchone()

        if (dbCursor.rowcount==0):
            print("No records found.")

        else:
            SaveFile(fileId + "-Customer.pdf", dbRow.imgFileOriginal)

    dbCursor.close()
    dbConnection.close()


if (__name__=='__main__'):

    if (len(sys.argv) == 2):
        FileId = str(int("0" + re.sub("\D","",sys.argv[1])))
        fileList = sys.argv[1]
        if (FileId != "0"):
            GetFileFromDatabase(fileList)

    else:
        print ("Usage:  failedfile.py nnnnn (where nnnnnn = file id)")
