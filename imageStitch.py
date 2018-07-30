import cv2
import os



folder = r"C:\Users\wangy\Desktop\stitchem"
output = r"C:\Users\wangy\Desktop\stitchemoutput"

stitcher = cv2.createStitcher(False)


#img1 = cv2.imread(r"C:\Users\wangy\Desktop\Sz0v9.png")
#img2 = cv2.imread(r"C:\Users\wangy\Desktop\zGwTt.png")


#stitchedtemp = stitcher.stitch((img1,img2))
#cv2.imwrite(r"C:\Users\wangy\Desktop\stitchemoutput\whatevs.jpg",stitchedtemp[1])




fileList = []
imgList = []

for file in os.listdir(folder):
		if file.endswith(".jpg"):
			fileList.append(os.path.join(folder,file))

for file in fileList:
	img = cv2.imread(file)
	imgList.append(img)

imgTuple = tuple(imgList)

stitched = stitcher.stitch(imgList)

cv2.imwrite(os.path.join(output,os.path.basename(fileList[0])),stitched[1])
