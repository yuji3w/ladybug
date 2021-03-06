#!/usr/bin/env python3

from numpy import *
import random
import time
import math
import os
import tkinter as tk
from tkinter import font
from tkinter import filedialog
import RPi.GPIO as GPIO
import subprocess #For taking a picture with fswebcam
import sys
import select #for timeouts and buzzing when usb gets disconnect
import pickle
#import Adafruit_ADS1x15

#adc = Adafruit_ADS1x15.ADS1115() #our analog input
GAIN = 16  #1,2,4,68,16. We have a small collection area PD 

GPIO.setmode(GPIO.BOARD)

GlobalX = 0 #X distance from home in steps
GlobalY = 0
GlobalZ = 0
GlobalR = 0 #keep same naming scheme, but R = rotation
#Note that upon resuming a scan we have to reset this to R we left off

#These are set by the GUI and passed off to scan configuration
XScanMin = 0
XScanMax = 0
YScanMin = 0
YScanMax = 0
ZScanMin = 0
ZScanMax = 0
XScanStep = 100 #A good default
YScanStep = 100
ZScanStep = 500 
RScanNumber = 1

FactorsOf160 = [1,2,4,5,8,10,16,20,32,40,80,160] #for drop down menu of rotations of R

#PDIn = 7 #photodiode input pin

 
YDIR = 26 #SAMPLE #change back to 26
XDIR = 18 #CAMERA
ZDIR = 40
RDIR = 19 #for clock and counterclock

YSTEP = 24 #stepping pin 
XSTEP = 16
ZSTEP = 38
RSTEP = 23

BEEP = 33 #GPIO pin to beep for pleasing yujie

#FOR FLASHFORGE FINDER WITH KES400A and original bed

XMax = 9000 #max range. Affected by choice of sled
YMax = 6800
ZMax = 29000 #my goodness. Approximate, want to be conservative to not crush my voice coils.

StepsPerRotation = 160 #for 8th microstepping on the R axis we have

XLimit = 8 #limit switch pin input
YLimit = 10
ZLimit = 12 #optical switch. Goes low but there is a transition over a few microsteps

XFORWARD = 1 #Arbitrary  
XBACKWARD = 0   

YFORWARD = 0 #this is bad coding
YBACKWARD = 1

ZFORWARD = 0
ZBACKWARD = 1

RFORWARD = 1 #To keep naming scchhhomeme. But we'll consider forward as clockwise if referenced
RBACKWARD = 0

FASTERER = 0.0003
FASTER = 0.0006
FAST = 0.002 #delay between steps in s,
SLOW = 0.007
SLOWER = 0.03

GPIO.setup(BEEP, GPIO.OUT)

GPIO.setup(XDIR, GPIO.OUT)
GPIO.setup(YDIR, GPIO.OUT)
GPIO.setup(ZDIR, GPIO.OUT)
GPIO.setup(RDIR, GPIO.OUT)

GPIO.setup(XSTEP, GPIO.OUT)
GPIO.setup(YSTEP, GPIO.OUT)
GPIO.setup(ZSTEP, GPIO.OUT)
GPIO.setup(RSTEP, GPIO.OUT)

GPIO.setup(YLimit, GPIO.IN, pull_up_down=GPIO.PUD_UP) #sense pin for Y home switch
GPIO.setup(XLimit, GPIO.IN, pull_up_down=GPIO.PUD_UP) #sense pin for X home switch
GPIO.setup(ZLimit, GPIO.IN, pull_up_down=GPIO.PUD_UP) 

#GPIO.setup(PDIn, GPIO.IN)

win = tk.Tk()
myFont = tk.font.Font(family='Helvetica', size=12, weight='bold')
myBigFont = tk.font.Font(family='Helvetica', size=20,weight='bold')
font.families()


def AnalogGet(samples=1,Gain=GAIN): #returns differential analog output from photodiode
    Analog_List = []
    for i in range(samples): #maybe add hardcode delay. Helps variance problems, can be made to report standard deviation
        Analog_Val = adc.read_adc_difference(3, gain=Gain)
        Analog_List.append(Analog_Val)
        
    Analog_Mean = mean(Analog_List)
    return Analog_Mean

