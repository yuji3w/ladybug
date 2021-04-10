    #!/usr/bin/env python3

#MARCH 16 2020! Convert beefy gui to try and run a scan with gcodes
#and like physically clicking buttons on the dinolite program

#December 28 2020: It has been a heck of a year since March 16.



from numpy import * #for generating scan parameters
import random #for repeatability tests
import time
import copy
import glob
import math
import os
import shutil
import string
import tkinter as tk #contains GUI, can be removed if converted to headless
from tkinter import font
from tkinter import filedialog
import sys
import select #for timeouts and buzzing when usb gets disconnect
import pickle #for saving scan data and resuming
import serial 
import subprocess
import datetime
import cv2
import re #regular expressions
import threading
from PIL import Image, ImageTk
from imutils.video import FPS
from utils.imagetools import * #tools for manipulating images during scan
from utils import findSameZ
from utils import RemoveBlurry
from utils.pickandplace import * #Automated PCB inspection test
import tsp #traveling salesman module. Requires pandas. Really slow
import utils.track_ball as ObjectTracker 
import utils.findcolors as findcolors #for object tracking with color
import circlify #for calculating evenly spaced points within circle for autofocus
import serial.tools.list_ports

#dictionary passed into gridscan. At minimum must change
#scanlocations! Can be made with definescan
#The fact that this isn't a class is the reason my code is always broke

DefaultScan = {'FileType':".jpg",'Width':640,'Height':480
                  ,'CameraSettings': [],'Restarted Scan':False,
                  "AutoFocus":False, "Z Heights": [],
               'ScanLocations':{'X':[],'Y':[],'Z':[],'R':[]},
               "Save Location":"", "Start Time":0, "PointInScan": 0,
               "Failures":[], "VibrationControl":0.15,
               'Camera':False, "ScanRates": [], 'FocusDictionary':{}}


#Distances from home position in steps for each motor.
#Starts at "0" so if you don't have any switches just move them there before running the program.



GlobalX = 0 #left and right (on finder)
GlobalY = 0 #towards and away from you (on finder)
GlobalZ = 0
GlobalR = 0 #keep same naming scheme, but R = rotation

#These are scan parameters intended to be set by the GUI and can otherwise be ignored

XScanMin = 0
XScanMax = 0
YScanMin = 0
YScanMax = 0
ZScanMin = 0
ZScanMax = 0
XScanStep = 100 #default step parameters,
YScanStep = 100
ZScanStep = 500

XMin = 0 #normally but theoretically could be altered by user
YMin = 0 
ZMin = 0 
RMin = 0 
XMax = 125 #tronxy 3d printer in mm
YMax = 150
ZMax = 120
RMax = 33.33 #not great but mm per rotation

BigXY = 5 #motion in mm for buttons, default, could be user reset
LittleXY = 0.5
LittleZ = 0.1

XSpeed = 2000 #standard max speeds for movement
YSpeed = 2000
ZSpeed = 1000

BigZ = 2
LittleZ = 0.1 #maybe even too big but can be played with

win = tk.Tk()
myFont = tk.font.Font(family='Helvetica', size=12, weight='bold')
mySmallFont = tk.font.Font(family='Helvetica', size=9, weight='bold')
myBigFont = tk.font.Font(family='Helvetica', size=20,weight='bold')
font.families()


def ConvertXYToPixelLocations(X=-1,Y=-1, PixelsPerMM = 370,
                             ImageXWidth=640,ImageYHeight=480):
    #Takes an image and tells you where the pixels *would be* if you had
    #a super gigantic image that encompassed the whole possible build plate
    #This keeps everyone on same page when image resizes and stuff
    #remember: Indexing is top left with opencv, but we want it to be bottom left!
    #We're leaving it at bottom left in this function, but when we smush we have to convert it
    
    if X == -1:
        X = GlobalX
    if Y == -1:
        Y = GlobalY
        
    ImageXCenter = int(X * PixelsPerMM)
    ImageXLow = int(ImageXCenter - (ImageXWidth/2))
    ImageXHigh = int(ImageXCenter + (ImageXWidth/2))

    ImageYCenter = int(Y * PixelsPerMM)
    ImageYLow = int(ImageYCenter - (ImageYHeight/2))
    ImageYHigh = int(ImageYCenter + (ImageYHeight/2))

    return ImageXLow,ImageXHigh,ImageYLow,ImageYHigh

    

def GoToSmush(MajorImage,
              X=-1,Y=-1,Z=-1,
              PixelsPerMM = 370,
              CanvasXMin=0,CanvasYMin=0,
              CanvasXMax=40,CanvasYMax=40,
              ImageXWidth=640,ImageYHeight=480):
    #Smushes images together. Assumes MajorImage is big enough.
    #note: indexing for images starts from top left, not bottom left 
    if X== -1:
        X = GlobalX
    if Y == -1:
        Y = GlobalY
    if Z == -1:
        Z = GlobalZ

    MinorImage = MoveConfirmSnap(X,Y,Z,cap)

    XLow,XHigh,YLow,YHigh = ConvertXYToPixelLocations(X=X,Y=Y, PixelsPerMM = PixelsPerMM,
                             ImageXWidth=ImageXWidth,ImageYHeight=ImageYHeight)
    
    MajorImage = CombineImages(XLow,XHigh,YLow,YHigh,MinorImage,MajorImage)
    return MajorImage

def CombineImages(XLow,XHigh,YLow,YHigh, MinorImage, MajorImage):
    #Combines images. CONVERTS FROM BOTTOM LEFT to TOP LEFT positions
    try:
        MajorHeight = shape(MajorImage)[0]
        FlippedYLow = MajorHeight-YLow
        FlippedYHigh = MajorHeight - YHigh
        
        #MajorImage[YLow:YHigh, XLow:XHigh] = MinorImage
        MajorImage[FlippedYHigh:FlippedYLow, XLow:XHigh] = MinorImage
        
    except ValueError: #MajorImage was too small
        print('The shape of MinorImage is {} and the shape of Major is {}'
        .format(shape(MinorImage),shape(MajorImage)))
        #print('YLow is {} YHigh is {}  XLow is {} XHigh is {}'.format(YLow,YHigh,XLow,XHigh))
        print('You stepped out of bounds. You should really do something about that')
        #should increase the size of the image
        #DoubleImage
        
    return MajorImage

def StackFolder(folder, StackedOutputFolder, ZMapOutputFolder, grid = (32,32)):
    """ Stacks series of folders and saves their outputs without stitching
        Basically just breaking stackstitchfolder in half; might do the
        other half too and just call the subfunctions"""

    if not os.path.exists(StackedOutputFolder):
        print("can't find {}, creating directory".format(StackedOutputFolder))
        os.makedirs(StackedOutputFolder)
    if not os.path.exists(ZMapOutputFolder):
        print("can't find {}, creating directory".format(ZMapOutputFolder))
        os.makedirs(ZMapOutputFolder)

    ImageFolders = [x[0] for x in os.walk(folder)][1:]

    lowest_Z = 1000
    highest_Z = 0
    for folder in ImageFolders: #quick fix for getting lowest Z up front
        files = os.listdir(folder)
        
        for file in files:
            file = folder + "\\" + file
            
            ZCoord = MakePositionsFromName(file)[2]
            if ZCoord < lowest_Z:
                lowest_Z = ZCoord
            if ZCoord > highest_Z:
                highest_Z = ZCoord

    for i, folder in enumerate(ImageFolders):        
        files = os.listdir(folder)
        ZCoord = []
        frames = []

        if not i % 10:
            print("{} of {} sets of folders".format(i,len(ImageFolders)))

        
        for file in files:
            file_end = file #base filename for saving files in new file
            file = folder + "\\" + file
            positions = MakePositionsFromName(file)
            X,Y,Z = positions[0],positions[1],positions[2]
            frame = cv2.imread(file)
            frames.append(frame)
            ZCoord.append(Z)
        
        Stacked, IndexMap = max_pool_subdivided_images_3d(frames, grid) #stack
        TrueZ3D = GetTrueZ3D(IndexMap, ZCoord) #convert map into raw Z values 

        DepthImage = NormalizeZMap(TrueZ3D,
                                   lowest_Z = lowest_Z,
                                   highest_Z = highest_Z) #problem: "blank space" is 0...
        DepthImage = DepthImage.astype(uint8)
        
        #idea: calculate mean of zmap and use this for z position in filename
        StackedFile = StackedOutputFolder + "\\" + file_end
        ZMapFile = ZMapOutputFolder + "\\" + file_end
        

        SavePicture(StackedFile,Stacked)
        SavePicture(ZMapFile,DepthImage)

    print('Done stacking folders')

def StitchFolder(folder, PixelsPerMM = 370, GiantSize = 'default', StitchZMap = False):

    
    if GiantSize == 'default': #Quick fix to work with low res scans
        #GiantSize = min(int(26000/PixelsPerMM),120)
        GiantSize = 120 #go for broke 
    if not StitchZMap:
        MajorImage = MakeGiantImage(PixelsPerMM = PixelsPerMM,
                                    CanvasXMin = 0, CanvasXMax = GiantSize,
                                    CanvasYMin = 0, CanvasYMax = GiantSize)
    else:
        MajorImage = MakeGiantImage(PixelsPerMM = PixelsPerMM, #ZMap image! FLOATS!
                          CanvasXMin = 0, CanvasXMax = GiantSize,
                                CanvasYMin = 0, CanvasYMax = GiantSize,
                          dim=1, floats=True) #black and white
    
        
    files = os.listdir(folder)
    frames = []

    for file in files:
        file = folder + "\\" + file
        positions = MakePositionsFromName(file)
        X,Y,Z = positions[0],positions[1],positions[2]

        
            
        frame = cv2.imread(file)
        frames.append(frame)
            
        XLow,XHigh,YLow,YHigh = ConvertXYToPixelLocations(X,Y,PixelsPerMM) #offset target?
        if not StitchZMap:
            MajorImage = CombineImages(XLow,XHigh,YLow,YHigh, frame, MajorImage) 
        else: #Banish the 3rd dimension
            MajorImage = CombineImages(XLow,XHigh,YLow,YHigh, frame[:,:,0], MajorImage) 
    print('cleaning up final image...')

    #inefficiently crop blank space from images.
    #Necessary for ZMap because blank "0" areas mess up normalization 
    MajorImage = RemoveBlank(MajorImage)

    if StitchZMap:
        MajorImage = NormalizeZMap(MajorImage) #problem: "blank space" is 0...
        MajorImage = MajorImage.astype(uint8)#.astype result of 3 hrs work
    
    return MajorImage
 

def StackStitchFolder(folder, PixelsPerMM = 370, grid = (32,32),GiantSize='default'):
    #returns stacked and stitched big image along with depthmap
    #expects folders to be already ZSorted
    #grid is how divided images are. Acceptable: 32, 40, 80, 160 (higher = slow)
    #question: How to deal with max image size problem
    #needs to save individual stacked pics for later manipulating
    
    if GiantSize == 'default': #Quick fix to work with low res scans
        GiantSize = min(int(26000/PixelsPerMM),120) 
    MajorImage = MakeGiantImage(PixelsPerMM = PixelsPerMM,
                                CanvasXMin = 0, CanvasXMax = GiantSize,
                                CanvasYMin = 0, CanvasYMax = GiantSize)
    ZMap = MakeGiantImage(PixelsPerMM = PixelsPerMM,
                          CanvasXMin = 0, CanvasXMax = GiantSize,
                                CanvasYMin = 0, CanvasYMax = GiantSize,
                          dim=1, floats=True) #black and white

    ImageFolders = [x[0] for x in os.walk(folder)][1:]
    for i, folder in enumerate(ImageFolders):
        files = os.listdir(folder)
        ZCoord = []
        frames = []

        if not i % 10:
            print("{} of {} sets of folders".format(i,len(ImageFolders)))
        
        for file in files:
            file = folder + "\\" + file
            positions = MakePositionsFromName(file)
            X,Y,Z = positions[0],positions[1],positions[2]
            frame = cv2.imread(file)
            frames.append(frame)
            ZCoord.append(Z)
        
        Stacked, IndexMap = max_pool_subdivided_images_3d(frames, grid) #stack
        TrueZ3D = GetTrueZ3D(IndexMap, ZCoord) #convert map into raw Z values 
        XLow,XHigh,YLow,YHigh = ConvertXYToPixelLocations(X,Y,PixelsPerMM)

        MajorImage = CombineImages(XLow,XHigh,YLow,YHigh, Stacked, MajorImage)    
        ZMap = CombineImages(XLow,XHigh,YLow,YHigh, TrueZ3D, ZMap) #the problem 

    print('cleaning up final images...')

    #inefficiently crop blank space from images.
    #Necessary for ZMap because blank "0" areas mess up normalization 
    ZMap = RemoveBlank(ZMap)
    MajorImage = RemoveBlank(MajorImage)
    
    DepthImage = NormalizeZMap(ZMap) #problem: "blank space" is 0...
    DepthImage = DepthImage.astype(uint8)#.astype result of 3 hrs work
    
    return MajorImage, DepthImage, ZMap
 
        
