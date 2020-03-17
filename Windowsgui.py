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

#Distances from home position in steps for each motor.
#Starts at "0" so if you don't have any switches just move them there before running the program.

GlobalX = 0 #left and right (on finder)
GlobalY = 0 #towards and away from you (on finder)
GlobalZ = 0
GlobalR = 0 #keep same naming scheme, but R = rotation
GlobalT = 0 #Tilt motor!

TCenter = 3800 #X location directly above tilt axis. Determine experimentally
YCenter = 3800 #Same for Y for convenience
GlobalTOffset = 0-TCenter #updated with moving X for dynamic 5 axis adjustment

#Note that resuming a scan is harder (no switches to reset) if using R and T.

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

FactorsOf160 = [1,2,4,5,8,10,16,20,32,40,80,160] #for drop down menu of rotations of R



#FOR FLASHFORGE FINDER WITH KES400A and original bed

TRadius = 20 #default value, generally use calculated dynamically

StepsPerRotation = 4096 #for 8th microstepping on the R axis we have (160 on original)
StepsPerTilt = 1600 #full tilt revolution, probably use half this
RadiansPerStep = (2*math.pi)/StepsPerTilt


XMax = 9250 #max range. Affected by choice of sled
YMax = 7200
ZMax = 29000 #my goodness. Approximate, want to be conservative to not crush my voice coils. #29000 with no giant motor setup
RMax = StepsPerRotation

#steps per mm needed for calculations about correct for tilt

XStepsPerMM = 47 #Measured using USB microscope close to 46.25 measured by hand
ZStepsPerMM = 200



XFORWARD = 1 #Arbitrary
XBACKWARD = 0

YFORWARD = 0 #this is bad coding
YBACKWARD = 1

ZFORWARD = 0
ZBACKWARD = 1

RFORWARD = 1 #To keep naming scchhhomeme. But we'll consider forward as clockwise if referenced
RBACKWARD = 0

TFORWARD = 1
TBACKWARD = 0

 #made faster for finder
FASTERER = 0.0002
FASTER = 0.0004
FAST = 0.001 #delay between steps in s,
SLOW = 0.004
SLOWER = 0.02



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


def RestartSerial(port=6, BAUD = 115200):

    if (not isinstance(port,int)) or (not isinstance(BAUD,int)):
         print ('please specify CNC port and BAUD rate (example: 6 , 115200)')
		
    try:
        CloseSerial() #will pass if no port by ladybug name open
        
        LadyBug = serial.Serial('COM' + str(port), BAUD)
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
    
def TiltCorrection(Initial,Final,Radius ='dynamic',X='default',Z='default'):
    """When we tilt our object, we are also translating it in the Z and X directions.
    this function takes the initial and final tilt position (in steps),
    converts that to a change in angle,
    and then determines the X and Z translation with trig.
    Function returns what the new X and Z values SHOULD BE to retain focus.

    Made dynamic, currently not symmetric forwards and backwards.
    Have to think about what to do for fact that rotary motor shaft is not centered."""



    #flat is pointed to the left

    if X == 'default': #cannot assign globalX in function name or it happens at runtime
        X = GlobalX
    if Z == 'default':
        Z = GlobalZ
    if Radius == 'dynamic': #keeping track dynamically as opposed to a set value
        global GlobalTOffset
        GlobalTOffset = X - TCenter
        TRadius = GlobalTOffset/XStepsPerMM

    Z_Initial = round(TRadius*math.sin(RadiansPerStep*(Initial)),6)
    X_Initial = round(TRadius*math.cos(RadiansPerStep*(Initial)),6)

    Z_Final = round(TRadius*math.sin(RadiansPerStep*(Final)),6)
    X_Final = round(TRadius*math.cos(RadiansPerStep*(Final)),6)

    Z_Change = Z_Final-Z_Initial #in Millimeters
    X_Change = X_Final-X_Initial

    try:
        Z_Change_Steps = round(ZStepsPerMM*Z_Change)
        X_Change_Steps = -1 * round(XStepsPerMM*X_Change) #negative because starting from the left
    except ZeroDivisionError:
        print ("those are the saaaaaaame")

        return False


    Corrected_X = X - X_Change_Steps

    Corrected_Z = Z - Z_Change_Steps
        #should maybe keep track of missing steps from rounding
    return Corrected_X,Corrected_Z


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

def CalculateSpeed(distance):
    #Just returns my terribly named speeds by distance traveled
    #mostly in order to reduce vibrations for short distances
    
    if distance >= 1000:
        SPEED = FASTERER    
    elif 500 <= distance < 1000:
        SPEED = FASTER
    elif 150 <= distance < 500:
        SPEED = FAST
    elif 50 <= distance < 150:
        SPEED = SLOW
    else:
        SPEED = SLOWER
        
    return (SPEED)
    
    
