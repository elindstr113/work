#!/usr/bin/python2

#########################################################################
# Author:      Eric Lindstrom
# Created:     January, 2013
# Description: Utility tool for looking up information about files from
#              the File Library. Allows for the download and replacement
#              of the files.  Also lists the files used in a TOMS order.
#########################################################################

import pyodbc
import sys
import os
import getopt
import netrc
import operator
import glob

flagDownload = False
flagCustomer = False
flagRevision = False
flagToms = False
flagReplace = False
flagShowHistory = False
flagAutoUpdate = False
flagFailFile = False
flagProof = False
fileId = ""
orderId = ""
fileToUpload = ""

secrets = netrc.netrc()
MPUid, account, MPPwd = secrets.authenticators("MP")
PEMUid, account, PEMPwd = secrets.authenticators("PEM")
FCUid, account, FCPwd = secrets.authenticators("FC")

# Dev or Prod for serverType
serverType = "Prod"
mpConnectionString = ("DSN=MP" + serverType + ";UID=" + MPUid +
                      ";PWD=" + MPPwd)
pemConnectionString = ("DSN=PEM" + serverType + ";UID=" + PEMUid +
                       ";PWD=" + PEMPwd)
fcConnectionString = ("DSN=FC" + serverType + ";UID=" + FCUid +
                      ";PWD=" + FCPwd)


def SaveFile(fileName, fileData, subdirectory=""):
    if (subdirectory != ""):
        subdirectory += "/"
    directoryPath = '/media/temp/frt/' + subdirectory
    if not os.path.exists(directoryPath):
        os.makedirs(directoryPath)
    fullPath = directoryPath + fileName
    print("Saving " + fullPath)
    outputFile = open(fullPath, 'wb')
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
    global orderId
    totalFileSize = 0

    fileList = GetListOfFilesFromTomsOrder()

    if (len(fileList) == 0):
        print("No records found.")

    else:
        theList = sorted(fileList.iteritems(), key=operator.itemgetter(1))
        print("\nFiles used in TOMS order " + orderId)
        for fileInfo in theList:
            print("   %s %s" % (fileInfo[0],
                                FormatFileSize(fileInfo[1]).rjust(12)))
            totalFileSize += fileInfo[1]
        print
        print("Total File Count: %s" % str(len(fileList)))
        print("Total Size:       %s\n" % FormatFileSize(totalFileSize))
        if flagDownload:
            for file in fileList:
                fileId = file
                GetFileFromDatabase("D", orderId)


def GetFileInfo():
    global fileId
    global flagShowHistory

    dbConnection = pyodbc.connect(mpConnectionString)
    dbCursor = dbConnection.cursor()

    #Get File Properties
    selectCommand = ("SET TEXTSIZE 2147483647 SELECT "
                     "RTRIM(C.CustId) AS custId, "
                     "RTRIM(C.Name) AS customerName,"
                     "P.vcFileDesc AS fileDescription, "
                     "P.vcFileName AS fileName, "
                     "P.tPreflightStatus AS preflightStatus, "
                     "P.intFileSize AS fileSize, P.nPages AS pageCount, "
                     "P.txtFileHistory AS History, P.bHasTransparency "
                     "FROM tblFCFileProps P "
                     "JOIN GPH_DBS1.SOL4_IGIAPP.dbo.Customer C "
                     "ON P.vcOwnerCustId=C.CustId WHERE intFileId = " + fileId)
    dbCursor.execute(selectCommand)
    dbFilePropsRow = dbCursor.fetchone()

    #Get Private For List
    selectCommand = ("SET TEXTSIZE 2147483647 SELECT "
                     "U.txtFirstName + ' ' + U.txtLastName AS Name "
                     "FROM tblUser U JOIN tblFCPrivate P "
                     "ON U.txtUserId=P.txtUserId "
                     "WHERE P.intFileId = " + fileId)
    dbCursor.execute(selectCommand)
    dbPrivateForRows = dbCursor.fetchall()

    dbCursor.close()
    dbConnection.close()

    if (dbFilePropsRow is None):
        print("No records found.")
    else:
        leftColumnWidth = 18
        print
        print ("Customer:".ljust(leftColumnWidth) +
               dbFilePropsRow.customerName + " (" +
               dbFilePropsRow.custId + ")")
        print ("File Description:".ljust(leftColumnWidth) +
               dbFilePropsRow.fileDescription)
        print ("File Name:".ljust(leftColumnWidth) + dbFilePropsRow.fileName)
        print ("File Size:".ljust(leftColumnWidth) +
               FormatFileSize(dbFilePropsRow.fileSize))
        print ("Number of Pages:".ljust(leftColumnWidth) +
               str(dbFilePropsRow.pageCount))
        print ("Preflight Status:".ljust(leftColumnWidth) +
               dbFilePropsRow.preflightStatus)
        print ("Has Transparency:".ljust(leftColumnWidth) +
               str(dbFilePropsRow.bHasTransparency == 1))
        if (flagShowHistory):
            historyLines = dbFilePropsRow.History.split(chr(13))
            eventDateTime, eventDesc = historyLines[0].split(chr(9))
            print ("%s%s%s" % ("History:".ljust(leftColumnWidth),
                               eventDateTime.ljust(23), eventDesc))
            for lineIndex in range(1, len(historyLines)):
                if (historyLines[lineIndex] != ""):
                    eventDateTime, eventDesc = (
                        historyLines[lineIndex].split(chr(9)))
                    print(" " * leftColumnWidth +
                          eventDateTime.ljust(23) + eventDesc)
        if (len(dbPrivateForRows) > 0):
            print("Private For:".ljust(leftColumnWidth) +
                  dbPrivateForRows[0].Name)
            for rowIndex in range(1, len(dbPrivateForRows)):
                Name = dbPrivateForRows[rowIndex].Name
                print(" " * leftColumnWidth + Name)
        print


