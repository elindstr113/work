#!/usr/bin/python2

import pyodbc
import sys
import os
import getopt
import re
import netrc

flagDownload = False
flagCustomer = False
flagRevision = False
flagToms = False
flagReplace = False
fileId = ""
orderId = ""
fileToUpload = ""

secrets = netrc.netrc()
MPUid, account, MPPwd = secrets.authenticators("MP")
PEMUid, account, PEMPwd = secrets.authenticators("PEM")
FCUid, account, FCPwd = secrets.authenticators("FC")

serverType = "Prod"  #or Dev or Prod
mpConnectionString = "DSN=MP" + serverType + ";UID=" + MPUid + ";PWD=" + MPPwd
pemConnectionString = "DSN=PEM" + serverType + ";UID=" + PEMUid + ";PWD=" + PEMPwd
fcConnectionString = "DSN=FC" + serverType + ";UID=" + FCUid + ";PWD=" + FCPwd

def SaveFile(fileName, fileData):

    fullPath = '/media/temp/frt/' + fileName
    print("Saving " + fullPath)
    outputFile = open(fullPath,'wb')
    outputFile.write(fileData)
    outputFile.close()

def FormatFileSize(fileSize):
    if fileSize > 1048576:
        return "%0.2f" % (fileSize / float(1048576)) + " MB"
    elif fileSize > 1024:
        return "%0.2f" % (fileSize / float(1024)) + " kb"
    else:
        return str(fileSize) + " bytes"

def GetListOfFilesFromTomsOrder():
    global orderId
    fileList = {}
    dbConnection = pyodbc.connect(pemConnectionString)
    dbCursor = dbConnection.cursor()
    dbCursor.execute("exec usp_OBGetFilesUsedInOrder @OrderId=?", orderId)
    dbRows = dbCursor.fetchall()
    for row in dbRows:
        fileList[str(row.intFileId)] = row.intFileSize
    dbCursor.close()
    dbConnection.close()
    return fileList


def ListTomsFiles():
    global fileId

    fileList = GetListOfFilesFromTomsOrder()

    if (len(fileList)==0):
        print("No records found.")

    else:
        print("\nFiles used in TOMS order " + orderId)
        for key, value in fileList.items():
            print("  " + key + " " + FormatFileSize(value).rjust(12))
        print
        print("Total File Count: " + str(len(fileList)) + "\n")
        if flagDownload:
            for file in fileList:
                fileId = file
                GetFileFromDatabase("D")

def GetFileInfo():
    global fileId

    dbConnection = pyodbc.connect(mpConnectionString)
    dbCursor = dbConnection.cursor()

    selectCommand = "SET TEXTSIZE 2147483647 SELECT RTRIM(C.CustId) AS custId, RTRIM(C.Name) AS customerName, P.vcFileDesc AS fileDescription, P.vcFileName AS fileName, P.tPreflightStatus AS preflightStatus, P.intFileSize AS fileSize, P.nPages AS pageCount FROM tblFCFileProps P JOIN GPH_DBS1.SOL4_IGIAPP.dbo.Customer C ON P.vcOwnerCustId=C.CustId WHERE intFileId = " + fileId

    dbCursor.execute(selectCommand)
    dbRow = dbCursor.fetchone()

    if (dbCursor.rowcount==0):
        print("No records found.")
    else:
        leftColumnWidth = 18
        print
        print ("Customer:".ljust(leftColumnWidth) + dbRow.customerName + " (" + dbRow.custId + ")")
        print ("File Description:".ljust(leftColumnWidth) + dbRow.fileDescription)
        print ("File Name:".ljust(leftColumnWidth) + dbRow.fileName)
        print ("File Size:".ljust(leftColumnWidth) + FormatFileSize(dbRow.fileSize))
        print ("Number of Pages:".ljust(leftColumnWidth) + str(dbRow.pageCount))
        print ("Preflight Status:".ljust(leftColumnWidth) + dbRow.preflightStatus)
        print

    dbCursor.close()
    dbConnection.close()