def DefineScan(XMin, XMax, YMin, YMax, ZMin, ZMax, RMin, RMax, XSteps=100, YSteps=100, ZSteps=1, RSteps=1):
    """core from stack exchange. https://stackoverflow.com/questions/20872912/raster-scan-pattern-python
    modified october 11 2018 to include Z and R, meaning R is now set in absolute positions
    Important: Because its not inclusive in max, it will break if for instance you say rmin = 0 rmax = 0, so we add 1 to all maximums
    so if you dont want to go more than one Z or R, set for instance Zmin=Zmax and ZSteps = 1.

    returns a list of four lists which each contain the absolute positions at every point in a scan for x,y,z,r"""

    XMax = XMax+1
    YMax = YMax+1
    ZMax = ZMax+1
    RMax = RMax+1


    # define some grids
    xgrid = arange(XMin, XMax,XSteps)
    ygrid = arange(YMin, YMax,YSteps)
    zgrid = arange(ZMin, ZMax, ZSteps)
    rgrid = arange(RMin,RMax,RSteps)

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

    ScanLocations = {'X':NewNewXScan,'Y':NewNewYScan,'Z':NewNewZScan,'R':NewNewRScan}
    
    
    CalculateOverlap(XSteps,YSteps,PixelsPerStep=1)
    
    print("{} images".format(len(NewNewXScan)))
    
    
    return(ScanLocations)


def GridScan(ScanLocations,conditions='default'):

    XCoord = ScanLocations['X']
    YCoord = ScanLocations['Y']
    ZCoord = ScanLocations['Z']
    RCoord = ScanLocations['R']

    start_time = time.time()

    """Note that we have already added 1 in the DefineScan to account for half intervals"""


    """conditions will contain save location, filetype, resolution. num_failures. First time running default
    is passed which contains standard conditions, but you can always specify it if you want to."""

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

    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    ZGoTo(int(ZCoord[0]))
    #RGoTo(int(RCoord[0]))



    for i in range(num_pictures):

        if i % 100 == 0: #every 100 pics
            print("{} of {} pictures remaining".format((num_pictures-i),original_pics))
            GPIO.output(BEEP,GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(BEEP,GPIO.LOW)

        folder = save_location + "/Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3) #will make new folder on each change in Z or R
        if not os.path.exists(folder): #should hopefully continue saving in the same folder after restart
            os.makedirs(folder)


        #go to locations

        XGoTo(int(XCoord[i]))
        YGoTo(int(YCoord[i]))
        ZGoTo(int(ZCoord[i]))
        RGoTo(int(RCoord[i]))

        time.sleep(0.1) #vibration control.



        #changed from original to add more zfill and no "of"
        name = "X" + str(XCoord[i]).zfill(5) + "Y" + str(YCoord[i]).zfill(5) + "Z" + str(ZCoord[i]).zfill(5) + "R" + str(RCoord[i]).zfill(4) + filetype

        """begin filesaving block"""

        try:
            for w in range(3):

                proc = subprocess.Popen(["fswebcam", "-r " + resolution, "--no-banner", folder + "/" + name, "-q"], stdout=subprocess.PIPE) #like check_call(infinite timeout)
                output = proc.communicate(timeout=10)[0]

                if os.path.isfile(folder + "/" + name): #better than checking time elapsed...
                    if w > 0: #USB was restarted
                        print ('Okay thanks bozo. Restarting with {}'.format(name))

                    break #move on to next picture

                elif (w <= 1): #usb got unplugged effing #hell

                    #attempt to catch USB from https://stackoverflow.com/questions/1335507/keyboard-input-with-timeout-in-python
                    print('HEY BOZO THE USB GOT UNPLUGGED UNPLUG IT AND PLUG IT BACK IN WITHIN {} SECONDS OR WE REBOOT'.format(timeallowed))
                    print('check if {} failed'.format(name))

                    GPIO.output(BEEP,GPIO.HIGH) #beep and bibrate

                    time.sleep(timeallowed)

                    GPIO.output(BEEP,GPIO.LOW)

                else: #USB unpluged and it wasn't plugged in in time
                    UpdatedX = XCoord[i:]
                    UpdatedY = YCoord[i:]
                    UpdatedZ = ZCoord[i:]
                    UpdatedR = RCoord[i:]

                    UpdatedScanLocations = {'X':UpdatedX, 'Y':UpdatedY, 'Z': UpdatedZ,'R':UpdatedR}

                    num_failures +=1

                    failed_pics.append(name)
                    failure_times.append(time.time())

                    conditions = {'save_location':save_location,
                                  'R_Location':int(RCoord[i]),
                                  'filetype':filetype,
                                  'resolution':resolution,
                                  'num_failures':num_failures,
                                  'original_pics':original_pics,
                                  'original_time':original_time,
                                  'original_locations':original_locations,
                                  'failed_pics':failed_pics,
                                  'failure_times':failure_times} #after restart because no gui timeout after 0 seconds

                    scan_params = [UpdatedScanLocations,conditions]
                    print(scan_params)
                    time.sleep(2)

                    scan_file = open('/home/pi/Desktop/ladybug/scandata.pkl', 'wb') #hardcode scan location

                    pickle.dump(scan_params,scan_file) #working!
                    scan_file.close()

                    print('restarting sorryyyyyy')

                    restart()

        except subprocess.TimeoutExpired: #does not catch USB UNPLUG. Catches if it takes too long because lag

            print ("{} failed :( ".format(name))
            proc.terminate() #corrective measure?
            continue #move on. In true loop, it keeps trying the same picture since it shouldn't matter which one



    print ('scan completed successfully after {} seconds! {} images taken and {} restarts'.format(time.strftime("%H:%M:%S", time.gmtime(time.time() - original_time)), str(original_pics),str(num_failures)))
    try:
        os.rename('/home/pi/Desktop/ladybug/scandata.pkl','/home/pi/Desktop/ladybug/scandataold.pkl') #quick fix to avoid infinite loop while still being able to analyze
    except FileNotFoundError:
        print('nooooooo failures! woo')

    for i in range(5):
        GPIO.output(BEEP,GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BEEP,GPIO.LOW)

    b = input('press enter to exit')


def XGoTo(XDest,speed = 2000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalX


    X,Y,Z,E = XDest, GlobalY, GlobalZ, GlobalR        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalX = X
    
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax))
    
