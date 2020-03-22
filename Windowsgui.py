#!/usr/bin/env python3

#MARCH 16 2020! Convert beefy gui to try and run a scan with gcodes and like physically clicking buttons on the dinolite program

from numpy import * #for generating scan parameters
import random #for repeatability tests
import time
import math
import os
import tkinter as tk #contains GUI, can be removed if converted to headless
from tkinter import font
from tkinter import filedialog
import sys
import select #for timeouts and buzzing when usb gets disconnect
import pickle #for saving scan data and resuming
import serial 
import subprocess
import cv2
from PIL import Image, ImageTk


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
RScanNumber = 1 #needs consolidation with absolute value positioning system. kind of a mess


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

BigZ = 2
LittleZ = 0.1 #maybe even too big but can be played with

timeout = 0.1 #default timeout for serial, important for GetPositions

win = tk.Tk()
myFont = tk.font.Font(family='Helvetica', size=12, weight='bold')
myBigFont = tk.font.Font(family='Helvetica', size=20,weight='bold')
font.families()

def ConvertStepsToMM (XSteps,YSteps,ZSteps,ESteps, XStepsPerMM=80,YStepsPerMM=80,ZStepsPerMM=400,EStepsPerMM = 33.33):
    XMM = round(XSteps/XStepsPerMM,4)
    YMM = round(YSteps/YStepsPerMM,4)
    ZMM = round(ZSteps/ZStepsPerMM,4)
    EMM = round(ESteps/EStepsPerMM,4)
    
    #consider having a residual counter?
    
    return (XMM,YMM,ZMM,EMM)

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


def SendGCode(GCode,machine='ladybug'):

    if machine == 'ladybug':
        machine = LadyBug
    
    GCode  += " /r\n"
    #print(GCode)
    #return(GCode)
    BytesGCode = GCode.encode('utf-8')
    machine.write(BytesGCode)

def EngageSteppers():
    SendGCode("M84 S3600") #tells it not to turn off motors for S seconds (default 60 grr)
    SendGCode("M17") #engage steppers

def DisengageSteppers():
    SendGCode("M18")

def GetPositions(machine = 'ladybug'):
    #returns dictionary X,Y,Z and maybe R of actual position at time of request
    #known issues of    

    sleeptime = 0.02
    
    if machine == 'ladybug': #fix so it doesn't fail at runtime. not proper 4sure
        machine = LadyBug 
        
    previous_buffer = machine.read_all() #clear buffer essentially

    SendGCode("M114") #report machine status
    time.sleep(sleeptime)
    for i in range (2): #communication back and forth not instant, i for failsafe
        try:
            dump = machine.read_until().decode('utf-8') #kept in bytes. read_all inconsistent
        
        except serial.SerialTimeoutException():
        
            print('timeout')
            return False
        
        if 'Count' in dump: #precedes actual position data

            remainder = dump[dump.find('Count'):] #has actual position
            
            Xraw = remainder[remainder.find('X:'):remainder.find('Y')]
            Yraw = remainder[remainder.find('Y:'):remainder.find('Z')]
            Zraw = remainder[remainder.find('Z:'):]

            X = float(''.join([s for s in Xraw if (s.isdigit() or s == '.')]).strip())
            Y = float(''.join([s for s in Yraw if (s.isdigit() or s == '.')]).strip())
            Z = float(''.join([s for s in Zraw if (s.isdigit() or s == '.')]).strip())

            #if ('.' not in X) or ('.' not in X) or ('.' not in X):
                #readline sometimes inconsistent. Common denominatior
            positions = {'X':X,'Y':Y,'Z':Z,'delay':i*sleeptime,'raw':dump,'prev':previous_buffer}
            return positions
        else:
            time.sleep(sleeptime) #and loop back to try again
    print('communication lag --- check USB cable or port if frequent')    
    return(False)

def RestartSerial(port=8, BAUD = 115200,timeout=timeout):

    if (not isinstance(port,int)) or (not isinstance(BAUD,int)):
         print ('please specify CNC port and BAUD rate (example: 6 , 115200)')
		
    try:
        CloseSerial() #will pass if no port by ladybug name open
        
        LadyBug = serial.Serial('COM' + str(port), BAUD,timeout=timeout)
        return LadyBug #name of controllable CNC machine
    
    except Exception: #SerialException is proper but not working
        
        print ('unable to connect to port {}, sacrifice a goat or whatever to fix it'.format(port))


def CloseSerial(machine = 'ladybug'):
    try:
        if machine == 'ladybug':
            machine = LadyBug
        machine.close()
    except NameError:
        pass
    

def CalculateOverlap(XSteps,YSteps,PixelsPerStep=1,XWidth=640,YHeight=480):
    #basic function gives percent overlap based on x/y pixels per step (same value if straight scope)
    #generally wasteful to exceed 50 percent overlap
    
    #3750 =~ 4000 steps away from object (19 =~20mm) 1 to 1 pixels per step with dinolite basic 
    #500 steps or 2.5ish mm is 1.5 pixels/step
    
    #250 steps away (2nd zoom mode only) is 7.5 pixels/step 
    
    XOverlap = ((XWidth-XSteps*PixelsPerStep)/XWidth)*100 #in percent
    YOverlap = ((YHeight-YSteps*PixelsPerStep)/YHeight)*100
    
    print ("X overlap is {}%, Y Overlap is {} if {} Pixels Per Step displacement".format(XOverlap,YOverlap,PixelsPerStep))
    
    return (XOverlap,YOverlap,PixelsPerStep)

    