def DoubleImage(ParentImage):
    #Does the yujie thing and doubles the image
    pass #lol where do you extend it 

def RemoveBlank(image):
    #https://stackoverflow.com/questions/13538748/crop-black-edges-with-opencv
    #Expensively removes black/blank boundaries of large image
    
    if len(image.shape) == 2: #quick fix for 2D images 
        y_nonzero, x_nonzero = np.nonzero(image)
    else:
        y_nonzero, x_nonzero, _ = np.nonzero(image)
    return image[np.min(y_nonzero):np.max(y_nonzero), np.min(x_nonzero):np.max(x_nonzero)]

def MoveToPixelLocation(XPix,YPix,Z = -1, PixelsPerMM = 370):
    #moves to pixel location with idealized grid with bottom left zero
    #moves to center of that image (bad?)
    #To deal with the rounding problem, just report your actual movement
    #since we only have 0.1 mm step precision
    #returns pic, actual Xpos, Actual Ypos, actual XPix, nearest YPix, 

    if Z == -1:
        Z = GlobalZ 
    
    FinXPos, FinYPos, FinXPix, FinYPix = ConvertPixelToXY(
        XPix, YPix, PixelsPerMM = PixelsPerMM)
    
    pic = MoveConfirmSnap(FinXPos,FinYPos,Z,cap)

    return pic,FinXPos,FinYPos,FinXPix,FinYPix
    
def ConvertPixelToXY(XPix,YPix, PixelsPerMM = 370, debug = True):
    #convert pixel to NEAREST 0.1 XY locations.
    #Returns XY location and REAL XPix and YPix gone to
    RawXPos = XPix/PixelsPerMM
    RawYPos = YPix/PixelsPerMM

    NearestXPos = round(RawXPos,1) #round to 0.1 MM
    NearestYPos = round(RawYPos,1)

    NearestXPix = round(NearestXPos * PixelsPerMM,2) #will be float
    NearestYPix = round(NearestYPos * PixelsPerMM,2)

    if debug:
        print("""At desired XPix {} and desired YPix {},
    The closest X mm is: {} and the Closest Y mm is: {},
    which corresponds to XPixel {} and YPixel {}""".format(
                   XPix,YPix,NearestXPos,NearestYPos,NearestXPix,NearestYPix))
    return (NearestXPos,NearestYPos,NearestXPix,NearestYPix)


def SmushScan(positions, PixelsPerMM = 370):
    #Goes to positions and blindly stitches them together

    MajorImage = MakeGiantImage(PixelsPerMM = PixelsPerMM)

    XStart = positions['X'][0]
    YStart = positions['Y'][0]

    for i in range(len(positions['X'])):
        X = positions['X'][i]
        Y = positions['Y'][i]
        Z = positions['Z'][i]

        MajorImage = GoToSmush(MajorImage,X,Y,Z,PixelsPerMM=PixelsPerMM)
        time.sleep(0.15)

    name = "capture\\Smush test from X {} to {}, Y {} to {} .jpg".format(str(XStart),str(X),str(YStart),str(Y))
    SavePicture(name,MajorImage) #no batching, all images are in memory. Careful!


def SmushDemo(StartX=7.5,StartY=4,StartZ=7.9):
    MajorImage = MakeGiantImage()
    Home()
    time.sleep(3)
    
    MoveConfirmSnap(StartX,StartY,StartZ,cap)
    for i in range(10):
        for j in range(10):
            X,Y,Z = StartX + i, StartY + j, StartZ
            MajorImage = GoToSmush(MajorImage,X,Y,Z)
            time.sleep(0.15)

    name = "capture\\test at X {}, Y {}.jpg".format(str(X),str(Y))

    #MajorImage = RemoveBlank(MajorImage) #EXPENSIVE
    SavePicture(name,MajorImage) #expensive if large

def MakeGiantImage(PixelsPerMM = 370,
                        BaseWidth = 640, BaseHeight = 480,
                        CanvasXMin = 0, CanvasYMin = 0,
                        CanvasXMax = 70, CanvasYMax = 70, dim=3,
                        floats=False):#floats for using with decimal z heights
    #Will initialize a HUGE blank image to encompass the maximum possible search area
    #And which will then have real image information filled in
    #Because Yujie says that it's more efficient to do this than to expand on command
    XPixels = round(PixelsPerMM * (CanvasXMax - CanvasXMin))
    YPixels = round(PixelsPerMM * (CanvasYMax - CanvasYMin))
    
    if dim == 1: #quick fix for pure 2d matrices. Sorry!
        if floats:#Raw ZHeights need floats to combine without rounding!!
            YujieImage = np.zeros((YPixels,XPixels), np.float64)
        else:
            YujieImage = np.zeros((YPixels,XPixels), np.uint8) 
    else:
        if floats:#too tired to save 2 lines with proper fix
            YujieImage = np.zeros((YPixels,XPixels,dim), np.float64)
        else:
            YujieImage = np.zeros((YPixels,XPixels,dim), np.uint8) #square image because plate is square, surprise!

    
    return YujieImage



def GenerateCode(X,Y,Z,E, speed = 2000): 
    
    #generates a line of absolute Gcode for a list of values. literally just stringing
    #e is extruder 

    line = "G1"
    line += " X" + str(round(X,4))
    line += " Y" + str(round(Y,4))
    line += " Z" + str(round(Z,4))
    line += " E" + str(round(E,4))
    
    line += " F"
    line += str(speed) #feedrate in units/minute
    
    
    return line

def SaveGCode(positions, filename = 'default'):
    #for use with a gcode viewer like ncviewer.com

    if filename == 'default':
        filename = 'GCodes.gx'

    with open (filename, 'w') as GCodeFile:
        for i in range(len(positions['X'])):
            line = GenerateCode(positions['X'][i],positions['Y'][i],positions['Z'][i],positions['R'][i])
            GCodeFile.write(line+"\n")
        GCodeFile.close()
    print('GCodes written to {}'.format(filename))

def SendGCode(GCode,machine='ladybug'):

    if machine == 'ladybug':
        machine = LadyBug
    
    GCode  += " /r\n"
    #print(GCode)
    #return(GCode)
    BytesGCode = GCode.encode('utf-8')
    machine.write(BytesGCode)
    #time.sleep(0.02) #this is for potential conflicts of calling gcodes too fast

def EngageSteppers(machine = 'ladybug'):
    if machine == 'ladybug':
        machine = LadyBug
        
    SendGCode("M84 S36000") #tells it not to turn off motors for S seconds (default 60 grr)
    time.sleep(0.05)
    SendGCode("M302 P1") #prevents errors from 'cold' extrusion
    time.sleep(0.05)
    SendGCode("M203 Z5") #lets z go a bit faster. disabled if using weak nano motor
    #time.sleep(0.05) #disabled for NANO. uncomment if Z too slow
    SendGCode("M17") #engage steppers

def TurnOnFan(speed=250, machine = 'ladybug'): #up to 250, adjust if shrieking
    if machine == 'ladybug':
        machine = LadyBug
    gcode = "M106 S" + str(speed)
    SendGCode(gcode)

def DisengageSteppers():
    SendGCode("M18")

def GetPositions(machine = 'ladybug',tries=1):
    #returns dictionary X,Y,Z and maybe R of actual position at time of request
    #this is the most likely function to be culprit if movement works but scan doesn't
    #Originally meant for normal cartesian marlin
    #This is one of the points of failures, for sure...
    
    sleeptime = 0.05 #can I calculate things in other threads during this time? 
    
    if machine == 'ladybug': #fix so it doesn't fail at runtime. not proper 4sure
        machine = LadyBug 

    previous_buffer = machine.read_all() #clear buffer essentially
    LadyBug.reset_input_buffer() #possible fix attempt 1122021
    previous_buffer = machine.read_all() #someone said do this twice
    
    SendGCode("M114") #report machine status
    
    time.sleep(sleeptime)
    
    for i in range (tries): #communication back and forth not instant, i for failsafe
        try:
            dump = machine.read_until().decode('utf-8') #kept in bytes. read_all inconsistent
        
        except serial.SerialTimeoutException(): #other exceptions found here
        
            print('Serial Timeout Exception') #This NEVER is what gets tripped. 
            return False

            #print('no dump. communication ERROR')
        
        if 'Count' in dump: #precedes actual position data
            try:
                remainder = dump[dump.find('Count'):] #has actual position
            
                Xraw = remainder[remainder.find('X:'):remainder.find('Y')]
                Yraw = remainder[remainder.find('Y:'):remainder.find('Z')]
                Zraw = remainder[remainder.find('Z:'):(remainder.find('E') if 'E' in remainder else None)] #E sometimes in remainderadded for Nano

                X = float(''.join([s for s in Xraw if (s.isdigit() or s == '.')]).strip())
                Y = float(''.join([s for s in Yraw if (s.isdigit() or s == '.')]).strip())
                Z = float(''.join([s for s in Zraw if (s.isdigit() or s == '.')]).strip())

                positions = {'X':X,'Y':Y,'Z':Z,'delay':i*sleeptime,'raw':dump,'prev':previous_buffer}

                return positions
            except Exception:
                print('If this gets printed at fail, go here')
                print('XRaw: {}').format(Xraw)
                print('YRaw: {}').format(Yraw)
                print('ZRaw: {}').format(Zraw)
                return False
        time.sleep(sleeptime) #and loop back to try again

    if not dump:
            #This is one big unsolved problem. Why did the connection break?
            return False


def WaitForConfirmMovements(X,Y,Z,attempts=100): #50 is several seconds
    #should make it based around predicted amount of time; fails in unusual slow scans 
    #calls get_positions until positions returned is positions desired
    #if it fails twice that means we're not moving at all.
    #that or failure to get positions at all means something went wrong. 


    PositionsList = [] #for debugging why things aren't moving at all
    
    for j in range(attempts):
            #time.sleep(0.05) #gonna try just giving the delay to getpositions

        positions = GetPositions()
        
        PositionsList.append(positions)
            
        if positions:
            
            if (math.isclose(X,positions['X'],abs_tol=0.1) #microns getting lost
                and math.isclose(Y,positions['Y'],abs_tol=0.1)
                and math.isclose(Z,positions['Z'],abs_tol=0.1)
                ):
                
                return positions #we have arrived
            else:
    
                if j > 15 and PositionsList[j] == PositionsList[j-14]:
                    print('Printer not moving, but not at destination? check inputs')
                    
                    return False # Different failure condition than unable to communicate. Bad inputs
                
                continue
            
    #exceeded allotted attempts. This is a COMMUNICATION issue! WHYYYYY
    #update 1/16/2021 WHYYYYYYYYY
    print('exceeded allotted {} attempts. USB disconnect?'.format(attempts))
    return False

