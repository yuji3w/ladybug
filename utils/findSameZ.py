import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--folder", required=True, help="folder location")
parser.add_argument("-e", "--extension", required=False, help="file extension without .")
args = vars(parser.parse_args())

folder = args["folder"]
extension = ".png"
if args["extension"]:
	extension = "." + args["extension"]


for file in os.listdir(folder):
	if file.endswith(extension):
		print(file)