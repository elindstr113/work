#!/usr/bin/python

from Tkinter import *
import pyodbc
import re
import netrc

class Application:



    def __init__(self,master):

        row = 0

        #Get File Number
        fileIdLabel = Label(text="File Id")
        fileIdLabel.grid(row=row, column=0, padx=5, sticky=W)
        self.FileId = Entry(width=10)
        self.FileId.grid(row=row, column=1, padx=5, sticky=W)
        self.SearchButton = Button(text="Get Props", command=self.GetFileProperties)
        #self.SearchButton.bind("<Button-1>",self.GetFileProperties)
        self.SearchButton.bind("<Return>", self.GetFileProperties)
        self.SearchButton.grid(row=row, column=2)

        row += 1

        #Customer
        self.label = Label(text="Customer").grid(row=row, column=0, sticky=W, padx=5)
        self.Customer = Label(text="")
        self.Customer.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
        row += 1

        #File Description
        self.label = Label(text="File Description").grid(row=row, column=0, sticky=W, padx=5)
        self.FileDescription = Label(text="")
        self.FileDescription.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
        row += 1

        #File Name
        self.label = Label(text="File Name").grid(row=row, column=0, sticky=W, padx=5)
        self.FileName = Label(text="")
        self.FileName.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
        row += 1

        #FileSize
        self.label = Label(text="File Size").grid(row=row, column=0, sticky=W, padx=5)
        self.FileSize = Label(text="")
        self.FileSize.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
        row += 1

        #Number of Pages
        self.label = Label(text="Number of Pages").grid(row=row, column=0, sticky=W, padx=5)
        self.PageCount = Label(text="")
        self.PageCount.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
        row += 1

        self.FileId.focus_set()

    def GetFileProperties(self, *args):

        fileId = str(int("0" + re.sub("\D","",self.FileId.get())))

        if (fileId):
            secrets = netrc.netrc()
            MPUid, account, MPPwd = secrets.authenticators("MP")
            dbConnection = pyodbc.connect("DSN=WEB3;UID=" + MPUid + ";PWD=" + MPPwd)
            dbCursor = dbConnection.cursor()
            dbCursor.execute("SET TEXTSIZE 2147483647 SELECT vcOwnerCustId, vcFileDesc, vcFileName, intFileSize, nPages FROM tblFCFileProps WHERE intFileId=" + fileId)
            dbRow = dbCursor.fetchone()

            if (dbCursor.rowcount==0):
                self.Customer["text"] = ""
                self.FileDescription["text"] = ""
                self.FileName["text"] = ""
                self.FileSize["text"] = ""
                self.PageCount["text"] = ""
            else:
                self.Customer["text"] = dbRow.vcOwnerCustId
                self.FileDescription["text"] = dbRow.vcFileDesc
                self.FileName["text"] = dbRow.vcFileName
                self.FileSize["text"] = dbRow.intFileSize
                self.PageCount["text"] = dbRow.nPages


        #print(self.FileId.get())
        #self.FileName["text"] = "M2012-15-10y First File"
        #self.UploadDate["text"] = "2012-15-102012-15-102012-15-10"



if (__name__=='__main__'):
    mainWindow = Tk()
    mainWindow.title("File Replacement Tool")
    app = Application(mainWindow)
    mainWindow.geometry("500x100+100+100")
    mainWindow.mainloop()