def RestartSerial(port= -1, BAUD = -1,timeout=1): #from 0.1 to 1 for timeout test

    PossibleBauds = (115200, 9600) #expand as more options are known

    FoundMachine = False
    
    global LadyBug #below functions expect this global

    try:
        CloseSerial() #will pass if no port by ladybug name open
    except Exception: #if LadyBug turned out to be a boolean or something
        pass

    if port != -1 and BAUD !=-1: #try given parameters first

        while True:

            time.sleep(0.01)
            LadyBug = TryToConnect(port,BAUD, timeout=timeout)
            if LadyBug:
                FoundMachine=True
                break
            else:
                print('Failed to connect with port {}, BAUD {}'.format(port,BAUD))
                inputstr = input("""

You may try to specify a port and BAUD rate or just a port.
Examples: '6, 115200' or just '8' (no quotes).
Or press enter to try all available ports automatically.
'q' to quit. """)

                inputs = inputstr.split(',')

                if len(inputs) == 2: #There's got to be a better way!
                    port = int(inputs[0])
                    BAUD = int(inputs[1])

                elif len(inputs) == 1 and inputs[0].isdigit():
                    port = int(inputs[0])

                elif inputs[0].lower() == 'q':
                    print("Sorry you're having trouble.")
                    return False
                
                else:
                    break #and try to automatically connect

    if not FoundMachine:
        #find and search automatically
        ports = []
        for i in serial.tools.list_ports.comports():
            ports.append(str(i).split(" ")[0])
        PortsAndBauds = [[a, b] for a in ports for b in PossibleBauds if a != b] 
        for val in PortsAndBauds: #zipped together so we only need one break 
            port, BAUD = val[0],val[1]
            LadyBug = TryToConnect(port,BAUD,timeout)
            if LadyBug:
                FoundMachine = True
                break
                
    if FoundMachine:
        print('Successful connection on port {} with Baud rate {}'.format(port, BAUD))
        time.sleep(1)
        EngageSteppers()
        time.sleep(1)
        
        #TurnOnFan()
        #time.sleep(1.5)
        return LadyBug #name of controllable CNC machine

    else:
        print("Unable to connect. Um... jiggle the cables?")
        
def TryToConnect(port, BAUD, timeout):
    global LadyBug

    if isinstance(port, str):
        if 'COM' not in port:
            port = 'COM' + port
            
    elif isinstance(port, int):
        port = 'COM' + str(port)
    else:
        print('invalid connection parameters')
        return False

    print("trying to connect with port {} and BAUD {}...".
                    format(port, BAUD))
    try: 
        LadyBug = serial.Serial(port, BAUD, timeout=timeout)
        time.sleep(1)
        if LadyBug:
            return LadyBug

    except serial.serialutil.SerialException:
        return False
    
def UpdateFocusDict(FocusDictionary, location, pic):
    #used to allow threaded calculation of focus during time waits
    blur = CalculateBlur(pic)
    FocusDictionary[location] = blur

def FocusDemo(cap):
    #Tinyscopecap is first camera with built in autofocus
    #turns out it's really easy to alter with opencv
    #this is just so I don't forget the commands

    cap.set(cv2.CAP_PROP_AUTOFOCUS,0)
    
    for i in range (5):
        for i in range(0,255,5):
            cap.set(cv2.CAP_PROP_FOCUS,i)
        for i in range(255,0,-5):
            cap.set(cv2.CAP_PROP_FOCUS,i)


def CloseSerial(machine = 'ladybug'):
    try:
        if machine == 'ladybug':
            machine = LadyBug
        machine.close()
    except NameError:
        pass

def CircleDemo(cap, speed=500): #finds outline, focuses, goes around edge
    param = CalculateOutline()
    xc, yc, r = param[0], param[1], param[2]
    MoveConfirmSnap(xc,yc,GlobalZ, cap)
    focus, pic = FindZFocus()
    MoveConfirmSnap(xc, yc-(r-2), focus, cap)
    SendGCode("G2 I0 J{} F{}".format(r-1.5,speed))
    #Arc shape. Move back a bit to center around edge. 
    return (xc, yc, r)

def MakeArc(XCenter,YCenter,Radius, Z=-1, speed='default'):
    #part of demo for going around a coin's edge, I want to call this to see
    #if I can use ICE video feature to stitch about 50 times faster
    if Z==-1:
        Z=GlobalZ
    if speed == 'default':
        speed = Radius * 100 #takes about 3.14159 seconds or so
    MoveConfirmSnap(XCenter,YCenter-(Radius-2), Z, cap)
    SendGCode("G2 I0 J{} F{}".format(Radius-1.5,speed))
    time.sleep(speed/800) #otherwise MoveConfirmSnap will timeout
    MoveConfirmSnap(XCenter,YCenter-(Radius-2),Z,cap)

def is_dark(img, thrshld = 15):
    is_dark = np.mean(img) < thrshld
    return is_dark

def FoundCoin(pic, threshold = 50):
    #magically determines if a picture contains a coin...
    #wait, does it? No! It just checks to see if it's blurry!
    #It assumes we're focused on the build plate! Ridiculous!
    #And yet, this is WAY more robust than the last method.
    #amended: if brightness very low, darkness is used as metric instead
    #helps if using highly polarized light

    if is_dark(pic): #light = coin if brightness very low
        CoinScore = threshold + 1
    else:
        CoinScore = CalculateBlur(pic)

    Coinscore = round(CoinScore,1)
    
    if CoinScore < threshold:
        return True, CoinScore
    else:
        return False, CoinScore

def AutoCoin(cap,
             SearchXMin = 20, SearchXMax = 100,
             SearchYMin=20, SearchYMax=100,
             SearchZMin = 0,SearchZMax = 5,
             FieldOfView = 1.6, FocusPoints = 7,
             MaxFocusPoints = 10,
             DepthOfField = 0.1, #0.05 for high res 
             FirstRadius = 10,
             SaveLocation = "AutoCoin\\",
             FocusDictionary = {},
             AcceptableBlur = 50, DrawCoolArc = True):
    #This will do a search pattern and when it finds a coin it will
    #automatically calculate the radius of the coin
    #and scan it within autofocused-determined parameter
    
    XMovement, YMovement = round(FieldOfView * 0.8,1), round(FieldOfView*0.6,1)

    
    positions = GetPositions()
    if (positions['X'] == 0 or
        positions['Y'] == 0 or
        positions['Z'] == 0):
        
        Home()
   
    
    WaitForConfirmMovements(0,0,0)
    TrueCoins = {(0,0):{'R': 0, 'PointsOfFocus': []}} #(X, Y): Radius, FocusHeights, anything else

    #1.5 callibrate against build plate. BlankPicture fills circle gaps
    BlankPicture = MoveConfirmSnap(SearchXMin,SearchYMin,0,cap)
    (BuildPlate, FocusPic) = FindZFocus()
    
    XYGrid = DefineScan(SearchXMin,SearchXMax,SearchYMin,SearchYMax,
                        BuildPlate,BuildPlate,1,1,FirstRadius,FirstRadius,1,1)
    XLocations, YLocations = XYGrid['X'], XYGrid['Y']
    
    
    for i in range (len(XLocations)):    #1: rough grid search
            
        X, Y, Z, R = XLocations[i],YLocations[i], BuildPlate, GlobalR

        pic = MoveConfirmSnap(X,Y,Z,cap)

        #2: Magic found a coin function
        truth, val = FoundCoin(pic) #bool, score
        
        if truth: #magic
            print('found a possible coin (score: {}) at {},{}'.format(val,X,Y))
            duplicate = False
            for coin in TrueCoins.keys(): #don't scan if duplicate
                TrueX, TrueY, TrueR = coin[0], coin[1], TrueCoins[coin]['R']               
                if (TrueX - X)**2 + (TrueY - Y)**2 <= TrueR**2:
                    print('Nevermind, already scanned this area')
                    duplicate = True 
                    break

            if not duplicate: #scan coin and add results to TrueCoins
                
                results = CalculateOutline(X,Y,BuildPlate)
        
                if not results: #False Positive or can't find boundaries
                    continue
            else:
                continue
            
        else:
            continue
        #add 1 to radius to account for weird lumpy coins
        XMiddle, YMiddle, Radius = results[0], results[1], results[2] + 1.5
        TrueCoins[(XMiddle,YMiddle)] = {'R': Radius, 'PointsOfFocus': []}
        XYFocusPoints = DivideCircle(XMiddle,YMiddle,Radius,FocusPoints) #optional: scanlocations
        MoveConfirmSnap(XMiddle,YMiddle,GlobalZ,cap)
        BasicHeight, MiddlePic = FindZFocus()

        if BasicHeight <= BuildPlate + 0.1: #too close, another false positive
            print('False Positive, focus height at {}, bottom surface at {}'.format(BasicHeight,BuildPlate))
            continue

        if DrawCoolArc: #this does absolutely nothing useful
            MakeArc(XMiddle,YMiddle,Radius)
        
        low = (BasicHeight - ((MaxFocusPoints//2) * DepthOfField))
        high = (BasicHeight + ((MaxFocusPoints//2) * DepthOfField))
        ZHeights = GenerateZ(low,high,DepthOfField)
        FocusSet = set()
        
        for point in XYFocusPoints: #places to check focus
            
            xfocus, yfocus = point[0], point[1]
            MoveConfirmSnap(xfocus,yfocus, BasicHeight, cap)
            
            FocusHeight, CoinFocusPic = FindZFocus(ZHeights,Comprehensive=True) #Future: analyze subimage


            if is_dark(CoinFocusPic): #prevent focusing on edges
                print("off the edge AKA dark pic, don't count this one")
                continue
            
            TrueCoins[(XMiddle,YMiddle)]['PointsOfFocus'].append((xfocus,yfocus,FocusHeight,CoinFocusPic))
            FocusSet.add(FocusHeight) #Future: Make sure it's not too many images, or use best ones
            
            #Add to FocusDictionary here

        
        FocusList = sorted(list(FocusSet))

        print('Z Heights we are looking at: {}'.format(FocusList))

        #Calculate boundaries. Rectangle first, then circle
        GridLocations = DefineScan(XMiddle - Radius,
                                   XMiddle + Radius,
                                   YMiddle - Radius,
                                   YMiddle + Radius,
                                   FocusHeight, FocusHeight,
                                   1, 1, XMovement,YMovement, 1, 1)
        
        ScanLocations = GridToCircle(GridLocations,XMiddle,YMiddle,Radius)  
        ScanLocations = InterlaceZ(ScanLocations,ZCoord = FocusList)
        FullLocations = InterlaceZ(GridLocations,ZCoord=FocusList)
        
        
        
        DefaultScan['ScanLocations'] = ScanLocations
        DefaultScan['Camera'] = cap
        DefaultScan['FocusDictionary'] = FocusDictionary
        
        if SaveLocation == 'Default': #prompts user for filedialog
            GridScan(DefaultScan)
        
        else:
            ScanName = "Scan " + time.strftime("%Y%m%d-%H%M%S")
            folder = SaveLocation + ScanName

            if not os.path.exists(folder): #To save in the same folder after restart
                    os.makedirs(folder)
                    
            DefaultScan['Save Location'] = folder
            DefaultScan['Start Time'] = time.time()
            DefaultScan['Restarted Scan'] = True
            GridScan(DefaultScan)

            print('This coin is done')
            print('Saving missing files...')
            
            Missing = FindMissingLocations(FullLocations,ScanLocations)
            SaveMissingLocations(Missing,folder,BlankPicture)

            print('Starting sort and stack pipeline...') #could thread this
            SortOrStackPipe(folder,extension = ".jpg", 
                            AcceptableBlur = AcceptableBlur,
                            FocusDictionary=FocusDictionary)
            print('Sort and stack pipeline done. Continuing coin search')
            FocusDictionary = {} #Prev step saves it. 

    print('All AutoCoin done')



def SaveMissingLocations(Missing,ParentFolder,FakePicture, FileType='.jpg'):
    for i in range(len(Missing['X'])):
        X, Y, Z, R = (Missing['X'][i],
                      Missing['Y'][i],
                      Missing['Z'][i],
                      Missing['R'][i])
        
        
        folder = MakeFolderFromPositions(X,Y,Z,R,ParentFolder,FileType)
        name  = MakeNameFromPositions(X,Y,Z,R,FileType)    
        SavePicture(folder + "/" + name,FakePicture)
            


def FindMissingLocations(FullLocations, PartialLocations):
    #difference between the two dictionaries
    #sets would be easy but order matters, you know
    
    MissingLocations = {'X':[],'Y':[],'Z':[],'R':[]}
    FullList = []
    PartList = []
    MissList = []
    
    for i in range(len(FullLocations['X'])):
        FullX, FullY, FullZ, FullR = (FullLocations['X'][i],
                                      FullLocations['Y'][i],
                                      FullLocations['Z'][i],
                                      FullLocations['R'][i])
        FullList.append([FullX,FullY,FullZ,FullR])
        
    for i in range(len(PartialLocations['X'])):
        
        PartX, PartY, PartZ, PartR = (PartialLocations['X'][i],
                                      PartialLocations['Y'][i],
                                      PartialLocations['Z'][i],
                                      PartialLocations['R'][i])
        
        PartList.append([PartX,PartY,PartZ,PartR])

    for item in FullList:
        if item not in PartList:
            MissList.append(item)

    for item in MissList:
        MissingLocations['X'].append(item[0])
        MissingLocations['Y'].append(item[1])
        MissingLocations['Z'].append(item[2])
        MissingLocations['R'].append(item[3])
        
    return MissingLocations


def SortOrStackPipe(ParentFolder, FocusDictionary = {},
                    extension = ".jpg", AcceptableBlur = 150):
    #this will take a parent folder containing standard output of scan
    #create symbolic copies of all files sorted by X/Y location
    #get rid of all files with no useful information (completely blurred)
    #decide if stacking is worth it for any image sets, and if it is,
    #will put those in its own special folder and in future attempt stack
    #TO PREVENT NEED FOR STACKING set the acceptable blur to a high number
    #amended to work with pickle'd dictionary file before calculating values again
    
    rawFolders = [x[0] for x in os.walk(ParentFolder) if os.path.isdir(x[0])][1:]
    
    originals = ParentFolder + "\\Originals (sorted by Z height)"

    if not os.path.exists(originals): 
        os.makedirs(originals)
    else:
        print('expecting folder to be original unsorted. Problems ahead!')

    for original in rawFolders: #move to originals location
        shutil.move(original,originals)

    AllNames = [y for x in os.walk(originals) for y in glob.glob(os.path.join(x[0], '*'+extension))]
    if not FocusDictionary: #not passed in, try to import pickled file 
        try:
            with open(ParentFolder + "\\FocusDictionary.pkl", 'rb') as FocusFile:
                FocusDictionary = pickle.load(FocusFile)            
        except (FileNotFoundError, EOFError) as e:
            print('unable to find pickle focus dictionary from previous scan. Generating now...')
            FocusDictionary = {}
                
    print('calculating any missing focus metrics for each image...')
    
    for name in AllNames:
        positions = MakePositionsFromName(name)
        if positions not in FocusDictionary: #calculate blur and add to dictionary
            pic = cv2.imread(name)
            blur = CalculateBlur(pic)
            FocusDictionary[positions] = blur
            
    with open(ParentFolder + "\\FocusDictionary.pkl", 'wb') as FocusFile:
        pickle.dump(FocusDictionary, FocusFile)
    
    ZSorted = ParentFolder + "\\Originals (sorted by XY location)"
    DeBlurred = ParentFolder + "\\Blurry removed (sorted by XY location)"
    BestPerStack = ParentFolder + "\\Temp"
    StitchThese = ParentFolder + "\\STITCH THESE for immediate results"
    StitchMix = ParentFolder + "\\Add stacked images here then stitch"
    StackThese = ParentFolder + "\\Stack these if desired"
    
    
    print('making new directories and moving things around...')
    if not os.path.exists(ZSorted):
        os.makedirs(ZSorted)
    if not os.path.exists(DeBlurred):
        os.makedirs(DeBlurred)
    if not os.path.exists(StitchThese):
        os.makedirs(StitchThese)
    if not os.path.exists(StackThese):
        os.makedirs(StackThese)
    if not os.path.exists(StitchMix):
        os.makedirs(StitchMix)
    if not os.path.exists(BestPerStack):
        os.makedirs(BestPerStack)
        
    #Find multiple Z heights for each XY. Future: Do all three in one go
    findSameZ.main(originals,ZSorted,extension=extension,copy=False)
    findSameZ.main(originals,DeBlurred,extension=extension,copy=False)
    findSameZ.main(originals,BestPerStack,extension=extension,copy=False)
    
    #remove unacceptably blurry pics.
    print('sorting out blurry images...')
    RemoveBlurry.main(DeBlurred,AcceptableBlur=AcceptableBlur,extension=extension, FocusDictionary=FocusDictionary)
    #do the same thing again with a high blur amount to get best of stackable images for the lazy
    RemoveBlurry.main(BestPerStack,AcceptableBlur=50000,extension=extension, FocusDictionary=FocusDictionary)

    #determine which definitely don't need stacking (one pic per folder)

    print('moving images that should be stacked for best results...')
    count = 0 
    ImageFolders = [x[0] for x in os.walk(DeBlurred)][1:]
    for folder in ImageFolders:
        files = os.listdir(folder)
        if len(files) == 1:
            source, dest = folder + "\\" + files[0], StitchMix + "\\" + files[0]
            os.link(source,dest)
        else: #move to new directory for stacking. Can't link entire directory for some reason
            count+=1
            parent = os.path.basename(folder)
            dest = StackThese + "\\" + parent
            if not os.path.exists(dest):
                os.makedirs(dest)
            for file in files:
                source = folder + "\\" + file
                dest = StackThese + "\\" + parent + "\\" + file
                os.link(source,dest)
    
    #Transfer best of stackable images too for lazy people
    LazyFolders = [x[0] for x in os.walk(BestPerStack)][1:]
    for folder in LazyFolders:
        files = os.listdir(folder)
        if len(files) == 1:
            source, dest = folder + "\\" + files[0], StitchThese + "\\" + files[0]
            os.link(source,dest)
    
                
    print('{} images need to be stacked before optimal stitching'.format(count))


def MakeNameFromPositions(X,Y,Z,R,FileType = ".jpg"):
    
    XStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(X))))).zfill(5)
    YStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(Y))))).zfill(5)
    ZStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(Z))))).zfill(5)
    RStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(R))))).zfill(5)
    name = "X" + XStr + "Y" + YStr + "Z" + ZStr + "R" + RStr + FileType
    return name


