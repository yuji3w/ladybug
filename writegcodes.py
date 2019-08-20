#I am going to try and write Gcodes!
#this program will call define scan to generate locations
#then convert it to gcode
#then save it line by line to a text file

import numpy
from definescan import *

def GenerateCode(x,y,z, r=0, f = '100'):

    #generates a line of absolute Gcode for a list of values. literally just stringing
    StepsPerMM = 100 
    
    line = "G1"
    line += " X" + str(round(x,4))
    line += " Y" + str(round(y,4))
    line += " Z" + str(round(z,4))
    line += " F"
    line += f #feedrate in units/minute
    return line

def SaveLine(filename,line):
    #saves a line to specified file.

    try:
        with open(filename, 'w') as file:
            file.write(line)

    except FileNotFoundError:
        print('no file aahhhh')


def main():

    a = DefineScan(0,15.2,0,10.5,0,0,0,0,1.2,1.1,1,1)
    for i in range(len(a['X'])):
        x = a['X'][i]
        y = a['Y'][i]
        z = a['Z'][i]
        line = GenerateCode(x,y,z)
        print(line)
    pass
    
if __name__ == '__main__':
    main()