def FindLaserFocus(ZMin = 0, ZMax = 3000, StepSize = 1, Sample_Number = 5, GoToFocus = True):
    """Moves Z axis through a range of values, finds the location with peak PD signal, and returns values"""
    AnalogList = [] #values
    ZList = [] #we'll save which ones we queried
    for i in range(ZMin,ZMax,StepSize):
        ZGoTo(i)
        AnalogList.append(AnalogGet(5)) #actual analog datapoint
        ZList.append(i)
        
    AnalogPeak = max(AnalogList)# note that if you actually look at the data, there tends to be 20 microns in each direction of ogood signaol
    
    ZPeak = ZList[AnalogList.index(AnalogPeak)] #Zlocation of peak
    
    if GoToFocus: #change Z value to location of highest focus
        ZGoTo(ZPeak)
        
    return AnalogPeak,ZPeak

def restart(): #restart pi
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)


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
    return(ScanLocations)

def LaserScan(ScanLocations, Adjust_Z=True, Sample_Number = 5, Z_Tolerance=20):
    #goes to each location in scan locations and saves the analog PD output into a list.
    #I envision this as being a subroutine within grid scan as the "take a picture".
    #unlikely to use rotation but keeping it so we don't have to change anything.
    #optional parameter uses find focus algorithm to adjust Z axis on the fly (future voice coils) 
    
    XCoord = ScanLocations['X']
    YCoord = ScanLocations['Y']
    ZCoord = ScanLocations['Z']
    RCoord = ScanLocations['R']
    
    num_pictures = len(XCoord) #remaining, not originally
    NumberOfRotations = len(set(RCoord))
    stepsPerRotation = ((max(RCoord)-min(RCoord))/len(set(RCoord)))
    
    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    if not Adjust_Z:
        
        ZGoTo(int(ZCoord[0]))
    else:
        Analog_Peak,Z_Peak = FindLaserFocus(2000,3000,5) #skips each 2 to just get in right area. #switch to 0-3k after testing
    #RGoTo(int(RCoord[0]))

    DigitalList = [] #list contains 1 and 0 outputs of PD at each loc
    for i in range(num_pictures):
        
        if i % 100 == 0: #every 100 pics
            print("laser scan {}% done".format((i*100/num_pictures)))
            GPIO.output(BEEP,GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(BEEP,GPIO.LOW)
        
        XGoTo(int(XCoord[i]))
        YGoTo(int(YCoord[i]))
        #RGoTo(int(RCoord[i]))

        time.sleep(0.1)
        if not Adjust_Z:
            ZGoTo(int(ZCoord[i]))
                
            DigitalList.append(AnalogGet(Sample_Number)) #differential output comparing PD voltage source to PD output
        else:
            Analog_Peak, Z_Peak = FindLaserFocus((Z_Peak-Z_Tolerance),(Z_Peak+Z_Tolerance),1,Sample_Number) ##note might fail if peak around max end of Z range

            ZCoord[i] = Z_Peak
            DigitalList.append(Analog_Peak)
                
        
    
    #go to initial position for easy scan repeat
    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    ZGoTo(int(ZCoord[0]))
    #RGoTo(int(RCoord[0]))
    
    ScanResults = [[XCoord],[YCoord],[DigitalList]] #just to simplify handling. dump to pickle 
    
    scan_file = open('/home/pi/Desktop/ladybug/laserresults.pkl', 'wb') 
                         
    pickle.dump(ScanResults,scan_file) #working!
    scan_file.close()
                    
    return(ScanResults)

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
        filetype = ".png"
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
    
    print("Stepping {} per image".format(str(StepsPerRotation))) #just for debugging
    print("has failed and restarted {} times so far".format(str(num_failures)))
    
    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    ZGoTo(int(ZCoord[0]))
    #RGoTo(int(RCoord[0]))
    
    
        
    for i in range(num_pictures):
        
        if i % 100 == 0: #every 100 pics
            print("{} of {} pictures remaining".format((num_pictures-i),original_pics))
            GPIO.output(BEEP,GPIO.HIGH)
            time.sleep(0.3)
            GPIO.output(BEEP,GPIO.LOW)
        
        folder = save_location + "/Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3) #will make new folder on each change in Z or R
        if not os.path.exists(folder): #should hopefully continue saving in the same folder after restart
            os.makedirs(folder)
                
            
        #go to locations
                    
        XGoTo(int(XCoord[i]))
        YGoTo(int(YCoord[i]))
        ZGoTo(int(ZCoord[i]))
        #RGoTo(int(RCoord[i]))
            
        time.sleep(0.1) #vibration control.
                
            
            
            
        name = "X" + str(XCoord[i]).zfill(4) + "Y" + str(YCoord[i]).zfill(4) + "Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3) + "of" + str(NumberOfRotations).zfill(3) + filetype

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

    a = input('press any key to exit')
def XRepeatTest(num_trials=100):
    
    HomeX()
    HomeX() #twice just to make sure it's good
    HomeX() #first couple homes are sometimes wonky. 
    global XMax
    total_steps = 0
    ranlocold = 0 #location old
    ListOfLoc = [0] #include initial location
    
    for i in range(num_trials):
        ranloc = random.randrange(100,XMax-100)
        total_steps += (abs(ranlocold-ranloc))
        ranlocold = ranloc
        ListOfLoc.append(ranloc)
        
        XGoTo(ranloc)
    
    StepsToHome = HomeX() #first bounce
   
    imperfection = ranloc - StepsToHome
    
    print("after {} total steps, over {} movements, it took {} steps to home instead of {}, for an imperfection of {}".format(total_steps,num_trials,StepsToHome,ranloc,imperfection))
    
    return([total_steps,imperfection,ListOfLoc])    


def YRepeatTest(num_trials=100): 
    
    HomeY()
    HomeY() 
    HomeY() #The first couple of homes are sometimes wonky
    global YMax
    total_steps = 0
    ranlocold = 0 #location old
    ListOfLoc = [0] #include initial location
    
    for i in range(num_trials):
        ranloc = random.randrange(100,YMax-100) #more than 0, less than max, in case misteps bring it to end of range
        total_steps += (abs(ranlocold-ranloc))
        ranlocold = ranloc
        ListOfLoc.append(ranloc)
        
        YGoTo(ranloc)
    
    StepsToHome = HomeY() #first bounce
    
    imperfection = ranloc - StepsToHome
     
    print("after {} total steps, over {} movements, it took {} steps to home instead of {}, for an imperfection of {}".format(total_steps,num_trials,StepsToHome,ranloc,imperfection))
    
    return([total_steps,imperfection,ListOfLoc])    

def MultiRepeatTest(num_repeats = 100):
    """calls y and x repeat many times with random numbers so we can plot stuff"""
    X_History = [] #populated with list of lists. Each list being 
    Y_History = []
    for i in range(num_repeats): #total trials
        numpertrial = 100 #random.randrange(1,10) #number of runs per trial
        
        XHomeData = XRepeatTest(numpertrial)
        YHomeData = YRepeatTest(numpertrial)
        
        XHomeData.append(numpertrial) #aka, final is [total steps, imperfection, num_times it moved, ListOfLoc]
        YHomeData.append(numpertrial)
        
        X_History.append(XHomeData)
        Y_History.append(YHomeData)
        
    
    #with open ('Xmultirepeat.txt', 'rb') as fp: #not human readable
    #    pickle.dump(X_History, fp)
    
    #with open('Ymultirepeat.txt', 'rb') as fp:
    #    pickle.dump(Y_History, fp)
        
        
    return(X_History,Y_History)        


def MoveX(direction,numsteps,delay):
    '''parent function for x. '''
    
    GPIO.output(XDIR, direction)
        
    for i in range(numsteps):
            
            GPIO.output(XSTEP, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(XSTEP, GPIO.LOW)
    
    global GlobalX
    
    if direction == 1: #totally arbitrary.
        GlobalX += numsteps
    else:
        GlobalX -= numsteps
    
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax)) #updates the global position on the screen. Not a good way to do it!
    
