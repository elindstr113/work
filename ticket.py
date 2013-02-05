#!/usr/bin/python2
import os

basePath = "/media/temp/Python/"

for line in file("/media/temp/sitelist.txt","r"):
	siteName = line.split(chr(9))[:1][0]
	newDir = basePath + siteName
	if not os.path.exists(newDir):
		os.makedirs(newDir)

