'''

Crops images to smallest dimensions of image in folder. Will crop evenly from each side.

Yujie

'''

import cv2
import numpy as np
import os, sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="input location")
parser.add_argument("-o", "--output", required=True, help="output location")
parser.add_argument("-e", "--extension", required=False, help="file extension without .")
args = vars(parser.parse_args())

extension = ".png"
if args["extension"]:
	extension = "." + args["extension"]

importDir = args["input"]
exportDir = args["output"]

def crop(yDim, xDim):
	global img
	global crop_img
	height, width, channels = img.shape
	xLeft = int((width-xDim)/2)
	xRight = xLeft+xDim
	yDown = int((height-yDim)/2)
	yUp = yDown+yDim
	crop_img = img[yDown:yUp, xLeft:xRight]
	return crop_img

def scanDim(folder):
	minH = minW = sys.maxsize
	imgList = []
	for file in os.listdir(folder):
		if file.endswith(extension):
			imgList.append(os.path.join(folder,file))
			tempImg = cv2.imread(os.path.join(folder,file))
			height, width, channels = tempImg.shape
			minH = height if height<minH else minH
			minW = width if width<minW else minW
	return imgList, minH, minW

def exportImg(folder, fileName):
	global img
	file = os.path.join(folder,fileName)
	cv2.imwrite(file,img)


imgList, minH, minW = scanDim(importDir)
for file in imgList:
	img = cv2.imread(file)
	img = crop(minH, minW)
	exportImg(exportDir, os.path.basename(file))