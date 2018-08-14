'''

Finds the focus metric which is inversely correlated with blurriness. 
The most in focus files will have high focus metrics. evalBlur exports a list of sorted tuples from least to most in focus.

Yujie

'''

from imutils import paths
import os, os.path
import cv2
import argparse
import operator
import pprint

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--folder", required=True, help="folder location")
parser.add_argument("-e", "--extension", required=False, help="file extension without .")
args = vars(parser.parse_args())

folder = args["folder"]
extension = ".png"
if args["extension"]:
	extension = "." + args["extension"]

#code adapted from https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/

def variance_of_laplacian(image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
	return cv2.Laplacian(image, cv2.CV_64F).var()

#images should be passed in from another .py file that imports blur.py
def evalBlur(images):
	blurDict = {}
	bestFocusMetric = 0
	#make the image grayscale and use LaPlace to evaluate focus
	for imagePath in paths.list_images(images):
		image = cv2.imread(imagePath)
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		#for focusMetric, higher is better
		focusMetric = variance_of_laplacian(gray)
		blurDict[imagePath] = focusMetric
		if focusMetric > bestFocusMetric:
			bestImage = imagePath
			bestFocusMetric = focusMetric
		#print(bestImage)
		print(imagePath)
		print(focusMetric)
	sortedBlur = sorted(blurDict.items(), key=operator.itemgetter(1))
	#this is a list of tuples from worst (lowest focus metric) to best (highest fm)
	return sortedBlur, bestImage

#Test
pprint.pprint(evalBlur(folder)[0])

