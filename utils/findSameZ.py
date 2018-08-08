"""
Takes a folders of folders and makes new folders containing "identical" images, at different Z heights, for stacking


Yujie and Ahron.



"""

import os
import argparse
import sys

if len(sys.argv) > 1:
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", required=True, help="input location")
	parser.add_argument("-o", "--output", required=True, help="output location")
	parser.add_argument("-e", "--extension", required=False, help="file extension without .")
	args = vars(parser.parse_args())


	inputFolder = args["input"]
	outputFolder = args["output"]
	extension = ".png"
	if args["extension"]:
		extension = "." + args["extension"]


else:
	inputFolder = r"G:\Aharon\SCANS\picolay batch test wasp - Copy"
	outputFolder =r"G:\Aharon\SCANS\test wasp output" 
	extension = ".jpg"


#beautiful list comprehension for files from https://stackoverflow.com/questions/28682226/list-comprehension-with-if-conditional-to-get-list-of-files-of-a-specific-type
files = [os.path.join(d,f) for d,_,fl in os.walk(inputFolder) for f in fl if f.endswith(extension)]
zFiles = []

def initZList():
	for file in files:
		fileName = list(os.path.basename(file))
		#need to get basename in list to mod chars
		fileName[11] = '0'
		fileName[12] = '0'
		fileName[13] = '0'
		fileName[14] = '0'
		#kills Z info to 0
		fileName = "".join(fileName)
		#put it back into string
		zFiles.append(fileName)

initZList()


from collections import defaultdict

def list_duplicates(seq):
    tally = defaultdict(list)
    for i,item in enumerate(seq):
        tally[item].append(i)
    return ((key,locs) for key,locs in tally.items() 
                            if len(locs)>1)


#creates a list of lists of length number_output folders. list[0] = name of wanted set of images, list[1] contains 
#list indeces of these files. Grab file names from original files list. 
    
duplicate_z = sorted(list_duplicates(zFiles)) #https://stackoverflow.com/questions/5419204/index-of-duplicates-items-in-a-python-list

#copy original files to new folders or move if input and output are the same

for set_of_duplicates in duplicate_z:
    new_folder = outputFolder + "\\" + set_of_duplicates[0].strip(extension) #fix because for some goshdang reason picolay won't accept otherwise
    os.mkdir(new_folder)
    for location in set_of_duplicates[1]: 
        old_path = files[location]
        old_name = os.path.basename(old_path)
        new_path = new_folder + "\\" + old_name
        os.rename(old_path,new_path)
        