def XGoTo(XDest, XMin=0):
    """checks the place is valid and then calls MoveX appropriately.
    Should be upgradable to have boundaries, aka min and max."""
    global GlobalX
    global XMax
    
    if not isinstance(XDest,int):
        return ('integers only dingus') #this is not good practice right
        
    if XDest <= XMax and XDest >= XMin:
        distance = XDest - GlobalX
        if distance > 0: #forward
            MoveX(XFORWARD,distance,FASTER)
        else:
            MoveX(XBACKWARD,abs(distance),FASTER) 
    else:
        print ('Destination out of range')

def XGet(event):
    '''records enter press from text box (XEntry) and calls "go to specified location function'''
    try:
        XDest = int(event.widget.get())
        XGoTo(XDest)
    except ValueError: #hey dumbo enter an integer
        print ("hey dumbo enter an integer")    

def MoveY(direction,numsteps,delay):
    '''parent function for Y. '''
    
    GPIO.output(YDIR, direction)    
        
    for i in range(numsteps):
            
        GPIO.output(YSTEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(YSTEP, GPIO.LOW)        
    
    global GlobalY
    
    if direction == 0: #totally arbitrary 
        GlobalY += numsteps
    else:
        GlobalY -= numsteps
    YPosition.configure(text="Y: "+str(GlobalY) + "/" +str(YMax))

def YGoTo(YDest, YMin=0):
    """checks the place is valid and then calls MoveY appropriately.
    Should be upgradable to have boundaries, aka min and max."""
    global GlobalY
    global YMax
    if not isinstance(YDest,int):
        return ('integers only dingus') #this is not good practice right
        
    if YDest <= YMax and YDest >= YMin:
        distance = YDest - GlobalY
        if distance > 0: #forward
            MoveY(YFORWARD,distance,FASTER)
        else:
            MoveY(YBACKWARD,abs(distance),FASTER) 
    else:
        print ('Destination out of range')

def YGet(event):
    '''records enter press from text box (YEntry) and calls "go to specified location function'''
    try:
        YDest = int(event.widget.get())
        YGoTo(YDest)
    except ValueError: #hey dumbo enter an integer
        print ("hey dumbo enter an integer")    


def MoveR(direction,numsteps,delay):

    GPIO.output(RDIR, direction)
    global GlobalR
    
    for i in range(numsteps):
        GPIO.output(RSTEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(RSTEP,GPIO.LOW)
    
    #insert counting information here
        


def MoveZ(direction,numsteps,delay):
    '''parent function for Z. This version has no sleep pin enable/disable:
    USE ONLY WITH LOW VOLTAGE (Less than 5v, less than 150 ma, or whatever
    doesn't cause the motor to overheat'''
    
    GPIO.output(ZDIR, direction)
    global GlobalZ
    global ZMax     
    for i in range(numsteps):
            
        GPIO.output(ZSTEP, GPIO.HIGH)
        time.sleep(delay)    
        GPIO.output(ZSTEP, GPIO.LOW)        
        
    
    if direction == ZFORWARD: #totally arbitrary 
        GlobalZ += numsteps
    else:
        GlobalZ -= numsteps
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))

