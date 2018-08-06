import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--folder", required=True, help="folder location")
args = vars(parser.parse_args())

folder = args["folder"]

for file in os.listdir(folder):
	if file.endswith(".jpg"):
		print(file)