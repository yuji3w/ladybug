import cv2
import numpy as np
import os, sys

importDir = r"C:\Users\wangy\Desktop\import"
exportDir = r"C:\Users\wangy\Desktop\export"

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
		if file.endswith(".jpg"):
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






r'''img = cv2.imread(r"C:\Users\wangy\Desktop\lenna.jpg")
crop(600,600)
cv2.imshow("cropped", crop_img)
cv2.waitKey(0)
cv2.imwrite(r"C:\Users\wangy\Desktop\heyoo.jpg",crop_img)'''
imgList, minH, minW = scanDim(importDir)
for file in imgList:
	img = cv2.imread(file)
	img = crop(minH, minW)
	exportImg(exportDir, os.path.basename(file))