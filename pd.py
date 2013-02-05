#!/usr/bin/python2
from pyPdf import PdfFileWriter, PdfFileReader

outputPDF = PdfFileWriter()
inputPDF = PdfFileReader(file("/media/temp/frt/257395.pdf","rb"))

for pageIndex in range(1,inputPDF.getNumPages(),2):
	outputPDF.addPage(inputPDF.getPage(pageIndex))

outputStream = file("/media/temp/frt/oddpages.pdf","wb")
outputPDF.write(outputStream)
outputStream.close()

