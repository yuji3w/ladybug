#should work with python 3 / cv2

from imutils import paths
import os, os.path
import cv2

#code adapted from https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/

def variance_of_laplacian(image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
	return cv2.Laplacian(image, cv2.CV_64F).var()

#images should be passed in from another .py file that imports blur.py
def evalBlur(images):
	bestFocusMetric = 0
	#make the image grayscale and use LaPlace to evaluate focus
	for imagePath in paths.list_images(images):
		image = cv2.imread(imagePath)
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		#for focusMetric, higher is better
		focusMetric = variance_of_laplacian(gray)
		if focusMetric > bestFocusMetric:
			bestImage = imagePath
			bestFocusMetric = focusMetric
		#print(bestImage)
		print(imagePath)
		print(focusMetric)

	return bestImage

#Test
print(evalBlur(r"G:\ANACONDA\focusstack\focusstack-master\Input"))