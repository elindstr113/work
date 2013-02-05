#!/usr/bin/python2

import pyodbc
import os
import time
import netrc

stopper = 1;

secrets = netrc.netrc()
username, account, password = secrets.authenticators("MP")

serverType = "Prod"  #or Dev or Prod
mpConnectionString = "DSN=MP" + serverType + ";UID=" + username + ";PWD=" + password


def GetYearFileWasUploaded(fileId):

    dbConnection = pyodbc.connect(mpConnectionString)
    dbCursor = dbConnection.cursor()

    selectCommand = "SET TEXTSIZE 2147483647 SELECT YEAR(dteUploaded) as TheYear FROM tblFCFileProps WHERE intFileId = " + fileId

    dbCursor.execute(selectCommand)
    dbRow = dbCursor.fetchone()

    if (dbCursor.rowcount==0):
        year = '0'
    else:
        year = str(dbRow.TheYear)

    dbCursor.close()
    dbConnection.close()
    return year

stopper = 1

listOfFilesToProcess = os.listdir('/media/fca/bin')

print(str(len(listOfFilesToProcess)) + " files to process")
time.sleep(3)

for fileName in listOfFilesToProcess:
    fileId = fileName[:6]
    year = GetYearFileWasUploaded(fileId)

    if (year != '0'):
        print (year + "  " + fileName)
        os.rename('/media/fca/bin/' + fileName, '/media/fca/' + year + '/' + fileName)

    stopper += 1
    if (stopper > 10000):
        exit(2)