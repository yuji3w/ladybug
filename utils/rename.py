# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 17:59:11 2018
RENAMES FILES (not folders) in search_dir by DATE TAKEN

@author: awayne1
"""

# Pythono3 code to rename multiple 
# files in a directory or folder
 
# importing os module
import os

search_dir = "E:\small bee scan\testformist"
NAME_PREFEX = "bee"

os.chdir(search_dir)
files = filter(os.path.isfile, os.listdir(search_dir))
files = [os.path.join(search_dir, f) for f in files] # add path to each file
files.sort(key=lambda x: os.path.getmtime(x))

#Sorts each file

# Function to rename multiple files
def main():
    i = 0
     
    for filename in files:
        dst = NAME_PREFEX + str(i) + ".png"
        src = filename
        dst = search_dir + "\\" + dst
         
        # rename() function will
        # rename all the files
        os.rename(src, dst)
        i += 1
        print(dst)
# Driver Code
if __name__ == '__main__':
     
    # Calling main() function
    main()