def DefineScan(XMin, XMax, YMin, YMax, ZMin, ZMax, RMin, RMax, XSteps=100, YSteps=100, ZSteps=1, RSteps=1):
    """core from stack exchange. https://stackoverflow.com/questions/20872912/raster-scan-pattern-python
    modified october 11 2018 to include Z and R, meaning R is now set in absolute positions
    Important: Because its not inclusive in max, it will break if for instance you say rmin = 0 rmax = 0, so we add 1 to all maximums
    so if you dont want to go more than one Z or R, set for instance Zmin=Zmax and ZSteps = 1.

    modified 3/19/20 to act with millimeters and floats (to two decimal places) 
    
    returns a list of four lists which each contain the absolute positions at every point in a scan for x,y,z,r"""

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
    my own code to account for Z now. Not efficient if there are a LOT of Z changes (it does X/Y rastering and returns to initial position for each Z).
    Otherwise it's ok.
    Note this will return empty lists if zgrid is empty (minz=maxz)


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
    
    
    CalculateOverlap(XSteps,YSteps,PixelsPerStep=1)
    
    print("{} images".format(len(NewNewXScan)))
    
    
    return(ScanLocations)



#all assumes cv2 here
def StartCamera(camera = 1, width = 1280, height = 960):

    cap = cv2.VideoCapture(camera)
    cap.set(3,1280)
    cap.set(4,960)
    
    ret,junkframe = cap.read() #junk because must grab first frame THEN set LED controls
    
    return cap #and pass to TakePicture

def TakePicture(cap):
    
    ret,frame = cap.read() 

    return frame

def SavePicture(name,frame):

    cv2.imwrite(name,frame)
    
def CloseCamera(cap):

    cap.release()


def ControlDino(setting = "FLCLevel" ,value=6):
    """uses dinolite windows batch file to control settings on EDGE plus model.
    assumes batch file in same folder as this gui
    Can change autoexposure or set value, which LEDs are on, and brightness as group
    Some values are redundant or unavailable with my cam, E.G FLC control supercedes simple LED

    "FLCLevel" --- 1-6 brightness, if  0 convert to LED off
    "FLCSwitch": control quadrants, value is 1111, 1010...
    "AE on": this means you CAN select exposure. Confusing
    "AE off"
    "EV": sets exposure values 16-220
    """
    

    if setting == "FLCLevel":
        subprocess.call('DN_DS_Ctrl.exe LED ON') #can't change FLC if it's already off
                        
        if value == 0:
            setting = "LED off"
            value = ""
                

    subprocess.call('DN_DS_Ctrl.exe ' + setting + " " + (str(value) if value else ""))
        
    
    

def GridScan(ScanLocations,conditions='default'):

    XCoord = ScanLocations['X']
    YCoord = ScanLocations['Y']
    ZCoord = ScanLocations['Z']
    RCoord = ScanLocations['R']

    start_time = time.time()

    """Note that we have already added 1 in the DefineScan to account for half intervals"""


    """conditions will contain save location, filetype, resolution. num_failures. First time running default
    is passed which contains standard conditions, but you can always specify it if you want to.

    most of this is irrelevant in the windows GUI"""

    if conditions == 'default':
        save_location = filedialog.askdirectory()
        filetype = ".jpg"
        resolution = "640x480" #fswebcam adjusts to be higher at least with alternate microscope I have
        timeallowed = 5 #number of seconds you have to save the scan.
        num_failures = 0
        original_pics = len(XCoord)
        original_time = start_time
        original_locations = ScanLocations
        failed_pics=[]
        failure_times=[]

    else:
        save_location = conditions['save_location']
        filetype = conditions['filetype']
        resolution = conditions['resolution']
        timeallowed=0 #after one restart we don't bother trying to save scan
        num_failures=conditions['num_failures']
        failed_pics=conditions['failed_pics']
        failure_times=conditions['failure_times']
        original_pics=conditions['original_pics']
        original_time=conditions['original_time']
        original_locations=conditions['original_locations']

    num_pictures = len(XCoord) #remaining, not originally
    NumberOfRotations = len(set(RCoord))
    stepsPerRotation = ((max(RCoord)-min(RCoord))/len(set(RCoord)))
  
    #print("Stepping {} per image".format(str(StepsPerRotation))) #just for debugging
    print("has failed and restarted {} times so far".format(str(num_failures)))

    cap = StartCamera()
    
    #DO ANY ADJUSTING OF CAMERA CONDITIONS HERE AFTER STARTING CAMERA
    

    for i in range(num_pictures):

        X = XCoord[i]
        Y = YCoord[i]
        Z = ZCoord[i]
        R = RCoord[i]

        #5 digits total with 2 decimals always and leading and trailing 0s if necessary

        XStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(X))))).zfill(5)
        YStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(Y))))).zfill(5)
        ZStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(Z))))).zfill(5)
        RStr = (''.join(filter(lambda i: i.isdigit(), ('{0:.2f}'.format(R))))).zfill(5)
        
                
        if i % 100 == 0: #every 100 pics
            print("{} of {} pictures remaining".format((num_pictures-i),original_pics))

        folder = save_location + "/Z" + ZStr + "R" + RStr #will make new folder on each change in Z or R
        if not os.path.exists(folder): #should hopefully continue saving in the same folder after restart
            os.makedirs(folder)


        #go to locations
 
        XGoTo(X)
        YGoTo(Y)
        ZGoTo(Z)
        RGoTo(R)

        #gcode confirmation movement block
    
        while True:
            time.sleep(0.1)
            positions = GetPositions()
            if positions:
                #print(positions['X'],positions['Y'],positions['Z'])
                if (X == positions['X']
                    and Y == positions['Y']
                    and Z == positions['Z']
                    ):
                
                    break #go ahead and take a picture
                else:
                    continue

                    
                
                        
        print('synchronized pic')
        name = "X" + XStr + "Y" + YStr + "Z" + ZStr + "R" + RStr + filetype

        """begin filesaving block"""

        try:
            frame = TakePicture(cap)
            SavePicture(folder + "/" + name,frame) #check whether pic saved properly?
        except Exception: #Filesaving errors go here
            print('error taking pictures')
            
    
    print ('scan completed successfully after {} seconds! {} images taken and {} restarts'.format(time.strftime("%H:%M:%S", time.gmtime(time.time() - original_time)), str(original_pics),str(num_failures)))

    #go back to beginning simplifies testing, but could also set a park position
    XGoTo(XCoord[0])
    YGoTo(YCoord[0])
    ZGoTo(ZCoord[0])
    RGoTo(RCoord[0])

    #beeping block
    

