#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import pyodbc
import re
import gtk
import netrc

class Application:

    def hello(self, widget, data=None):
        self.customerNameLabel.set_text("HELLO there and how are you today")
        print("Hello")

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def __init__(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_border_width(5)
        self.window.set_title("File Replacement Tool")

        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy", self.destroy)

        verticalBox = gtk.VBox(False, 0)

        #inputBox = gtk.HBox(homogeneous, spacing, expand, fill, padding)
        horizontalBox = gtk.HBox(True, 0)

        fileIdLabel = gtk.Label("File Id")
        fileIdLabel.set_alignment(0, 2)
        horizontalBox.pack_start(fileIdLabel, True, True, 0)
        fileIdLabel.show()

        label = gtk.Label("Texxt Box")
        label.set_alignment(0, 0)
        horizontalBox.pack_start(label, True, True, 0)
        label.show()

        getFileButton = gtk.Button("Get File")
        getFileButton.connect("clicked", self.hello, None)
        horizontalBox.pack_start(getFileButton, True, False, 0)
        getFileButton.show()

        verticalBox.pack_start(horizontalBox)
        horizontalBox.show()

        horizontalBox = gtk.HBox(True,0)
        label = gtk.Label("Customer")
        label.set_alignment(0, 0)
        horizontalBox.pack_start(label,True, True, 0)
        label.show()
        self.customerNameLabel = gtk.Label("")
        self.customerNameLabel.set_alignment(0, 0)
        horizontalBox.pack_start(self.customerNameLabel,True, True, 0)
        self.customerNameLabel.show()

        verticalBox.pack_start(horizontalBox)
        horizontalBox.show()

        self.window.add(verticalBox)
        verticalBox.show()
        self.window.show()



##        row = 0
##
##        #Get File Number
##        fileIdLabel = Label(text="File Id")
##        fileIdLabel.grid(row=row, column=0, padx=5, sticky=W)
##        self.FileId = Entry(width=10)
##        self.FileId.grid(row=row, column=1, padx=5, sticky=W)
##        self.SearchButton = Button(text="Get Props", command=self.GetFileProperties)
##        #self.SearchButton.bind("<Button-1>",self.GetFileProperties)
##        self.SearchButton.bind("<Return>", self.GetFileProperties)
##        self.SearchButton.grid(row=row, column=2)
##
##        row += 1
##
##        #Customer
##        self.label = Label(text="Customer").grid(row=row, column=0, sticky=W, padx=5)
##        self.Customer = Label(text="")
##        self.Customer.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
##        row += 1
##
##        #File Description
##        self.label = Label(text="File Description").grid(row=row, column=0, sticky=W, padx=5)
##        self.FileDescription = Label(text="")
##        self.FileDescription.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
##        row += 1
##
##        #File Name
##        self.label = Label(text="File Name").grid(row=row, column=0, sticky=W, padx=5)
##        self.FileName = Label(text="")
##        self.FileName.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
##        row += 1
##
##        #FileSize
##        self.label = Label(text="File Size").grid(row=row, column=0, sticky=W, padx=5)
##        self.FileSize = Label(text="")
##        self.FileSize.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
##        row += 1
##
##        #Number of Pages
##        self.label = Label(text="Number of Pages").grid(row=row, column=0, sticky=W, padx=5)
##        self.PageCount = Label(text="")
##        self.PageCount.grid(row=row, column=1, columnspan=2, sticky=W, padx=5)
##        row += 1
##
##        self.FileId.focus_set()

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

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

if (__name__=='__main__'):
    app = Application()
    app.main()