def GetFileFromDatabase(downloadType, orderId=""):
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

    selectCommand = ("SET TEXTSIZE 2147483647 SELECT P.vcFileName, " +
                     fieldName + " AS theFile FROM tblFCFileProps P "
                     "JOIN IGIFCNTR.FileCenter.dbo.tblFCFiles F "
                     "ON P.intFileId=F.intFileId WHERE P.intFileId=" + fileId)

    if fieldName != "":
        dbCursor.execute(selectCommand)
        dbRow = dbCursor.fetchone()

        if (dbCursor.rowcount == 0):
            print("No records found.")

        else:
            fileName = dbRow.vcFileName
            imgFile = dbRow.theFile

            fileExtension = ""
            if (fileName.find(".")):
                fileExtension = "." + fileName.split(".")[-1:][0]
            if downloadType != "R":
                outputFileName += fileExtension

            SaveFile(outputFileName, imgFile, orderId)

        dbCursor.close()
        dbConnection.close()


def ReplaceFile():
    global fileToUpload
    global fileId
    print("File: " + fileToUpload)
    if fileId != "":
        if os.path.exists(fileToUpload):
            fileData = pyodbc.Binary(open(fileToUpload, 'rb').read())
            dbConnection = pyodbc.connect(fcConnectionString)
            dbConnection.execute("exec usp_FLCUpdateFile @intFileId=?, "
                                 "@file=?", fileId, fileData)
            dbConnection.commit()
            dbConnection.close()
            dbConnection = pyodbc.connect(mpConnectionString)
            dbConnection.execute("UPDATE tblFCFileProps SET intFileSize = " +
                                 str(len(fileData)) +
                                 " WHERE intFileId=" + fileId)
            dbConnection.commit()
            dbConnection.close
            print("File uploaded.")
        else:
            print("File does not exist")


def FailFile():
    global fileId
    if fileId != "":
        dbConnection = pyodbc.connect(mpConnectionString)
        dbConnection.execute("UPDATE tblFCFileProps SET "
                             "tPreflightStatus='F' WHERE intFileId=" + fileId)
        dbConnection.commit()
        dbConnection.close()
        print("File flagged as 'Failed Preflight'.")
        print
    else:
        print("File does not exist")


def AutoUpdateFiles():
    global fileId
    global fileToUpload
    redistillDirectory = "/media/temp/frt/autoupdate"
    os.chdir(redistillDirectory)
    for files in glob.glob("*.pdf"):
        fileId = files[:-4]
        fileToUpload = redistillDirectory + "/" + files
        ReplaceFile()
        os.remove(fileToUpload)


def GetProofKeys():
    sql = ("SELECT ProofData.value('(//ProofKey/text())[1]', 'varchar(20)') "
           "AS ProofKey FROM tblProofRequests WHERE OrderId=" + orderId +
           "ORDER BY ProofId")
    proofKeys = []
    dbConnection = pyodbc.connect(pemConnectionString)
    dbCursor = dbConnection.cursor()
    dbCursor.execute(sql)
    dbRows = dbCursor.fetchall()
    for row in dbRows:
        proofKeys.append(row.ProofKey)
    dbCursor.close()
    dbConnection.close()
    return proofKeys