def MakePositionsFromName(name):
    #inverse of Make Name From Positions (harder)
    #from file name or basename returns an (X,Y,Z,R) tuple
    basename = os.path.splitext(os.path.basename(name))[0]
    splitname = re.sub( r"([A-Z])", r" \1", basename).split()
    numbersonly = [x[1:] for x in splitname]
    positions = [float((x[0:-2] + "." + x[-2:])) for x in numbersonly]
    positions = tuple(positions)

    return positions

def GridToCircle(GridLocations,XCenter, YCenter, Radius):
    #given a square grid formed by using DefineScan,
    #Removes terms that would be sticking out if it were a circle.
    #this is so obvious and relatively easy and woo hoo new years eve 2020

    ScanLocations = copy.deepcopy(GridLocations)
    
    track = []
    for i in range(len(ScanLocations['X'])):
        X,Y = ScanLocations['X'][i],ScanLocations['Y'][i]
        if ((X-XCenter)**2) + ((Y-YCenter)**2) > Radius**2:
            track.append(i)
            
    for key in ScanLocations.keys():
        
        for index in sorted(track, reverse=True):
            del ScanLocations[key][index]
                
    print('{} images reduced to {} upon circularification'.format(len(ScanLocations['X']) + len(track), len(ScanLocations['X'])))
    #why does this give the wrong value? 
    return ScanLocations
            
        
def CalculateOutline(StartX = -1, StartY = -1, StartZ = -1,
                     shape = 'coin', SearchDistance = 40,
                     Precision = 1, FOVLOW = 1):
    """calculates outline of an object (for now a coin).
        If your coin is oblong, place the longer side along the Y axis
        because it uses this to calculate the "radius".
        Could really use an overhaul to allow range of shapes"""
    
    StartX, StartY, StartZ = int(StartX), int(StartY), float(StartZ)
    
    if StartX == -1:
        StartX = int(GlobalX)
    if StartY == -1:
        StartY = int(GlobalY)
    if StartZ == -1:
        StartZ = GlobalZ
    
    if shape == 'coin':
        
        #Go to right, then go left then go middle
        #go up, then down, then middle
        #this point is center of coin
        XLeft, XRight, YUpper, YLower = 0, 0, 0, 0
        
        AllGoTo(StartX,StartY,StartZ)
        record = {} #going to use tuples of XYZ as keys... hang on tight!
        for i in range(StartX, StartX + SearchDistance, Precision):

            X, Y, Z = i, StartY, StartZ
            pic = MoveConfirmSnap(X,Y,Z,cap)
            record[(X,Y,Z)] = FoundCoin(pic) #True or False, Score

            if (not record [(X,Y,Z)][0]
            and (X - Precision,Y,Z) in record.keys()
            and not record[(X - Precision, Y, Z)][0]):

                XRight = X - Precision #we overshot
                break

        for i in range(StartX - Precision,
                       StartX - SearchDistance if StartX - SearchDistance > 0 else 0,
                       Precision * -1 ): #now we go left
            X, Y, Z = i, StartY, StartZ

            pic = MoveConfirmSnap(X,Y,Z,cap)

            record[(X,Y,Z)] = FoundCoin(pic)

            if (not record [(X,Y,Z)][0]
                and (X + Precision, Y, Z) in record.keys()
                and not record[(X + Precision, Y, Z)][0]):

                XLeft = X + Precision
                break

        

        if XLeft and XRight:
            XMiddle = round((XLeft + XRight)/2,1) 
            
        else:
            print('failed to find X coin boundaries!')
            return(False)

        for i in range(StartY, StartY + SearchDistance, Precision):

            X, Y, Z = XMiddle, i, StartZ

            pic = MoveConfirmSnap(X,Y,Z,cap)

            record[(X,Y,Z)] = FoundCoin(pic) 

            if ((not record [(X,Y,Z)][0])
                and ((X,Y-Precision,Z) in record.keys())
                and (not record[(X, Y - Precision, Z)][0])):

                YUpper = Y - Precision #we overshot
                break

        for i in range(StartY - Precision,
                       StartY - SearchDistance if StartY - SearchDistance > 0 else 0,
                       Precision * -1 ): #now we go down

            X,Y,Z = XMiddle, i, StartZ

            pic = MoveConfirmSnap(X,Y,Z,cap)

            record[(X,Y,Z)] = FoundCoin(pic)

            if (not record [(X,Y,Z)][0]
                and (X, Y + Precision, Z) in record.keys()
                and not record[(X, Y + Precision, Z)][0]):

                YLower = Y + Precision
                break
            
        if YUpper and YLower:
            Radius, YMiddle = round((YUpper - YLower)/2,1), round((YLower + YUpper)/2,1) 
        else:
            print('failed to find Y boundaries')
            return False

        if Radius <=1: #it's noise
            print('too small false positive')
            return False

        else:
            
            print('Found coin at X: {}, Y: {}, Radius {}'.format(XMiddle,YMiddle,Radius))

        

        return (XMiddle, YMiddle, Radius)     
        
        
def MoveConfirmSnap(X,Y,Z,cap): #I use this a bunch so function it is
    AllGoTo(X,Y,Z)
    success = WaitForConfirmMovements(X,Y,Z)
    
    if not success:
        print('proper timeout catching block needed if this prints (MoveConfirmSnap) ')
    pic = TakePicture(cap)
    return(pic)
    