def YGoTo(YDest,speed = 2000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalY


    X,Y,Z,E = GlobalX, YDest, GlobalZ, GlobalR        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalY = Y
    
    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))

def ZGoTo(ZDest,speed = 2000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalZ


    X,Y,Z,E = GlobalX, GlobalY, ZDest, GlobalR        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalZ = Z
    
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))    

def RGoTo(RDest,speed = 2000):
    #everything being switched to milimeters at this point, sorry. 

    global GlobalR


    X,Y,Z,E = GlobalX, GlobalY, GlobalZ, RDest        
    
    GCode = GenerateCode(X,Y,Z,E,speed)
    SendGCode(GCode)
    GlobalR = E
    
    RPosition.configure(text="R: "+str(GlobalR) + "/" + str(RMax))


def XGet(event):
    '''records enter press from text box (XEntry) and calls "go to specified location function'''
    try:
        XDest = int(event.widget.get())
        XGoTo(XDest)
    except ValueError: #hey dumbo enter an integer
        print ("hey dumbo enter an integer")

def YGet(event):
    '''records enter press from text box (YEntry) and calls "go to specified location function'''
    try:
        YDest = int(event.widget.get())
        YGoTo(YDest)
    except ValueError: #hey dumbo enter an integer
        print ("hey dumbo enter an integer")



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
        ZDest = int(event.widget.get())
        ZGoTo(ZDest)
    except ValueError: #hey dumbo enter an integer
        print ("hey dumbo enter an integer")



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
    MoveX(XBACKWARD,100,FAST)
    print("X moved to da left a lot!")

def MoveXLeftSmall():
    MoveX(XBACKWARD,10,SLOW)
    print("X moved to da left a little!")

def MoveXRightBig():
    MoveX(XFORWARD,100,FAST)
    print("X moved to da right a lot!")

def MoveXRightSmall():
    MoveX(XFORWARD,10,SLOW)
    print("X moved to da right a little!")


def MoveYForwardBig():
    MoveY(YFORWARD,100,FAST)
    print("Y moved forward a lot!")

def MoveYForwardSmall():
    MoveY(YFORWARD,10,SLOW)
    print("Y moved forward a little!")

def MoveYBackBig():
    MoveY(YBACKWARD,100,FAST)
    print("Y moved back a lot!")

def MoveYBackSmall():
    MoveY(YBACKWARD,10,SLOW)
    print("Y moved back a little!")



def MoveZDownBig(): #dir dis delay
    MoveZ(ZBACKWARD,250,FASTER) #faster than others to reduce time on
    print("Z moved down a lot!")

def MoveZDownSmall():
    MoveZ(ZBACKWARD,25,FAST)
    print("Z moved down a little!")

def MoveZUpBig():
    MoveZ(ZFORWARD,250,FASTER)
    print("Z moved up a lot!")

def MoveZUpSmall():
    MoveZ(ZFORWARD,25,FAST)
    print("Z moved up a little!")

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