def XGoTo(XDest,speed = 10000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalX


    X,Y,Z,E = XDest, GlobalY, GlobalZ, GlobalR        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalX = round(X,2)
    
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))
    
def YGoTo(YDest,speed = 10000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalY


    X,Y,Z,E = GlobalX, YDest, GlobalZ, GlobalR        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalY = round(Y,2)
    
    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))

def ZGoTo(ZDest,speed = 5000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalZ


    X,Y,Z,E = GlobalX, GlobalY, ZDest, GlobalR        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalZ = round(Z,2)
    
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
        print ("hey dumbo enter a number")

def YGet(event):
    '''records enter press from text box (YEntry) and calls "go to specified location function'''
    try:
        YDest = float(event.widget.get())
        YGoTo(YDest)
    except ValueError: #hey dumbo enter an number
        print ("hey dumbo enter an number")



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
        print ("hey dumbo enter a number")



def HomeX():
    global GlobalX

    SendGCode('G28 X')

    GlobalX = 0
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))

def HomeY():
    global GlobalY

    SendGCode('G28 Y')

    GlobalY = 0
    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))

def HomeZ():
    global GlobalZ

    SendGCode('G28 Z')

    GlobalZ = 0
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))
    
def Home():
    #probably could consume the other three
    SendGCode('G28')
    
    GlobalZ = 0
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))
    GlobalY = 0
    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))
    GlobalX = 0
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))



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


#BUTTONS FOR SETTING SCAN PARAMETERS


#BEGIN WHAT GOES ONSCREEN

win.title("Raspberry Pi GUI")
win.geometry('1400x880')

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


RCWSmallButton = tk.Button(BottomFrame, text = "↻", font = myBigFont, command = MoveRCWSmall, height = 1, width = 2)
RCWSmallButton.pack(side = tk.BOTTOM, pady=5)

RCCWSmallButton = tk.Button(BottomFrame, text = "↺", font = myBigFont, command = MoveRCCWSmall, height = 1, width = 2)
RCCWSmallButton.pack(side = tk.BOTTOM,pady=5)

TUpSmallButton = tk.Button(BottomFrame, text = "TUP", font = myBigFont, command = MoveTUpSmall, height = 1, width = 2)
TUpSmallButton.pack(side = tk.BOTTOM, pady=5)

TDownSmallButton = tk.Button(BottomFrame, text = "TDN", font = myBigFont, command = MoveTDownSmall, height = 1, width = 2)
TDownSmallButton.pack(side = tk.BOTTOM,pady=5)


SecondaryBottomFrame = tk.Frame(BottomFrame)
SecondaryBottomFrame.pack(side=tk.TOP)

#Display analog value of PD

"""begin resume scan if failed"""


try:
	
    LadyBug = RestartSerial() #initiate GCODE based machine
    time.sleep(3)
    EngageSteppers() #prevents default timeout from happening

    #LaserTest = DefineScan(1100,1300,600,800,0,0,0,0,20,20) #placed in a random location so it will get lost


    scan_file = open('/home/pi/Desktop/ladybug/scandata.pkl', 'rb')

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

    GridScan(locations,conditions)

except FileNotFoundError:

    print('no saved scan file found. doing nothing')