def DefineScan(XMin, XMax, YMin, YMax, ZMin, ZMax, RMin, RMax, XSteps=100, YSteps=100, ZSteps=1, RSteps=1):
    """core from stack exchange. https://stackoverflow.com/questions/20872912/raster-scan-pattern-python
    modified october 11 2018 to include Z and R, meaning R is now set in absolute positions
    Important: Because its not inclusive in max, it will break if for instance you say rmin = 0 rmax = 0, so we add 1 to all maximums
    so if you dont want to go more than one Z or R, set for instance Zmin=Zmax and ZSteps = 1.

    modified 3/19/20 to act with millimeters and floats (to two decimal places) 
    
    returns a dictioanry of four lists which each contain the absolute positions at every point in a scan for x,y,z,r"""

    XMax = XMax+0.01 #same idea as modifying steps before but this time with 0.01 mm
    YMax = YMax+0.01
    ZMax = ZMax+0.01
    RMax = RMax+0.01


    # define some grids
    xgrid = arange(XMin, XMax, XSteps)
    ygrid = arange(YMin, YMax, YSteps)
    zgrid = arange(ZMin, ZMax, ZSteps)
    rgrid = arange(RMin, RMax, RSteps)

    xscan = []
    yscan = []

    for i, yi in enumerate(ygrid):
        xscan.append(xgrid[::(-1)**i]) # reverse when i is odd
        yscan.append(ones_like(xgrid) * yi)

    # squeeze lists together to vectors
    xscan = concatenate(xscan)
    yscan = concatenate(yscan)

    """up until this, it works just fine for x/y. I am adding
    my own code to account for Z now. Not efficient if there are a LOT of Z changes
    (it does X/Y rastering and returns to initial position for each Z).
    Otherwise it's ok.
    """

    NewXScan = []
    NewYScan = []
    NewZScan = []


    for i in range(len(zgrid)):
        for j in range(len(xscan)):

            NewXScan.append(xscan[j])
            NewYScan.append(yscan[j])
            NewZScan.append(zgrid[i]) #note i not j

    #and for rotations. Same deal as with Z"

    #this too will return empty lists of minr = maxr

    NewNewXScan = [] #I seriously hope nobody ever reads these variable names
    NewNewYScan = []
    NewNewZScan = []
    NewNewRScan = []

    for i in range(len(rgrid)):
        for j in range(len(NewXScan)):
            NewNewXScan.append(NewXScan[j])
            NewNewYScan.append(NewYScan[j])
            NewNewZScan.append(NewZScan[j])
            NewNewRScan.append(rgrid[i])

    ScanLocations = {'X':[round(num,2) for num in NewNewXScan],
                     'Y':[round(num,2) for num in NewNewYScan],
                     'Z':[round(num,2) for num in NewNewZScan],
                     'R':[round(num,2) for num in NewNewRScan]}
    
    
    
    print("{} images".format(len(NewNewXScan)))
    
    
    return(ScanLocations)

def InterlaceZ(ScanLocations, ZCoord):
    #Takes a ScanLocations Dictionary (expected 2 dimensional, unchanging Z)
    #and interlaces ZCoord evenly inside it. (Z priority is better for stacking)
    #Advanced: Z Height depends on X/Y location as opposed to comprehensive
    XLocations = ScanLocations['X']
    YLocations = ScanLocations['Y']
    ZLocations = ScanLocations['Z']
    RLocations = ScanLocations['R']
    

    NewX = []
    NewY = []
    NewZ = []
    NewR = []
    flag = -1     
    for i in range(len(XLocations)):
        flag = flag * -1
        for j in ZCoord[::flag]:
            NewX.append(XLocations[i]) #duplicates
            NewY.append(YLocations[i])
            NewR.append(RLocations[i])
            NewZ.append(j)

            
    ScanLocations['X'] = NewX
    ScanLocations['Y'] = NewY
    ScanLocations['Z'] = NewZ
    ScanLocations['R'] = NewR

    return ScanLocations


def RotateScan(ScanLocations, degrees = 30):
    #function to rotate a 3D array around a specified axis (currently Y). Ideally, around arb point in space.  
    #X Location minus offset becomes new hypotenuse after rotating.
    #(sin(degrees) * X) + Z gives new Z .
    #cos(degrees)* X gives new X. Right? Y should be unchanged.
    #make this Axis-able
    XLocations,ZLocations = ScanLocations['X'],ScanLocations['Z']
    sinof = sin(np.deg2rad(degrees))
    cosof = cos(np.deg2rad(degrees))
    XOffset = min(XLocations) #not fair to assume it is zeroth position

    ZLocations = [round((x-XOffset)*sinof + z,2) for x, z in zip(XLocations, ZLocations)]
    XLocations = [round(((i - XOffset) * cosof)+XOffset,2) for i in XLocations]

    ScanLocations['X'] = XLocations
    ScanLocations['Z'] = ZLocations
    return (ScanLocations)

#all assumes cv2 here
def StartCamera(camera = 1, Width = 640, Height = 480):
    #assumes having a built-in webcam, too. change to 0 otherwise
    #most fundamental thing I guess. Change Width and Height here?

    cap = cv2.VideoCapture(camera)
    cap.set(3,Width)
    cap.set(4,Height)
    
    ret,junkframe = cap.read() #junk because must grab first frame THEN set LED controls
    
    return cap #and pass to TakePicture

def TakePicture(cap):
    
    ret,frame = cap.read() 

    return frame

def SavePicture(name,frame): #name includes locations and extension
    folder = os.path.dirname(name)

    if not os.path.exists(folder):
        os.makedirs(folder)
        
    cv2.imwrite(name,frame)
    
def CloseCamera(cap):

    cap.release()

def CalculateBlur(frame): 
    blur = cv2.Laplacian(frame, cv2.CV_64F).var()
    return blur

def ShowPicture(frame):
    cv2.imshow('X:' + str(GlobalX) + ' Y:' + str(GlobalY) + ' Z:' + str(GlobalZ),frame)

'''
def MoveFromClick(event,x,y,flags,param):
    #Moves to put clicked on area in center
    #right now more annoying than helpful
    
    if param:
        PixelsPerUnit = param(0)
        
    else:
        PixelsPerUnit = 50 #number of pixels per mill
    
    if event == cv2.EVENT_FLAG_LBUTTON:
        print('movefromclickactivated')    
        KeepBugInCenter(x,y,PixelsPerUnit=PixelsPerUnit)

'''     
def ShowCamera(cap=False,camera_choice=1,TrackTheBug=False,
               SavePath = "capture\\",
               StackPath = "capture\\stacked\\",
               Width=640,Height=480):
    #best to call this with threading so you can use other gui controls 
    #though really they should be integrated together.
    #or some other third smaller solution
    
    
    if cap == False: #else pass in an explicit cap
        cap = cv2.VideoCapture(camera_choice) #default 1 if on laptop with webcam

    #tracking variables
    fps = None
    BoxTimeout = 0
    initBB = None
    prev_img_name = 'im an image'
    DefaultName = """space to snap, h to home, d autostacks, f autofocuses,
    j,k,l,i,-,+, to move, t toggles track and c which color,
    s draw bounding box, b resize video, v starts and stops video"""
    cv2.namedWindow(DefaultName,cv2.WINDOW_NORMAL) #resize
    cv2.resizeWindow(DefaultName, Width,Height) #small better for preview
    
    
    #ColorLower, ColorUpper = (64,255,255) , (29,86,6) #green
    
    ColorLowers = [(64,255,255),(10,100,20)] #note lower"s". cycle through to get color
    ColorUppers = [(29,86,6),(20,255,200)] 
    ColorsIndex = 0 #count and cycle through
    NumberOfColors = len(ColorLowers)
    
    ColorLower, ColorUpper = ColorLowers[ColorsIndex],ColorUppers[ColorsIndex]

    if not os.path.exists(StackPath): #Show stacked pics taken from out of main loop
        os.makedirs(StackPath)
    StackedPics = [os.path.join(StackPath, fn) for fn in next(os.walk(StackPath))[2] if ".jpg" in fn]    
    SCount = 0 #Check only every few seconds to save resources 

    while True:
        ret, frame = cap.read()
        np.resize(frame,(Width,Height,3)) #just force it    
        if not ret:
            break
        
        SCount +=1 #this next block is for loading any stacked files
        if SCount % 50:
            TempStacked = [os.path.join(StackPath, fn) for fn in next(os.walk(StackPath))[2] if ".jpg" in fn]
            NewPics = list(list(set(StackedPics)-set(TempStacked)) + list(set(TempStacked)-set(StackedPics)))
            if NewPics:
                StackedPics = TempStacked
                for pic in NewPics:
                    name = os.path.basename(pic)
                    loadpic = cv2.imread(pic)
                    cv2.imshow(name,loadpic)
                    
            SCount = 1 #Avoid overflow. Stack block over

    
        #cv2.setMouseCallback(DefaultName,MoveFromClick)#possibly bad looped
        k = cv2.waitKey(30)
        
        if k%256 == 32: #this and video capture now before frame modification
            # SPACE pressed take picture
            img_name = MakeNameFromPositions(GlobalX,GlobalY,GlobalZ,GlobalR,'.jpg') 
            if img_name == prev_img_name:
                counter+=1
                img_name = str(counter) + img_name
            #this turned out to be weirdly hard to make it add number only if
            #picture at location has been taken before.
            #and this will still overwrite if you leave and come back
            
            elif img_name != prev_img_name: 
                counter = 0            
            print(SavePath)
            print(img_name)
            cv2.imwrite(SavePath + img_name, frame)
            print("{} written!".format(img_name))
            prev_img_name = img_name.lstrip(string.digits) 

        
        if k%256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break

        if k%256 == ord('j'): #can't figure out arrow keys. ijkl for movement
            AllGoTo(GlobalX-LittleXY,GlobalY,GlobalZ,update=False, speed=XSpeed) #thread problems. dont update position
        if k%256 == ord('l'):
            AllGoTo(GlobalX+LittleXY,GlobalY,GlobalZ,update=False, speed=XSpeed)
        if k%256 == ord('i'):
            AllGoTo(GlobalX,GlobalY+LittleXY,GlobalZ,update=False, speed=YSpeed)
        if k%256 == ord('k'):
            AllGoTo(GlobalX,GlobalY-LittleXY,GlobalZ,update=False, speed=YSpeed)
        if k%256 == ord('-'):
            AllGoTo(GlobalX,GlobalY,GlobalZ-LittleZ,update=False, speed=ZSpeed)
        if k%256 == ord('='): #- and + but + is shifted
            AllGoTo(GlobalX,GlobalY,GlobalZ+LittleZ,update=False, speed=ZSpeed)
        if k%256 == ord('f'): #AutoFocus
            y = threading.Thread(target=FindZFocus) #update image during
            y.start()
        if k%256 == ord('d'): #super basic autostack for testing
            StackThread = threading.Thread(target=DefaultStack)
            StackThread.start() #update picture during
            
        if k%256 == ord('h'):
            Home()
            
        if k%256 == ord('c'): #toggle color choice
            ColorsIndex +=1
            if ColorsIndex == NumberOfColors:
                ColorsIndex = 0 
            ColorLower, ColorUpper = ColorLowers[ColorsIndex],ColorUppers[ColorsIndex] #brown
            print('colors track toggled. lower hsv range: {} upper {}'.format(ColorLower,ColorUpper))
        if k%256 == ord('v'): #toggle video
            try:
                out.release() #first close if not start
                print('Ending video capture')
                del out
            except NameError: 
                #VideoName = time.asctime().replace(" ","") + '.avi'
                VideoName = SavePath + "Vid starting at " + MakeNameFromPositions(GlobalX,GlobalY,GlobalZ,GlobalR,'.mp4')
                out = cv2.VideoWriter(VideoName,cv2.VideoWriter_fourcc('H','2','6','4'), 20, shape(frame)[1::-1])
                print('Starting video capture')
        
        try:
            out.write(frame)
        except NameError:
            pass
        
        if k%256 == ord('t'): #Toggle bug tracking
            TrackTheBug = not TrackTheBug #swap 
            print("Track the bug: {}".format(TrackTheBug))
        if k%256 == ord('b'): #resize window
            if Width == 640:
                Width, Height = 1280,960
            elif Width == 1280:
                Width, Height = 640,480
            
            print('width and height is now {},{}'.format(Width,Height))

            cv2.resizeWindow(DefaultName,Width,Height)
        
        if k%256 == ord("s"):
            #initiate track by bounded box
            print("Select slow-moving ROI with cursor to track then hit enter") 
            tracker = cv2.TrackerKCF_create() 
            # press ENTER or SPACE after selecting the ROI)
            initBB = cv2.selectROI(DefaultName, frame, fromCenter=False,
            showCrosshair=True)

            # start OpenCV object tracker using the supplied bounding box
            # coordinates, then start the FPS throughput estimator as well
            tracker.init(frame, initBB)
            fps = FPS().start()
                
        if initBB is not None:
        #call bounding boxer
            frame, tracker, fps, success, box = ObjectTracker.UpdateBox(frame,tracker,fps)
            if not success:
                BoxTimeout +=1
                if BoxTimeout > 50: #max attempts, reinitialize everything
                    initBB = None 
                    fps = None          
            
            else:
                BoxTimeout = 0
                (x, y, w, h) = [int(v) for v in box] #x,y 0,0 top left
                CenterX = (x+(w/2))
                CenterY = (y+(h/2))
                #print(CenterX,CenterY)
                KeepBugInCenter(CenterX,CenterY,Width=Width,Height=Height)
                #print('found object hooooray')
                #call motion mover thing
        
        
        if TrackTheBug: #trackthebug by color needs consolidation with box method

            TrackerOutput = ObjectTracker.BallTracker(frame,
                    ColorLower = ColorLower,
                    ColorUpper = ColorUpper,
                    Width=Width, Height=Height) #False if nothing detected 

            if TrackerOutput:

                frame = TrackerOutput[0]
                x = TrackerOutput[1] #centroid
                y = TrackerOutput[2]

                KeepBugInCenter(x,y,Width=Width,Height=Height)

            #green # ColorLower = (29,86,6), ColorUpper = (64, 255, 255)
            #brown (10, 100, 20),(20, 255, 200)
            #black (0, 0, 0), (360, 100, 20) #bad
            #experimental (124,40,0) , (168,103,255)

        cv2.imshow(DefaultName, frame)

    cv2.destroyAllWindows()



    