def ZGoTo(ZDest, ZMin=0):
    """checks the place is valid and then calls MoveZ appropriately.
    """
    
    global GlobalZ
    global ZMax
    if not isinstance(ZDest,int):
        return ('integers only dingus') #this is not good practice right
        
    if ZDest <= ZMax and ZDest >= ZMin:
        numsteps = ZDest - GlobalZ
        if numsteps > 0: #forward
            MoveZ(ZFORWARD,numsteps,FASTERER)
        else:
            MoveZ(ZBACKWARD,abs(numsteps),FASTERER) 
    else:
        print ('Destination out of range')

def ZGet(event):
    '''records enter press from text box (ZEntry) and calls "go to specified location function'''
    try:
        ZDest = int(event.widget.get())
        ZGoTo(ZDest)
    except ValueError: #hey dumbo enter an integer
        print ("hey dumbo enter an integer")    


def CheckPress(PIN):
    '''checks whether specified GPIO pin has been pressed, since home procedures have to call multiple times'''
    input_state = GPIO.input(PIN)
    if input_state == False: #button press
            time.sleep(0.05) #debounce
            input_state = GPIO.input(PIN)
            if input_state == False: #still!
                return True #yep, button press
            
def HomeX():
    global GlobalX
    for i in range(XMax + 500): #some number that's noticably larger than the range, but also will eventually stop in case something goes wrong 
    
    #check if button is pressed
        
        
        if CheckPress(XLimit): #button pressed once. need to move forward and back again to ensure correct start position
            MoveX(1,300,FASTER) #move forward
            for j in range(400): #move back and check again
                if CheckPress(XLimit): #again
                    
                
                    print('Button has been pressed after {} steps!'.format(i))
                    print('was already homed check: took {} out of 300 steps on the second bounce'.format(j))
                    GlobalX = 0
                    XPosition.configure(text="X: " +str(GlobalX) + "/" + str(XMax))
                    return (i) #break away essentially
                MoveX(0,1,SLOW)
            #do stepping protocol (second in case button already pressed)
        MoveX(0,1,FAST)#dir dis delay

