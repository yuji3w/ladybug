# -*- coding: utf-8 -*-
"""
Created on Sun Aug  5 18:27:35 2018

@author: awayne1

Picolay requires that all images in a stack be in a subfolder. this takes a list of folders,
like all the Z heights for a rotation, and moves them individual folders for each X/Y position.
For instance, if we have 4 Z heights (folders) each containing 20 scan locations, we would end up with 
20 folders with four files each. 



"""
#tkinter for file path asking
import tkinter as tk
from tkinter import filedialog
import os

require_input = True #otherwise everything hardcoded
 

hard_input_dir = "G:\Aharon\SCANS\picolay batch test wasp" # all folders should just be in one place. Because that's how we already have it
hard_output_dir = "" #let's say all in one folder for now. #pics/Zheights
hard_type = '.jpg'
hard_Z = 4 #number of Z heights there are

root = tk.Tk()
root.withdraw()

if require_input:
    print ("Please select the directory containing input folders")
    input_dir = filedialog.askdirectory()
    filetype = input('Please type in filetype. For instance .jpg ')
    Z_heights = int(input('how many kinds of Zs are there? for instance 3'))
else:
    input_dir = hard_input_dir
    filetype = hard_type
    Z_heights = hard_Z

#beautiful list comprehension for files from https://stackoverflow.com/questions/28682226/list-comprehension-with-if-conditional-to-get-list-of-files-of-a-specific-type
files = [os.path.join(d,f) for d,_,fl in os.walk(input_dir) for f in fl if f.endswith(filetype)]

num_files = len(files)

#find number of rotations

loc_of_of = files[0].find('of') #naming scheme: "X####Y####Z####R###of###.extension"

if loc_of_of != -1 and require_input == False: #we should be using our naming scheme:
    num_rotations = files[0][loc_of_of+2:loc_of_of+5]
    
    if num_rotations.isdigit(): 
        num_rotations = int(num_rotations)
    else:
        num_rotations = int(input('I dont get the naming scheme. Please enter how many rotations there are'))
else:
    num_rotations = int(input('I dont get the naming scheme. Please enter how many rotations there are'))
        

#find number of Z heights


stackable_files = num_files / Z_heights #number of output folders there should be

if not stackable_files.is_integer():
    print(stackable_files)
    stackable_files = int(input('Files/rotations is not a whole number. Please check that you have no extraneous or missing files. Looking for type {}. You can try typing in the number of unique stackable files'.format(filetype)))
else:
    stackable_files = int(stackable_files)
    
for R in range(num_rotations):
    RStr = str(R+1).zfill(3)
    templist = []
    for file in files:
        if RStr in file:
            templist.append(file)
            