#!/usr/bin/python
# -*- coding: utf-8 -*-

'''

Finds the focus metric which is inversely correlated with blurriness. 
The most in focus files will have high focus metrics. evalBlur exports a list of sorted tuples from least to most in focus.

Yujie then corrupted by Ahron years later

'''

from imutils import paths
import os
import re
import os.path
import cv2
import argparse
import operator
import pprint
from os import listdir
from os.path import isfile, join
from shutil import copyfile


# code adapted from https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/

def variance_of_laplacian(image):

    # compute the Laplacian of the image and then return the focus
    # measure, which is simply the variance of the Laplacian

    return cv2.Laplacian(image, cv2.CV_64F).var()


# images should be passed in from another .py file that imports blur.py

def evalBlur(folder, AcceptableBlur=200):
    blurDict = {}
    bestImages = []
    BadImages = []  # holds files to delete

    rawFolders = [x[0] for x in os.walk(folder)]
    for folder in rawFolders:
        FolderBadImages = []
        imagePaths = [os.path.join(folder, file) for file in
                      listdir(folder) if isfile(os.path.join(folder,
                      file))]

        # print(imagePaths)

        len(imagePaths)
        bestFocusMetric = 0
        bestImage = ''

        # make the image grayscale and use LaPlace to evaluate focus
        for imagePath in imagePaths:
            
            
            image = cv2.imread(imagePath)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    # for focusMetric, higher is better

            focusMetric = variance_of_laplacian(gray)
            blurDict[imagePath] = focusMetric
            
            if focusMetric > bestFocusMetric:
                bestImage = imagePath
                bestFocusMetric = focusMetric
            if focusMetric < AcceptableBlur:  # modification starts here
                FolderBadImages.append(imagePath)

            if len(FolderBadImages) == len(imagePaths) \
                and len(FolderBadImages) > 0:  # all fail metric, keep best

                FolderBadImages.remove(bestImage)  # don't delete the best crappy on

        for image in FolderBadImages:
            BadImages.append(image)

    BadImages = [valid for valid in BadImages if valid != '']

    return BadImages

def MakePositionsFromName(name):
    #inverse of Make Name From Positions (harder)
    #from file name or basename returns an (X,Y,Z,R) tuple
    basename = os.path.splitext(os.path.basename(name))[0]
    splitname = re.sub( r"([A-Z])", r" \1", basename).split()
    numbersonly = [x[1:] for x in splitname]
    positions = [float((x[0:-2] + "." + x[-2:])) for x in numbersonly]
    positions = tuple(positions)

    return positions

def sortBlur(folder, AcceptableBlur=200, FocusDictionary = {}):
    #like RemoveBlur but uses passed in dictionary of focuses
    
    blurDict = {}
    bestImages = []
    BadImages = []  # holds files to delete

    rawFolders = [x[0] for x in os.walk(folder)]
    for folder in rawFolders:
        FolderBadImages = []
        imagePaths = [os.path.join(folder, file) for file in
                      listdir(folder) if isfile(os.path.join(folder,
                      file))]

        # print(imagePaths)

        len(imagePaths)
        bestFocusMetric = 0
        bestImage = ''

        # make the image grayscale and use LaPlace to evaluate focus
        for imagePath in imagePaths:
            
            
            #image = cv2.imread(imagePath)
            #gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    # for focusMetric, higher is better
            imagekey = MakePositionsFromName(imagePath)
            
            focusMetric = FocusDictionary[imagekey]

            #focusMetric = variance_of_laplacian(gray)
            blurDict[imagePath] = focusMetric
            
            if focusMetric > bestFocusMetric:
                bestImage = imagePath
                bestFocusMetric = focusMetric
            if focusMetric < AcceptableBlur:  # modification starts here
                FolderBadImages.append(imagePath)

            if len(FolderBadImages) == len(imagePaths) \
                and len(FolderBadImages) > 0:  # all fail metric, keep best

                FolderBadImages.remove(bestImage)  # don't delete the best crappy on

        for image in FolderBadImages:
            BadImages.append(image)

    BadImages = [valid for valid in BadImages if valid != '']

    return BadImages



def main(folder, AcceptableBlur=200, extension='.jpg', FocusDictionary = {}):

    if not FocusDictionary:
        BadImages = evalBlur(folder, AcceptableBlur)
    else: #Ahron amended quickly: if locations of focuses passed in, don't recalculate
        BadImages = sortBlur(folder, AcceptableBlur, FocusDictionary=FocusDictionary)
    print('\n' * 5)

    #pprint.pprint(BadImages)
    print ('Bad images. Quantity: {}'.format(len(BadImages)))

    for image in BadImages:
        os.remove(image)  # dangerous part


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True,
                        help='input folder location')
    parser.add_argument('-e', '--extension', required=False,
                        help='file extension without .')
    parser.add_argument('-t', '--acceptable blur', required=False,
                        help='default 3, higher numbers more strict')
    args = vars(parser.parse_args())
    if not args['acceptable blur']:
        blur = 3
    else:
        blur = int(args['acceptable blur'])
    if args['extension']:
        extension = '.' + args['extension']
        main(args['input'], blur,
             extension=extension)
    else:
        main(args['input'], blur)

			
