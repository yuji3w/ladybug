#takes the PD results of a laser scan and the original positions
#and turns that into an attempted greyscale image

import pickle
import os
import statistics
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

scan_data = r"G:\Aharon\LADYBUG PROJECT FILES\laserscans\August15 greypaper 20x20\laserresults.pkl"

#this is something that will be contained in the file data

#note that X and Y is kind of arbitrary
X_Len = 21
Y_Len = 21

data = pickle.load( open( scan_data, "rb" ) )

X_loc = data[0][0]
Y_loc = data[1][0]
results = data[2][0]

min_val = min(results)
max_val = max(results)
mean_val = statistics.mean(results)
length = len(results)
print('the min val is {}, the max val is {}, the mean val is {}, and there are {} values'.format(min_val,max_val,mean_val,length))

#call min_val zero

#results[:] = [x - min_val for x in results]

#convert vals to a map from 0 to 255 for greyscale
#mapped_results = np.interp(results,[min_val,max_val],[0,255])
#to round it:
mapped_results = np.interp(results,[min_val,max_val],[0,255])
#mapped_results = mapped_results.astype(int)

pixels_array = np.asarray(mapped_results)
pixels_array = pixels_array.reshape(Y_Len,X_Len)

#pixels_array = pixels_array.transpose()

img = Image.fromarray(pixels_array, 'L')

#img = Image.fromarray(pixels_array.reshape(Y_Len,X_Len), 'L')

#pixels_array.reshape(X_Len,Y_Len)
#pixels_array = np.expand_dims(pixels_array, axis=2)

img.show()

#plt.imshow(pixels_array, cmap="gray")
#plt.show()