def HomeY():
    global GlobalY
    for i in range(YMax + 500): #some number that's noticably larger than the range, but also will eventually stop in case something goes wrong 
    
    #check if button is pressed
        
        
        if CheckPress(YLimit): #button pressed once. need to move forward and back again to ensure correct start position
            MoveY(YFORWARD,300,FASTER) #move forward
            for j in range(400): #move back and check again
                if CheckPress(YLimit): #again
                    
                
                    print('Button has been pressed after {} steps!'.format(i))
                    print('was already homed check: took {} out of 300 steps on the second bounce'.format(j))
                    GlobalY = 0
                    YPosition.configure(text="Y: "+str(GlobalY) + "/" + str(YMax))
                    return (i) #break away essentially
                MoveY(YBACKWARD,1,SLOW)
            #do stepping protocol (second in case button already pressed)
        MoveY(YBACKWARD,1,FAST)#dir dis delay

def HomeZ():
    global GlobalZ
    
    for i in range(ZMax + 500): #some number that's noticably larger than the range, but also will eventually stop in case something goes wrong 
    
    #check if button is pressed
        
    
        if CheckPress(ZLimit): #button pressed once. need to move forward and back again to ensure correct start position
            MoveZ(ZFORWARD,300,FAST) #move forward -- at least 1k b/c neg range
            for j in range(400): #move back and check again
                if CheckPress(ZLimit): #again
                    

                    print('Z switch has been tripped after {} steps!'.format(i))
                    print('was already homed check: took {} out of 300 steps on the second bounce'.format(j))
                    
                    
                    GlobalZ = 0
                    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))
                    return (i) #break away essentially
                MoveZ(ZBACKWARD,1,FAST)
            #do stepping protocol (second in case button already pressed)
        MoveZ(ZBACKWARD,1,FASTERER)#dir dis delay  



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
    MoveR(RFORWARD, 8, SLOW)
    print("You rotated something clockwise a bit!")
    
def MoveRCCWSmall(): #counterclockwise
    MoveR(RBACKWARD, 8, SLOW)
    print("You rotated something counterclockwise a bit!")
    
def exitProgram():
    print("Exit Button pressed")
    GPIO.cleanup() 
    win.quit()

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

SecondaryBottomFrame = tk.Frame(BottomFrame)
SecondaryBottomFrame.pack(side=tk.TOP)

#Display analog value of PD
AnalogValue = tk.Label(SecondaryBottomFrame, font=(myFont), height = 2, width=12)
AnalogValue.after(1000, AnalogGet)
AnalogValue.pack(side = tk.TOP)

"""begin resume scan if failed"""


try:
    GPIO.output(BEEP,GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(BEEP,GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(BEEP,GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(BEEP,GPIO.LOW)
    
    LaserTest = DefineScan(1100,1300,600,800,0,0,0,0,20,20) #placed in a random location so it will get lost

    
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


    