def GetFileFromDatabase(downloadType):
    global fileId

    dbConnection = pyodbc.connect(mpConnectionString)
    dbCursor = dbConnection.cursor()

    fieldName = ""
    outputFileName = ""

    outputFileName = fileId
    if downloadType == "D":
        fieldName = "imgFile"
    elif downloadType == "C":
        fieldName = "imgFileOriginal"
        outputFileName += "-Customer"
    elif downloadType == "R":
        fieldName = "imgRevisions"
        outputFileName += ".zip"

    selectCommand = "SET TEXTSIZE 2147483647 SELECT P.vcFileName, " + fieldName + " AS theFile FROM tblFCFileProps P JOIN IGIFCNTR.FileCenter.dbo.tblFCFiles F ON P.intFileId=F.intFileId WHERE P.intFileId=" + fileId

    if fieldName != "":
        dbCursor.execute(selectCommand)
        dbRow = dbCursor.fetchone()

        if (dbCursor.rowcount==0):
            print("No records found.")

        else:
            fileName = dbRow.vcFileName
            imgFile = dbRow.theFile

            fileExtension = ""
            if (fileName.find(".")):
                fileExtension = "." + fileName.split(".")[-1:][0]
            if downloadType != "R":
                outputFileName += fileExtension

            SaveFile(outputFileName, imgFile)

        dbCursor.close()
        dbConnection.close()

def ReplaceFile():
    global fileToUpload
    global fileId
    print("File: " + fileToUpload)
    if fileId != "":
        if os.path.exists(fileToUpload):
            fileData = pyodbc.Binary(open(fileToUpload,'rb').read())
            dbConnection = pyodbc.connect(fcConnectionString)
            dbConnection.execute("exec usp_FLCUpdateFile @intFileId=?, @file=?",fileId, fileData)
            dbConnection.commit()
            dbConnection.close()
            print("File uploaded.")
        else:
            print("File does not exist")


def ProcessRequest():
    global fileId
    global orderId

    if fileId != "":
        GetFileInfo()
        if flagDownload:
            GetFileFromDatabase("D")
        if flagCustomer:
            GetFileFromDatabase("C")
        if flagRevision:
            GetFileFromDatabase("R")
        if flagReplace:
            ReplaceFile()
    elif orderId != "":
        ListTomsFiles()
    else:
        usage()
        sys.exit(2)

def usage():
    rightPadding = 10
    leftIndent = " " * 3
    print("Usage:  frt.py [OPTION] [FileId or TOMS Order Id")
    print(leftIndent + "-f nnnnn".ljust(rightPadding) + "Look up file information")
    print(leftIndent + "-d".ljust(rightPadding) + "Download the original file indicated by the -f flag")
    print(leftIndent + "-c".ljust(rightPadding) + "Download the customer file indicated by the -f flag")
    print(leftIndent + "-r".ljust(rightPadding) + "Download the revision file indicated by the -f flag")
    print(leftIndent + "-t nnnnn".ljust(rightPadding) + "List all the files used in a TOMS order (can be")
    print(" "*12 + " combinded with the -d flag")
    print(leftIndent + "-R /path".ljust(rightPadding) + "Replace file indicated by the -f flag")


def main(argv):

    global flagDownload
    global flagCustomer
    global flagRevision
    global flagToms
    global flagReplace
    global fileToUpload
    global fileId
    global orderId

    try:
        opts, args = getopt.getopt(argv, "hdcrf:t:R:", ["help", "download", "customer", "revision", "file", "toms", "replace"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:

        if opt in ("-h", "--help"):
            usage()
            exit(2)
        elif opt in ("-d", "--download"):
            flagDownload = True
        elif opt in ("-c", "--customer"):
            flagCustomer = True
        elif opt in ("-r", "--revision"):
            flagRevision = True
        elif opt in ("-f", "--file"):
            fileId = arg
        elif opt in ("-t", "--toms"):
            flagToms = True
            orderId = arg
        elif opt in ("-R", "--replace"):
            flagReplace = True
            fileToUpload = arg

    ProcessRequest()

if (__name__=='__main__'):
    main(sys.argv[1:])
