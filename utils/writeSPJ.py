import os

rootFolder = r"G:\Aharon\SCANS\rocketbeetle"
outputFolder = r"G:\Aharon\SCANS\rocketbeetle"

def createSPJ(folder):
	global SPJ
	folderAboveName = os.path.basename(os.path.dirname(folder))
	folderName = os.path.basename(os.path.normpath(folder))
	SPJ = open(os.path.join(outputFolder,"R"+folderAboveName+"Z"+folderName+".spj"), "x")

def modifySPJ(folder):
	global SPJ
	folderAboveName = os.path.basename(os.path.dirname(folder))
	folderName = os.path.basename(os.path.normpath(folder))
	SPJ = open(os.path.join(outputFolder,"R"+folderAboveName+"Z"+folderName+".spj"), "w")
	SPJ.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
	SPJ.write("<stitchProject version=\"2.0\" cameraMotion=\"rigidScale\" projection=\"perspective\">\n")
	SPJ.write("  <sourceImages>\n")
	for root, dirs, files in os.walk(folder):
		for file in files:
			if file.endswith('.jpg'):
				SPJ.write("    <sourceImage filePath=\"")
				SPJ.write(os.path.join(folder,file))
				SPJ.write("\" />\n")
	SPJ.write("  </sourceImages>\n")
	SPJ.write("</stitchProject>")


rawFolders = [x[0] for x in os.walk(rootFolder)]
print(rawFolders)
#f = open("hello.aio","x")
for folder in rawFolders:
	if any(file.endswith(".jpg") for file in os.listdir(folder)):
		#print(folder)
		createSPJ(folder)
		modifySPJ(folder)
		#f = open(, "x")