def KeepBugInCenter(ObjectX,ObjectY,PixelsPerUnit = 200, Width = 640,
                    Height=480, thresh = 30, speed = 2000):
    #we want to make X and Y be center of the frame --- width and height/2
    #calls motion accordingly...
    #this should be PID loop ideally 
 
    GoalX = Width/2
    GoalY = Height/2    
    
    XPixels = (GoalX-ObjectX)
    YPixels = (GoalY-ObjectY)

    if abs(XPixels) < thresh:
        XPixels = 0
    if abs(YPixels) < thresh:
        YPixels = 0

    XMovement = round(XPixels/PixelsPerUnit,1)
    YMovement = round(YPixels/PixelsPerUnit,1)

    XFinal = GlobalX - XMovement
    YFinal = GlobalY + YMovement

    if YMovement or XMovement:
        
        AllGoTo(XFinal,YFinal,GlobalZ,update=False, speed=speed) #not waiting for update yet

    return XFinal,YFinal

def DefaultStack(pics = 20, stepsize = 0.1,
                 dims = (32,32), center = 'default'):
    
    if center == 'default':
        center = GlobalZ
    low = round(center - (pics//2 * stepsize),1)
    high = round(center + (pics//2 * stepsize),1)
    ZCoord = GenerateZ(low if low >=0 else 0 ,high, stepsize)

    stacked, allframes, TrueZ3D = ZStackKinda(ZCoord,subdiv_dims = dims) #the juicy part
    
    DepthMap = NormalizeZMap(TrueZ3D)
    
    name = "Capture\\Stacked\\{} to {} at X {}, Y {}.jpg".format(low,high,GlobalX,GlobalY)
    DepthName = "Capture\\Stacked\\depth {} to {} at X {}, Y {}.jpg".format(low,high,GlobalX,GlobalY)

    SavePicture(name,stacked)
    
    SavePicture(DepthName,DepthMap)

    #ShowPicture(stacked) #if function is seperate thread, pic won't show
    #solution is to look for new saved files in main thread and load them 

def ZStackKinda(ZCoord, subdiv_dims = (4,4),
                camera='default', X=-1, Y=-1):
    """takes pictures at ZCoord and then can call max_pool_subdivided_images
    with desired chunking amount and finally returns fakestacked image"""

    if X==-1:
        X = GlobalX
    if Y== -1:
        Y = GlobalY

    if camera == 'default':
        camera = cap #still don't know the best way to say this
    frames = []

    if GlobalZ == ZCoord[-1]: #flip if starting at top
        ZCoord.reverse()
    
    for Z in ZCoord: #ZCoord list of Z values to go to
        frame = MoveConfirmSnap(GlobalX,GlobalY,Z,cap)
        frames.append(frame)
    
    Stacked, IndexMap = max_pool_subdivided_images_3d(frames, subdiv_dims) #actual stacker (thanks yujie!)

    TrueZ3D = GetTrueZ3D(IndexMap, ZCoord) #convert map into 3D 
    
    
    return Stacked,frames, TrueZ3D

def GetTrueZ3D(IndexMap, ZCoord):
    #uses dictionary lookup to convert a 2D "image" with indexes
    #into a 2D image with each value corresponding to true Z height
    #the idea is that after stitching these images together
    #lowest Z height will be set to zero then all expanded to 255 grayshade
    #it is much more efficient to create the indexer just once...
    #...but with the way yujie's code is, the order might change each time.
    #credit to Andy Hayden and Abhijit

    d = {v: k for v, k in enumerate(ZCoord)}
        
    indexer = np.array([d.get(i, -1) for i in range(IndexMap.min(), IndexMap.max() + 1)])  
    
    TrueZ3D = indexer[(IndexMap - IndexMap.min())]

    return TrueZ3D

def NormalizeZMap(ZMap, lowest_Z = 'default', highest_Z = 'default'):
    #takes matrix of true 3D locations and subtracts all by lowest value
    #and converts to graymap of up to 255
    
    if lowest_Z == 'default' and highest_Z == 'default':
        NormalMap = ((ZMap - ZMap.min()) * 255/(ZMap.max() - ZMap.min()))
    else:
        NormalMap = ((ZMap - lowest_Z) * 255 / (highest_Z - lowest_Z))
        
    return NormalMap

def GenerateZ(LowZ,HighZ,Precision):
    #I used this more than once so into a function it goes
    
    ZHeights = []
    
    while LowZ <= HighZ:
        ZHeights.append(LowZ)
        LowZ = round(LowZ+Precision,2)

    return(ZHeights)
    
def CalculateStepSize(PixelsPerStep=370,
                      XOverlap = 40, YOverlap = 40,
                      XWidth = 640, YHeight = 480):
    #returns correct amount to move X and Y for desired amount of overlap and pixel size.
    #Step in PixelsPerStep can refer to literal steps or just mm. mm easier
    #overlap in percent
    
    XSteps = round(XWidth/PixelsPerStep - (((XOverlap/100)*XWidth)/PixelsPerStep),3)
    YSteps = round(YHeight/PixelsPerStep - (((YOverlap/100)*YHeight)/PixelsPerStep),3)

    
    return XSteps,YSteps

def DivideCircle(XCenter, YCenter, Radius, Divisions, ScanLocations=None):
    #"circle within circle" packing problem
    #internal circles have constant radius and points those circle centers
    consts = []
    locations = []
    
    for i in range(Divisions):
        consts.append(1)
        
    circles = circlify.circlify(consts)
    for circle in circles:
        x, y, r = circle.x, circle.y, circle.r
        x = round((XCenter - (x * Radius)),1)
        y = round((YCenter - (y * Radius)),1)

        if ScanLocations: #force points to be closest to original scan points
            xindex = np.argmin(np.abs(np.array(ScanLocations['X'])-x))
            x = ScanLocations['X'][xindex]
            yindex = np.argmin(np.abs(np.array(ScanLocations['Y'])-y))
            y = ScanLocations['Y'][yindex]
            
        locations.append((x,y))

    return locations



def CallibratePlate(CoordinatePoints = [(25,60),(90,125),(105,30),(62,75)],
                    LowPoint = 3,
                    HighPoint = 5,
                    Precision = 0.1,
                    ShowImage = False):

    '''a 3 or whatever point leveling system that just reports the point of
    max focus at coordinate points of interest (usually 3 thumbscrews).
    Only approximately accurate to within a camera's depth of field'''

    #extra corner points (10,10),(120,10),(120,140),(10,140)
    
    ZHeights=GenerateZ(LowPoint,HighPoint,Precision)
 
    print('ZHeights to check are {}'.format(ZHeights))
    
    Focuses = []
    
    for count, point  in enumerate(CoordinatePoints):
        XPoint = point[0]
        YPoint = point[1]
        
        XGoTo(XPoint)
        YGoTo(YPoint)
        time.sleep(2)
        WaitForConfirmMovements(XPoint,YPoint,GlobalX) #adds margin on top of sleep

        Focus, FocusImage = FindZFocus(ZHeights,GoToFocus=False) 
        Focuses.append(Focus)
        
        print('Focus for Point {} (X:{},Y{}) at Z Height = {}'.format(
            count,XPoint,YPoint,Focus))
        
        if ShowImage:
              ShowPicture(FocusImage)
    print('{} point check done okay'.format(count+1))
    
    return(Focuses)
    

def FindZFocus(ZCoord='broad', Comprehensive = False,
               GoToFocus = True, camera='default',
               ScannedBroad = False):
    
    if camera == 'default':
        camera = cap #still don't know the best way to say this

    if ZCoord == 'broad':
        ZCoord = GenerateZ((GlobalZ-10 if GlobalZ-10 >= 0 else 0),
                           GlobalZ + 10,
                           0.5)
        ScannedBroad = True #scan again with narrower range
        
        if GlobalZ >=0.5:
            AllGoTo(GlobalX,GlobalY, GlobalZ - 0.5,update=False) #if you're already focused this is faster

    elif ZCoord == 'narrow':
        ZCoord = GenerateZ((GlobalZ-0.6 if GlobalZ-0.6 >= 0 else 0),
                           GlobalZ + 0.6,
                           0.1)
        if GlobalZ >= 0.3:
            AllGoTo(GlobalX,GlobalY, GlobalZ - 0.3,update=False)
        
        
    frames = []
    blurs = []
    
    #index of coord closest to current location for speed optimization
    index = np.argmin(np.abs(np.array(ZCoord)-GlobalZ))
    initial = ZCoord[index]
        
    counter = 0
    ZTraveled = []
    for i, Z in enumerate(ZCoord):

        if index + i < len(ZCoord):
            GoingUp = True
            RealIndex = index + i
            
        else:
            GoingUp = False
            counter +=1
            RealIndex = index - counter

        Z = ZCoord[RealIndex]
        ZTraveled.append(Z)
        AllGoTo(GlobalX,GlobalY,Z,update=False)
        #print ("i: {} RealIndex: {} counter: {}".format(i,RealIndex, counter))
        while True:
            positions = GetPositions()
            
            if positions and positions['Z'] == Z: #我们到了
                break
            else:
                time.sleep(0.05)
        time.sleep(0.05) #vibration control

        frame = TakePicture(camera)
        blur = CalculateBlur(frame)

        if GoingUp:
            frames.append(frame)
            blurs.append(blur)
            if Comprehensive == False and i >= 2: #arrest search if overshoot focus point    
                if (blurs[i-2] > 50) and (blurs[i] < blurs [i-1]) and (blurs[i-1] < blurs[i-2]):
                    break
                #elif (blurs[i] < 50) and (blurs[i] < blurs[i-1]) and (blurs[i-1] < blurs[i-2]): #going wrong way
                #    break
        
        else:
            frames.insert(0,frame)
            blurs.insert(0,blur)
            TrueMax = blurs.index(max(blurs)) #(more spaghetti) THIS WAS ONE LINE DOWN UNDER IF COMPREHENSIVE
            if Comprehensive == False and i > 2: #arrest search if overshoot focus point    
                
                #print('TrueMax is {}'.format(TrueMax))
                if TrueMax > 2: #going down. don't worry about absolutes
                    if (blurs[TrueMax] > 50) and (blurs[TrueMax] > blurs[TrueMax - 1]) and (blurs[TrueMax-1] > blurs[TrueMax-2]):
                        break
                    #elif (blurs[TrueMax] < 50) and (blurs[TrueMax] > blurs[TrueMax -1]) and (blurs[TrueMax-1] > blurs[TrueMax-2]):
                    #      break
        

            
    if GoingUp:
        ZFocus = ZTraveled[blurs.index(max(blurs))]
        BestFrame = frames[blurs.index(max(blurs))]
    else:
        ZFocus = ZCoord[TrueMax + RealIndex]
        BestFrame = frames[blurs.index(max(blurs))]
        
    if GoToFocus:
        AllGoTo(GlobalX,GlobalY,ZFocus,update=False)
    
    if ScannedBroad: #slightly more efficient "where am I" scan
        ZFocus, BestFrame = FindZFocus(ZCoord='narrow') #recursive needs to return 
        
    
    return (ZFocus,BestFrame)



def ControlDino(setting = "FLCLevel 6"):
    """uses dinolite windows batch file to control settings on EDGE plus model.
    FLCLevel: 1-6 brightness, if  0 convert to LED off
    FLCSwitch: control quadrants, value is 1111, 1010...
    AE on
    AE off (locks current exposure value)
    EV: sets exposure values 16-220, strange behavior
    """
    

    if "FLCLevel" in setting:
        subprocess.call('DN_DS_Ctrl.exe LED ON') #can't change FLC if it's already off
        if '0' in setting:
            setting = "LED off"
                            

    subprocess.call('DN_DS_Ctrl.exe ' + setting)    
        



def MakeFolderFromPositions(X,Y,Z,R,ParentFolder,FileType='.jpg'):
    ZStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(Z))))).zfill(5)
    RStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(R))))).zfill(5)
    folder = ParentFolder + "/Z" + ZStr + "R" + RStr #will make new folder on each change in Z or R
    if not os.path.exists(folder): #should hopefully continue saving in the same folder after restart
        os.makedirs(folder)
     
    return folder


               
