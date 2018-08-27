'''

Crops images to smallest dimensions of image in folder. Will crop evenly from each side unless specified with side flag

Yujie

Ahron change 8/11/18: Added a couple of comments, substituted global vars for args, added crop from left,right,up,down

Also, implement SMART, using smartcrop.py. Credit to epixelic, https://github.com/epixelic/python-smart-crop
'''

import cv2
import numpy as np
import os, sys
import argparse
import subprocess
import smartcrop #note that this file currently has a dependency hard linked inside it. 



def crop(img, yDim, xDim, side): #crops image evenly on all sides to specified dimensions, or from specific side (evenly on other axis)

	height, width, channels = img.shape
	xLeft = int((width-xDim)/2)
	xRight = xLeft+xDim
	yDown = int((height-yDim)/2)
	yUp = yDown+yDim

	if side == "all":
		crop_img = img[yDown:yUp, xLeft:xRight]
	elif side == "bottom": #crops from bottom and does sides evenly
		crop_img = img[height-yDim:height,xLeft:xRight]
	elif side == "top":
		crop_img = img[0:height-(height-yDim),xLeft:xRight]
	elif side == "left":
		crop_img = img[yDown:yUp, width-xDim:width]
	elif side == "right":
		crop_img = img[yDown:yUp, 0:width-(width-xDim)] 
	
	return crop_img


def scanDim(folder, extension):
	minH = minW = sys.maxsize #purpose? 
	imgList = []
	for file in os.listdir(folder):
		if file.endswith(extension):
			imgList.append(os.path.join(folder,file))
			tempImg = cv2.imread(os.path.join(folder,file)) # inefficient to actually read the image each time. We just care about resolution. Alternative?
			height, width, channels = tempImg.shape
			minH = height if height<minH else minH #the file's height becomes minh if smaller than current height. else necessary?
			minW = width if width<minW else minW
	return imgList, minH, minW

def exportImg(img, folder, fileName):
	#this also helps if the PNG file is corrupted since it essentially makes a new one
	file = os.path.join(folder,fileName)
	cv2.imwrite(file,img)



def main(importDir, exportDir, extension = ".png", side = "all"):
	rawFolders = [x[0] for x in os.walk(importDir)]

	for currentDir in rawFolders:
		imgList, minH, minW = scanDim(currentDir, extension)
		
		newfolder = os.path.join(exportDir,os.path.basename(currentDir)) 
		os.mkdir(newfolder)
		for file in imgList:

			img = cv2.imread(file)
			if side != "smart":
				img = crop(img, minH, minW, side)
				#print(currentDir)
				#print(os.path.basename(currentDir))
				
				exportImg(img, newfolder, os.path.basename(file))

			else: #do smart crop
				smartcrop.smart_crop(file,minW,minH, os.path.join(exportDir, os.path.basename(file)), False) #true resizes original image


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", required=True, help="input location")
	parser.add_argument("-o", "--output", required=True, help="output location")
	parser.add_argument("-e", "--extension", required=False, help="file extension without .")
	parser.add_argument("-s", "--side", required=False, help="side to preferentially crop from. left, right, top, bottom, smart (attempts to find center of image and crop from that), all. defaults to all")
	args = vars(parser.parse_args())

	side = "all"
	if args["side"]: #side to crop from
		side = str(args["side"])
	extension = ".png"
	if args["extension"]:
		extension = "." + args["extension"]

	main(args["input"], args["output"], extension, side)
		