def GetProofFileName(proofKey, proofFileId):
    sql = ("SELECT S.Description FROM tblProducts P JOIN tblProductSpecs S "
           "ON P.ProductSpecId=S.ProductSpecId AND P.OrderId=" + orderId +
           " WHERE P.ProductId IN ( "
           "SELECT fld.value('(ProductId/text())[1]','int') FROM "
           "tblProofRequests CROSS APPLY "
           "ProofData.nodes('//ProofRequest[ProofKey=\"" + proofKey +
           "\"]/ProofProducts/ProofProduct[ProofFileId=\"" + str(proofFileId) +
           "\"]') AS tbl(fld) WHERE OrderId=" + orderId + ")")
    dbConnection = pyodbc.connect(pemConnectionString)
    dbCursor = dbConnection.cursor()
    dbCursor.execute(sql)
    dbRows = dbCursor.fetchone()
    dbCursor.close()
    return dbRows.Description


def GetProofFiles(proofKey):
    dbConnection = pyodbc.connect(pemConnectionString)
    dbCursor = dbConnection.cursor()
    dbCursor.execute("EXEC usp_OBGetProofIdAndSizeByProofKey "
                     "@ProofKey=?", proofKey)
    dbRows = dbCursor.fetchall()
    dbRows.sort(key=lambda x: x.FileSize)
    for row in dbRows:
        print(("    %d - %s %s") % (row.ProofFileId,
                                    FormatFileSize(row.FileSize).rjust(9),
                                    GetProofFileName(proofKey,
                                                     row.ProofFileId)))
    dbCursor.close()
    dbConnection.close()


def ShowProofRequests():
    proofKeys = GetProofKeys()
    for proofKey in proofKeys:
        print("\nProof Key: " + proofKey)
        GetProofFiles(proofKey)
    print


def ProcessRequest():
    global fileId
    global orderId
    global flagAutoUpdate
    global flagFailFile
    global flagProof

    if flagProof and orderId != "":
        ShowProofRequests()
    else:
        for fileIdInList in fileId.split(","):

            fileId = fileIdInList
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
                if flagFailFile:
                    FailFile()
            elif orderId != "":
                ListTomsFiles()
            elif flagAutoUpdate:
                AutoUpdateFiles()
            else:
                usage()
                sys.exit(2)


def usage():
    rightPadding = 10
    leftIndent = " " * 3
    print("Usage:  frt.py [OPTION] [FileId or TOMS Order Id")
    print(leftIndent + "-f nnnnn".ljust(rightPadding) +
          "Look up file information")
    print(leftIndent + "-H".ljust(rightPadding) +
          "Display file history indicated by the -f flag")
    print(leftIndent + "-d".ljust(rightPadding) +
          "Download the original file indicated by the -f flag")
    print(leftIndent + "-c".ljust(rightPadding) +
          "Download the customer file indicated by the -f flag")
    print(leftIndent + "-r".ljust(rightPadding) +
          "Download the revision file indicated by the -f flag")
    print(leftIndent + "-t nnnnn".ljust(rightPadding) +
          "List all the files used in a TOMS order")
    print(" " * 13 + "(can be combinded with the -d flag)")
    print(leftIndent + "-p nnnnn".ljust(rightPadding) +
          "List all of the files on a TOMS proof")
    print(leftIndent + "-R /path".ljust(rightPadding) +
          "Replace single file indicated by the -f flag")
    print(leftIndent + "-A".ljust(rightPadding) +
          "Auto update files from /media/tmp/frt/autoupdate")
    print(leftIndent + "-F".ljust(rightPadding) +
          "Fail the file indicated by the -f flag")


def main(argv):

    global flagDownload
    global flagCustomer
    global flagRevision
    global flagToms
    global flagReplace
    global flagShowHistory
    global fileToUpload
    global flagAutoUpdate
    global flagFailFile
    global flagProof
    global fileId
    global orderId

    try:
        opts, args = getopt.getopt(argv, "hdcrHf:t:R:AFp:", ["help",
                                                             "download",
                                                             "customer",
                                                             "revision",
                                                             "history",
                                                             "file",
                                                             "toms",
                                                             "replace",
                                                             "auto",
                                                             "fail",
                                                             "proof"])
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
        elif opt in ("-H", "--history"):
            flagShowHistory = True
        elif opt in ("-f", "--file"):
            fileId = arg
        elif opt in ("-t", "--toms"):
            flagToms = True
            orderId = arg
        elif opt in ("-A", "--auto"):
            flagAutoUpdate = True
        elif opt in ("-F", "--fail"):
            flagFailFile = True
        elif opt in ("-R", "--replace"):
            flagReplace = True
            fileToUpload = arg
        elif opt in ("-p", "--proof"):
            flagProof = True
            orderId = arg

    ProcessRequest()

if (__name__ == '__main__'):
    main(sys.argv[1:])