def GridScan(ScanConditions): # DefaultScan dictionary available for modifying
    
    if not ScanConditions['Restarted Scan']:
        save_location = filedialog.askdirectory()
        start_time = time.time()
        
    else:
        save_location = ScanConditions['Save Location']
        start_time = ScanConditions['Start Time']

    cap = ScanConditions['Camera']
    Width = ScanConditions['Width']
    Height = ScanConditions['Height']
    FileType = ScanConditions['FileType']
    Failures = ScanConditions['Failures']
    ScanRates = ScanConditions['ScanRates'] #how fast takes pictures periodically
    AutoFocus = ScanConditions['AutoFocus'] #true or false
    PotentialZ = ScanConditions['Z Heights']
    PointInScan = ScanConditions['PointInScan']
    ScanLocations = ScanConditions['ScanLocations']
    CameraSettings = ScanConditions['CameraSettings']
    FocusDictionary = ScanConditions['FocusDictionary']
    VibrationControl = ScanConditions['VibrationControl']
    
    XCoord = ScanLocations['X']
    YCoord = ScanLocations['Y']
    ZCoord = ScanLocations['Z']
    RCoord = ScanLocations['R']

    if not cap: # already passed a camera object in
        
        cap = StartCamera(Width=Width,Height=Height)
    
    #DO ANY ADJUSTING OF CAMERA CONDITIONS HERE AFTER STARTING CAMERA
    #Note: manual exposure settings are not absolute: you MUST move the camera
    #before starting the scan to the same place you tested exposure setting
    
    if CameraSettings:
        for setting in CameraSettings[:-1]:
            ControlDino(setting)
            time.sleep(2)
        ControlDino(setting) #why wait 2 seconds between commands if you don't have to
            

    for i in range(PointInScan,len(XCoord)): #pointinscan 0 default, invoked in restart 

        X = XCoord[i]
        Y = YCoord[i]
        Z = ZCoord[i]
        R = RCoord[i]

        #go to locations
 
        XGoTo(X)
        YGoTo(Y)
        if not AutoFocus: #I don't like this :(
            ZGoTo(Z)
        RGoTo(R)

        #needs to have a mode that prioritizes Z movements for stacking
        #total autofocus rework to return sorted Zs in order instead of just one
        #and then you can pick X number to keep etc.

        
        #gcode confirmation movement block
        #hacky restart fix goes here
        SuccessfulWait = WaitForConfirmMovements(X,Y,(Z if not AutoFocus else GlobalZ))

        if not SuccessfulWait:
            global LadyBug
            LadyBug = RestartSerial()
            Home()
            time.sleep(4)
            XGoTo(X)
            YGoTo(Y)
            if not AutoFocus: #I don't like this :(
                ZGoTo(Z)
            RGoTo(R)
            time.sleep(3)
            
            Failures.append(i) #point in scan
            print('restarted at point {} grr'.format(i))
            
            SuccessfulWait = WaitForConfirmMovements(X,Y,(Z if not AutoFocus else GlobalZ),attempts=100)
            #twice in a row would suck            

        #Picture taking block
        
        for i in range(3): #catches some failed pictures
                                
            try:
                if not AutoFocus:
                    time.sleep(VibrationControl) 
                    frame = TakePicture(cap)
                else:
                    Z,frame = FindZFocus(PotentialZ,False,cap) #should rework to allow walking

                #picture and focus info saving block
                #5 digits total with 2 decimals always and leading and trailing 0s if necessary
                folder = MakeFolderFromPositions(X,Y,Z,R,save_location,FileType)
                name  = MakeNameFromPositions(X,Y,Z,R,FileType)

                SavePicThread = threading.Thread(target=SavePicture,args=((folder + "/" + name),frame))
                FocusThread = threading.Thread(target=UpdateFocusDict, args = (FocusDictionary,(X,Y,Z,R),frame))
                FocusThread.start() # hopefully allows usefulness during idle sleep times
                SavePicThread.start()                            


               
                         
            except Exception: #Filesaving errors go here
                print('partial (not total) failure for picture {}'.format(name))
                

            else: #successful pic
                PointInScan +=1
                if PointInScan % 100 == 0: #every 100 pics  
                    ScanRates.append(time.time())
                    
                    if len(ScanRates)>1:
                        tttt = int(ScanRates[-1]-ScanRates[-2]) #time taken this time
                        print("{} of {} pics took {} seconds".format(PointInScan,len(XCoord),tttt))

                break                    

        else:
            print('total failure for picture {}'.format([X,Y,Z,R]))
            Failures.append([X,Y,Z,R])
            
    #end of scan, retaking failed pictures goes here
    print ('Failures: {}'.format(Failures)) #ints for serial and locations for pictures
    print ('scan completed successfully! Time taken: {}'.format(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))))
    print('Saving focus dictionary...')

    try:
        
        FocusFile = open(save_location + '\\FocusDictionary.pkl', 'wb')
        pickle.dump(FocusDictionary, FocusFile)
        FocusFile.close()
  
    except Exception: 
        print("Unable to save focus dictionary")    
    
    #go back to beginning simplifies testing, but could also set a park position
    XGoTo(XCoord[0])
    YGoTo(YCoord[0])
    if not AutoFocus: #Crash number 3
        ZGoTo(ZCoord[0])
    RGoTo(RCoord[0])

    #CloseCamera(cap) #uncomment if things are strange here

def XGoTo(XDest,speed = 10000):
    
    global GlobalX


    X,Y,Z,E = XDest, GlobalY, GlobalZ, GlobalR        
    GlobalX = round(X,2) #round BEFORE sending
    GCode = GenerateCode(GlobalX,Y,Z,E,speed)
    SendGCode(GCode)
    
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))
    
def YGoTo(YDest,speed = 10000):
    
    global GlobalY


    X,Y,Z,E = GlobalX, YDest, GlobalZ, GlobalR        
    GlobalY = round(Y,2)
    GCode = GenerateCode(X,GlobalY,Z,E,speed)
    SendGCode(GCode)
    
    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))

def ZGoTo(ZDest,speed = 1000):
    
    global GlobalZ


    X,Y,Z,E = GlobalX, GlobalY, ZDest, GlobalR        
    GlobalZ = round(Z,2)
    GCode = GenerateCode(X,Y,GlobalZ,E,speed)
    SendGCode(GCode)
    
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))    

def AllGoTo(XDest=-1,YDest=-1,ZDest=-1,RDest=-1,speed = 3000,update=False,
            ): 
    #set update to True or False to update or not Tkinter (can mess up threads)    
    global GlobalX,GlobalY,GlobalZ,GlobalR


    
    if XDest < 0 or XDest > XMax: #Can't declare global at runtime...
        XDest = GlobalX
    if YDest < 0 or YDest > YMax:
        YDest = GlobalY #can't set = 0 as false because 0 is valid location...
    if ZDest < 0 or ZDest > ZMax:
        ZDest = GlobalZ #can do 'default' but bah.
    if RDest < 0:
        RDest = GlobalR
        
    X,Y,Z,E = XDest,YDest,ZDest,RDest        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalX,GlobalY,GlobalZ,GlobalE = round(X,2),round(Y,2),round(Z,2),round(E,2)

    if update:

        #not updating tkinter allows function to be called from threaded process
        
        XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))    
        YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))
        ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))

    

    
def RGoTo(RDest,speed = 2000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalR


    X,Y,Z,E = GlobalX, GlobalY, GlobalZ, RDest        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalR = round(E,2)
    
    #RPosition.configure(text="R: "+str(GlobalR) + "/" + str(RMax))


def XGet(event):
    '''records enter press from text box (XEntry) and calls "go to specified location function'''
    try:
        XDest = float(event.widget.get())
        XGoTo(XDest)
    except ValueError: #hey dumbo enter a number
        print ("Please enter a real number")

def YGet(event):
    '''records enter press from text box (YEntry) and calls "go to specified location function'''
    try:
        YDest = float(event.widget.get())
        YGoTo(YDest)
    except ValueError: #hey dumbo enter an number
        print ("Please enter a real number")



def MoveT(direction,numsteps,delay,ZXCorrect=False):
    #tilt motor. Should probably have a way to initialize and prevent going over range
    GPIO.output(TDIR,direction)
    global GlobalT

    CorrectZAfter = False

    if ZXCorrect == True: #dynamically correct X and Z position. Maybe should be in TGoTo instead
        initial = GlobalT
        if direction == TFORWARD: #don't judge me repeating this twice ok
            final = GlobalT + numsteps
        else:
            final = GlobalT - numsteps

        Corrected_X, Corrected_Z = TiltCorrection(initial,final)

        XGoTo(Corrected_X)

        if Corrected_Z <=GlobalZ: #if Z goes down, move Z first then tilt.
            ZGoTo(Corrected_Z)
        else: CorrectZAfter = True #correct Z after tilt if moving up

        #actually move tilt now

    for i in range(numsteps):
        GPIO.output(TSTEP,GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(TSTEP,GPIO.LOW)

    if CorrectZAfter:
        ZGoTo(Corrected_Z)
    if direction == TFORWARD:
        GlobalT += numsteps
    else:
        GlobalT -= numsteps
    #more stuff should go here at some point


def ZGet(event):
    '''records enter press from text box (ZEntry) and calls "go to specified location function'''
    try:
        ZDest = float(event.widget.get())
        ZGoTo(ZDest)
    except ValueError: #hey dumbo enter an number
        print ("Please enter a real number")




def HomeX():
    global GlobalX

    SendGCode('M203 X30') #this alone changes things so much
    
    SendGCode('G28 X')

    SendGCode('M203 X80') #and make it an okay speed again


    GlobalX = 0
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))

def HomeY():
    global GlobalY
    SendGCode('M203 Y20') 
    
    SendGCode('G28 Y')

    SendGCode('M203 Y80')

    GlobalY = 0
    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))

def HomeZ():
    global GlobalZ

    SendGCode('G28 Z')

    GlobalZ = 0
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))
    
def Home():
    #probably could consume the other three
    #SLOW DOWN FIRST 1/10/21
    SendGCode('M203 Y20 X30') #this alone changes things so much
    
    SendGCode('G28')

    SendGCode('M203 Y80 X80') #and make it an okay speed again
    
    GlobalZ = 0
    #ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))
    GlobalY = 0
    #YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))
    GlobalX = 0
    #XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))

def InitiatePCBTools():
    #called by gui and deals with information from pickandplace module
    PCBLocation = filedialog.askopenfilename ()

    designators, columns, rows = GetLocations(PCBLocation)

    DesignatorKeys = list(designators)
    ListOfCoordinateTuples = [] #list order becomes important here
    for key in DesignatorKeys:
        ListOfCoordinateTuples.append(designators[key])
        
    
    while True:
        print('board components are {}'.format(DesignatorKeys))
        
        choice = input("enter component name to goto and snap picture or 'all' to do all. Control C to exit")
        
        try:
            if choice.lower() == 'all':
                print('this may take a sec. traveling salesman problem grr')
                PathChoice, TotalDistance = ShortestPath(ListOfCoordinateTuples)
                print('got it! optimum distance = {} mm '.format(TotalDistance))
                for node in PathChoice:
                  component = DesignatorKeys[node]
                  location = ListOfCoordinateTuples[node]
                  AllGoTo(location[0],location[1]) #NOTE. breaks genericness of any size coordinates
                  WaitForConfirmMovements(location[0],location[1],GlobalZ)
                  time.sleep(0.1) #for vibration, could be longer for human inpu
                  frame = TakePicture(cap) #assumes you already opened cam preview
                  SavePicture(component + ".jpg",frame)

                  
            else: 
                location = designators[choice]
                AllGoTo(location[0],location[1]) #NOTE. breaks genericness of any size coordinates 
                
                WaitForConfirmMovements(location[0],location[1],GlobalZ)
                time.sleep(0.1) #for vibration, could be longer for human input
                frame = TakePicture(cap) #assumes you already opened cam preview
                SavePicture(choice + ".jpg",frame)
        except KeyError:
            print('Sorry, invalid choice in key or programmer')
            continue
        except KeyboardInterrupt:
            print('Thanks for flying with pcb tools v0.0')
            return designators, columns, rows, PathChoice
    
    
    return designators, columns, rows, PathChoice
    
