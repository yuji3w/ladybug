"""
Takes a folders of folders and makes new folders containing "identical" images, at different Z heights, for stacking


Yujie and Ahron.



"""

import os
import argparse
import sys
from shutil import copyfile
from collections import defaultdict


# beautiful list comprehension for files from https://stackoverflow.com/questions/28682226/list-comprehension-with-if-conditional-to-get-list-of-files-of-a-specific-type
def initZList(files, zFiles):
    for file in files:
        fileName = list(os.path.basename(file))
        # need to get basename in list to mod chars
        fileName[13] = '0'  # shifted from 11
        fileName[14] = '0'
        fileName[15] = '0'
        fileName[16] = '0'
        fileName[17] = '0'  # added with jan 2020 filename change
        # kills Z info to 0
        fileName = "".join(fileName)
        # put it back into string
        zFiles.append(fileName)
        # Make this return zFiles


def list_duplicates(seq):
    tally = defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items()
            if len(locs) > 1)


def main(inputFolder, outputFolder, extension, copy, minimumfilesize=False):
    files = [os.path.join(d, f) for d, _, fl in os.walk(inputFolder)
             for f in fl if f.endswith(extension)]
    zFiles = []
    initZList(files, zFiles)

    # creates a list of lists of length number_output folders. list[0] = name of wanted set of images, list[1] contains
    # list indeces of these files. Grab file names from original files list.

    # https://stackoverflow.com/questions/5419204/index-of-duplicates-items-in-a-python-list
    duplicate_z = sorted(list_duplicates(zFiles))

    # copy original files to new folders or move if input and output are the same

    for set_of_duplicates in duplicate_z:
        # fix because for some goshdang reason picolay won't accept otherwise

        if minimumfilesize: #easy way get rid of bad files like blank
            
            old_path = files[set_of_duplicates[1][0]]
            size = os.path.getsize(old_path)
            if size < (int(minimumfilesize)*1000): #bytes to kb ish 
                #print('Image data less than {} kb'.format(minimumfilesize))
                continue
        

        new_folder = outputFolder + "\\" + \
            set_of_duplicates[0].strip(extension)
        os.mkdir(new_folder)

        for location in set_of_duplicates[1]:
            old_path = files[location] 
            old_name = os.path.basename(old_path)
            new_path = new_folder + "\\" + old_name

            if copy:
                copyfile(old_path, new_path)
            if not copy:
                os.link(old_path, new_path)

                


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="input location")
    parser.add_argument("-o", "--output", required=True,
                        help="output location")
    parser.add_argument("-e", "--extension", required=False,
                        help="file extension without .")
    parser.add_argument("-c", "--copy", required=False,
                        help="If not enabled hard symbolic links not copy")
    parser.add_argument("-m", "--minimumfilesize",required=False,
                        help="blank/useless files below this size kb not moved")
    args = vars(parser.parse_args())
    
    inputFolder = args["input"]
    outputFolder = args["output"]
    extension = ".jpg"
    copy = False
    minimumfilesize = False
    
    if args["copy"]:
        copy = True
    if args["extension"]:
        extension = "." + args["extension"]
    if args["minimumfilesize"]:
        minimumfilesize = args["minimumfilesize"]
        
    main(inputFolder, outputFolder, extension, copy, minimumfilesize)
