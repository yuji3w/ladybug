'''
Kills all files in folder (no subdirectories)

Ahron and Yujie

'''

#TODO: get running. Won't work because of permissions. -Yujie
#get it working programmatically like you did before, Ahron


import os
import glob
import argparse

def main(folder, extension):
	files = glob.glob(folder)
	for f in files:
		os.remove(f)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", required=True, help="folder location")
	parser.add_argument("-e", "--extension", required=False, help="file extension without .")
	args = vars(parser.parse_args())
	folder = args["input"]
	extension = ".png"
	if args["extension"]:
		extension = "." + args["extension"]
	main(folder, extension)