def StartAutoCoin():
    #for tkinter
    AutoCoin(cap)

def ShortestPath(ListOfCoordinateTuples):
    #just calls tsp (traveling salesman problem) module
    #could be replaced with something homebrewed for package reduction
    #(needs pandas)
    #Works with arbitrary dimensions within each tuple -- XY but also XYZ etc.

    TotalDistance, PathChoice = tsp.tsp(ListOfCoordinateTuples)

    return PathChoice, TotalDistance
    

def MoveXLeftBig(): #dir distance delay
    (XGoTo(GlobalX-BigXY),print('X decreased by',BigXY)) if (GlobalX-BigXY)>XMin else (XGoTo(XMin),print('X at Min ({})'.format(XMin)))
    
def MoveXLeftSmall():
    (XGoTo(GlobalX-LittleXY),print('X decreased by',LittleXY)) if (GlobalX-LittleXY)>XMin else (XGoTo(XMin),print('X at Min ({})'.format(XMin)))

def MoveXRightBig():
    (XGoTo(GlobalX+BigXY),print('X increased by',BigXY)) if (GlobalX+BigXY) < XMax else (XGoTo(XMax),print('X at Max ({})'.format(XMax)))
    

def MoveXRightSmall():
    (XGoTo(GlobalX+LittleXY),print('X increased by',LittleXY)) if (GlobalX+LittleXY) < XMax else (XGoTo(XMax),print('X at Max ({})'.format(XMax)))
    

def MoveYForwardBig():
    (YGoTo(GlobalY+BigXY),print('Y increased by',BigXY)) if (GlobalY+BigXY)<YMax else (YGoTo(YMax),print('Y at Max ({})'.format(YMax)))
    
def MoveYForwardSmall():
    (YGoTo(GlobalY+LittleXY),print('Y increased by',LittleXY)) if (GlobalY+LittleXY) < YMax else (YGoTo(YMax),print('Y at Max ({})'.format(YMax)))
    
def MoveYBackBig():
    (YGoTo(GlobalY-BigXY),print('Y decreased by',BigXY)) if (GlobalY-BigXY)>YMin else (YGoTo(YMin),print('Y at Min ({})'.format(YMin)))
    
def MoveYBackSmall():
    (YGoTo(GlobalY-LittleXY),print('Y decreased by',LittleXY)) if (GlobalY-LittleXY)>YMin else (YGoTo(YMin),print('Y at Min ({})'.format(YMin)))



def MoveZDownBig(): #dir dis delay
    (ZGoTo(GlobalZ-BigZ),print('Z decreased by',BigZ)) if (GlobalZ-BigZ)>ZMin else (ZGoTo(ZMin),print('Z at Min ({})'.format(ZMin)))

def MoveZDownSmall():
    (ZGoTo(GlobalZ-LittleZ),print('Z decreased by',LittleZ)) if (GlobalZ-LittleZ)>ZMin else (ZGoTo(ZMin),print('Z at Min ({})'.format(ZMin)))
def MoveZUpBig():
    (ZGoTo(GlobalZ+BigZ),print('Z increased by',BigZ)) if (GlobalZ+BigZ)<ZMax else (ZGoTo(ZMax),print('Z at Max ({})'.format(ZMax)))

def MoveZUpSmall():
    (ZGoTo(GlobalZ+LittleZ),print('Z increased by',LittleZ)) if (GlobalZ+LittleZ)<ZMax else (ZGoTo(ZMax),print('Z at Max ({})'.format(ZMax)))

def MoveRCWSmall():
    #cw when staring down at spindle or object
    MoveR(RFORWARD, 40, SLOW) #increased to 40 for finder Beefy
    print("You rotated something clockwise a bit!")

def MoveRCCWSmall(): #counterclockwise
    MoveR(RBACKWARD, 40, SLOW)
    print("You rotated something counterclockwise a bit!")

def MoveTUpSmall():
    #tilt 5th axis added jan 28 2020
    MoveT(TFORWARD, 8, SLOW)
    print("You tilted something up a bit!")

def MoveTDownSmall():
    MoveT(TBACKWARD, 8, SLOW)
    print("You tilted something down a bit!")

def StartThreadedCamera(FollowBool=False,Width=1280,Height=960):
    
    global cap #can I do this so that cap stays if it's made this way

    try:
        bool(cap) #variable even exists?
    except NameError:
        cap = StartCamera(Width=Width,Height=Height)

    x = threading.Thread(target=ShowCamera, args=([cap,1,FollowBool]))
    #x.setDaemon(True) #trying to fix main thread is not in main loop
    x.start()
    
#BUTTONS FOR SETTING SCAN PARAMETERS


#BEGIN WHAT GOES ONSCREEN

win.title("Windows GUI")
win.geometry('640x480')

LeftFrame = tk.Frame(win)
LeftFrame.pack(side = tk.LEFT)

RightFrame = tk.Frame(win)
RightFrame.pack(side = tk.RIGHT)

TopFrame = tk.Frame(win)
TopFrame.pack(side = tk.TOP)

BottomFrame = tk.Frame(win)
BottomFrame.pack(side = tk.BOTTOM)

YPosition = tk.Label(TopFrame, font=(myFont), height = 2, width=12) #use a Label widget, not Text
YPosition.pack(side = tk.TOP)

YEntry = tk.Entry(TopFrame, width = 4)
YEntry.bind('<Return>', YGet)
YEntry.pack(side=tk.TOP)


YForwardBigButton = tk.Button(TopFrame, text = "⇑", font = myFont, command = MoveYForwardBig, height = 1, width =2 )
YForwardBigButton.pack(side = tk.TOP)

YForwardSmallButton = tk.Button(TopFrame, text = "↑", font = myFont, command = MoveYForwardSmall, height = 1, width =2 )
YForwardSmallButton.pack(side = tk.TOP)

YBackSmallButton = tk.Button(TopFrame, text = "↓", font = myFont, command = MoveYBackSmall, height = 1, width =2 )
YBackSmallButton.pack(side = tk.TOP)

YBackBigButton = tk.Button(TopFrame, text = "⇓", font = myFont, command = MoveYBackBig, height = 1, width =2 )
YBackBigButton.pack(side = tk.TOP)


#display position and provide entrybox
XPosition = tk.Label(LeftFrame, font=(myFont), height = 2, width=12) #use a Label widget, not Text
XPosition.pack(side = tk.LEFT)

XEntry = tk.Entry(LeftFrame, width = 4)
XEntry.bind('<Return>', XGet)
XEntry.pack(side=tk.LEFT)

XLeftBigButton = tk.Button(LeftFrame, text = "⟸", font = myFont, command = MoveXLeftBig, height = 1, width =2 )
XLeftBigButton.pack(side = tk.LEFT)

XLeftSmallButton = tk.Button(LeftFrame, text = "←", font = myFont, command = MoveXLeftSmall, height = 1, width =2 )
XLeftSmallButton.pack(side = tk.LEFT)

XRightSmallButton = tk.Button(LeftFrame, text = "→", font = myFont, command = MoveXRightSmall, height = 1, width =2 )
XRightSmallButton.pack(side = tk.LEFT)

XRightBigButton = tk.Button(LeftFrame, text = "⟹", font = myFont, command = MoveXRightBig, height = 1, width =2 )
XRightBigButton.pack(side = tk.LEFT)

ZPosition = tk.Label(RightFrame, font=(myFont), height = 2, width=12) #use a Label widget, not Text
ZPosition.pack(side = tk.RIGHT)

ZEntry = tk.Entry(RightFrame, width = 4)
ZEntry.bind('<Return>', ZGet)
ZEntry.pack(side=tk.RIGHT)


ZUpBigButton = tk.Button(RightFrame, text = "Z⇑", font = myFont, command = MoveZUpBig, height = 1, width =2 )
ZUpBigButton.pack(side = tk.RIGHT)

ZUpSmallButton = tk.Button(RightFrame, text = "Z↑", font = myFont, command = MoveZUpSmall, height = 1, width =2 )
ZUpSmallButton.pack(side = tk.RIGHT)

ZDownSmallButton = tk.Button(RightFrame, text = "Z↓", font = myFont, command = MoveZDownSmall, height = 1, width =2 )
ZDownSmallButton.pack(side = tk.RIGHT)

ZDownBigButton = tk.Button(RightFrame, text = "Z⇓", font = myFont, command = MoveZDownBig, height = 1, width =2 )
ZDownBigButton.pack(side = tk.RIGHT)

HomeXButton = tk.Button(BottomFrame, text = "HOME X", font = myFont, command = HomeX, height = 2, width =8 )
HomeXButton.pack(side = tk.BOTTOM,pady=5)

HomeYButton = tk.Button(BottomFrame, text = "HOME Y", font = myFont, command = HomeY, height = 2, width =8 )
HomeYButton.pack(side = tk.BOTTOM,pady=5)

HomeZButton = tk.Button(BottomFrame, text = "HOME Z", font = myFont, command = HomeZ, height = 2, width =8 )
HomeZButton.pack(side = tk.BOTTOM,pady=5)

AutoCoinButton = tk.Button(BottomFrame, text = "AUTOCOIN", font = mySmallFont, command = StartAutoCoin, height = 1, width = 15)
AutoCoinButton.pack(side = tk.BOTTOM, pady=5)



#RCWSmallButton = tk.Button(BottomFrame, text = "↻", font = myBigFont, command = MoveRCWSmall, height = 1, width = 2)
#RCWSmallButton.pack(side = tk.BOTTOM, pady=5)

#RCCWSmallButton = tk.Button(BottomFrame, text = "↺", font = myBigFont, command = MoveRCCWSmall, height = 1, width = 2)
#RCCWSmallButton.pack(side = tk.BOTTOM,pady=5)

#TUpSmallButton = tk.Button(BottomFrame, text = "TUP", font = myBigFont, command = MoveTUpSmall, height = 1, width = 2)
#TUpSmallButton.pack(side = tk.BOTTOM, pady=5)

#TDownSmallButton = tk.Button(BottomFrame, text = "TDN", font = myBigFont, command = MoveTDownSmall, height = 1, width = 2)
#TDownSmallButton.pack(side = tk.BOTTOM,pady=5)


SecondaryBottomFrame = tk.Frame(BottomFrame)
SecondaryBottomFrame.pack(side=tk.TOP)

#Display analog value of PD

"""begin resume scan if failed"""


try:
    cap = StartCamera(Width=640,Height=480)
    frame = TakePicture(cap) #for testing
    
    LadyBug = RestartSerial() #initiate GCODE based machine
    StartThreadedCamera() #This is the main opencv window you interact with
    
    scan_file = open('/home/pi/Desktop/ladybug/scandata.pkl', 'rb') 
    #I can't uncomment this pi related stuff without fixing the whole try except block
    scan_params = pickle.load(scan_file)
    scan_file.close()

    HomeX()
    HomeY()
    HomeZ()

    locations = scan_params[0] #position data
    conditions = scan_params[1] #save location, filetype, resolution, timeout, numfailures

    """because R has no endstop we have to set it to what it was in the scan"""
    #global GlobalR #I'm not sure why this causes a syntax error, it wasn'tbefore.
    GlobalR = conditions['R_Location']

    GridScan(locations,conditions) #long broken 
 
except FileNotFoundError:
    #...because there's a hardcoded pi desktop scan file up there
    print('setting DinoLite level to FLC 6, assuming you are using one rn')
    ControlDino('FLCLevel 6')
    print('assuming starting at optimum exposure location')
    print('run command ControlDino("AE on") to turn exposure back on')
    ControlDino('AE off')
    
    print ('Press H to home, F to autofocus, D to autostack, space takes pic')
    print ('i,j,k,l move XY, - + move Z axis')
    
    print('Lets scan some stuff')
    
