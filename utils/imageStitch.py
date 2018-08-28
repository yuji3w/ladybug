'''

Stitches together multiple images as long as they are in the same folder.

Yujie

'''

import cv2
import os
import argparse

def cvStitch(folder, output, extension = ".png"):
	stitcher = cv2.createStitcher(False)

	fileList = []
	imgList = []

	for file in os.listdir(folder):
			if file.endswith(extension):
				fileList.append(os.path.join(folder,file))

	for file in fileList:
		img = cv2.imread(file)
		imgList.append(img)

	imgTuple = tuple(imgList)
	stitched = stitcher.stitch(imgList)
	cv2.imwrite(os.path.join(output,os.path.basename(fileList[0])),stitched[1])

def main(folder, output, extension):
	cvStitch(folder, output, extension)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", required=True, help="folder input")
	parser.add_argument("-o", "--output", required=True, help="folder output")
	parser.add_argument("-e", "--extension", required=False, help="file extension without .")
	args = vars(parser.parse_args())

	folder = args["input"]
	output = args["output"]
	extension = ".png"
	if args["extension"]:
		extension = "." + args["extension"]
	main(folder, output, extension)