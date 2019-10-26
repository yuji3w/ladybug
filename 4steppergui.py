#!/usr/bin/env python3

from numpy import * #for generating scan parameters
import random #for repeatability tests
import time
import math
import os
import tkinter as tk #contains GUI, can be removed if converted to headless
from tkinter import font
from tkinter import filedialog
import RPi.GPIO as GPIO
import subprocess #For taking a picture with fswebcam
import sys
import select #for timeouts and buzzing when usb gets disconnect
import pickle #for saving scan data and resuming

GPIO.setmode(GPIO.BOARD) #IMPORTANT! Physical pin layout

#Distances from home position in steps for each motor. 
#Starts at "0" so if you don't have any switches just move them there before running the program. 

GlobalX = 0 #"Top" motor
GlobalY = 0 #"Bottom" motor
GlobalZ = 0 #up and down
GlobalR = 0 #Rotation. 

#These are scan parameters intended to be set by the GUI and can otherwise be ignored
XScanMin = 0
XScanMax = 0
YScanMin = 0
YScanMax = 0
ZScanMin = 0
ZScanMax = 0
XScanStep = 100 #amount of motion (in steps) in each dimension in the scan 
YScanStep = 100 #reasonable default for field of view. Can scretch to 150 for faster scans.
ZScanStep = 500 
RScanNumber = 1 #number of rotations per scan, 1 = no rotation

FactorsOf160 = [1,2,4,5,8,10,16,20,32,40,80,160] #for drop down menu of rotations of R since 20 step motor with 8th micro
 
#begin defining pins for input and output (GPIO.BOARD). These can be changed to fit your setup.

YDIR = 26 #Sample AKA bottom direction pin
XDIR = 18 #Camera AKA top
ZDIR = 40 
RDIR = 19 

YSTEP = 24 #Stepping pins
XSTEP = 16
ZSTEP = 38
RSTEP = 23

BEEP = 33 #GPIO pin to beep for indications (thanks Yujie). Can also put an LED here or something else

XLimit = 7 #Mechanical limitswitch pin input
YLimit = 13
ZLimit = 15 #Optical switch pin input!


XMax = 1800 #max range in 8th microsteps. Affected by choice of carriage
YMax = 1800
ZMax = 3000
StepsPerRotation = 160 #for 8th microstepping on the R axis we have

XFORWARD = 1 #Arbitrary, can flip around if motors go in wrong direction
XBACKWARD = 0   

YFORWARD = 1 
YBACKWARD = 0

ZFORWARD = 1
ZBACKWARD = 0

RFORWARD = 1 #Consider forward as clockwise if looking at your sample if referenced
RBACKWARD = 0

#preset speeds, defined as delay between steps in s.

FASTERER = 0.0003
FASTER = 0.0006
FAST = 0.002 
SLOW = 0.007
SLOWER = 0.03
SLOWERER = 0.06

#Begin GPIO output setup

GPIO.setup(BEEP, GPIO.OUT)
GPIO.setup(XDIR, GPIO.OUT)
GPIO.setup(YDIR, GPIO.OUT)
GPIO.setup(ZDIR, GPIO.OUT)
GPIO.setup(RDIR, GPIO.OUT)
GPIO.setup(XSTEP, GPIO.OUT)
GPIO.setup(YSTEP, GPIO.OUT)
GPIO.setup(ZSTEP, GPIO.OUT)
GPIO.setup(RSTEP, GPIO.OUT)

#GPIO input setup for limit switches
GPIO.setup(YLimit, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(XLimit, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(ZLimit, GPIO.IN) #no pull up! Direct sense with optical switch.


#Start Tkinter GUI window. More Tkinter way below. 
#May fork to a headless version of this with all Tkinter stuff removed,
#Since I think it adds a lot of bloat and not too much benefit.

win = tk.Tk()
myFont = tk.font.Font(family='Helvetica', size=12, weight='bold')
myBigFont = tk.font.Font(family='Helvetica', size=20,weight='bold')
font.families()


#BEGIN ACTUAL CODE

def restart(): #restart whole pi
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

def MoveX(direction,numsteps,delay):
    '''parent function for moving x. Just sets direction pin,
    then flips step pin high and low with delay  '''
    
    GPIO.output(XDIR, direction)
        
    for i in range(numsteps):
            
            GPIO.output(XSTEP, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(XSTEP, GPIO.LOW)
    
    global GlobalX
    
    if direction == XForward:
        GlobalX += numsteps
    else:
        GlobalX -= numsteps
    
    XPosition.configure(text="X: "+str(GlobalX) + "/" + str(XMax)) 
    #updates the global position on the screen. Get rid of this if headless!
    
def XGoTo(XDest, XMin=0):
    """checks if the place is valid and then calls MoveX appropriately.
    Should stop you from going across boundaries."""
  
    global GlobalX
    global XMax
    
    if not isinstance(XDest,int):
        return ('Please input an integer for X destination') #why you so stupid, stupid
        
    if XDest <= XMax and XDest >= XMin:
        distance = XDest - GlobalX
        if distance > 0: #forward
            MoveX(XFORWARD,distance,FASTER)
        else:
            MoveX(XBACKWARD,abs(distance),FASTER) 
    else:
        print ('Destination out of range')

def MoveY(direction,numsteps,delay):
    '''parent function for Y. '''
    
    GPIO.output(YDIR, direction)    
        
    for i in range(numsteps):
            
        GPIO.output(YSTEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(YSTEP, GPIO.LOW)        
    
    global GlobalY
    
    if direction == YForward:  
        GlobalY += numsteps
    else:
        GlobalY -= numsteps
    YPosition.configure(text="Y: "+str(GlobalY) + "/" +str(YMax)) #REMOVE IF CONVERTING TO HEADLESS WITHOUT GUI
    
def YGoTo(YDest, YMin=0):
    """checks the place is valid and then calls MoveY appropriately."""
  
    global GlobalY
    global YMax
    if not isinstance(YDest,int):
        return ('Please input an integer for Y destination')
        
    if YDest <= YMax and YDest >= YMin:
        distance = YDest - GlobalY
        if distance > 0: #forward
            MoveY(YFORWARD,distance,FASTER)
        else:
            MoveY(YBACKWARD,abs(distance),FASTER) 
    else:
        print ('Destination out of range')

def MoveZ(direction,numsteps,delay):
    '''parent function for Z. This version has no sleep pin enable/disable:
    Be careful to use a low voltage and amount of current! Otherwise small motors like this will get hot!'''
    
    GPIO.output(ZDIR, direction)
    global GlobalZ
         
    for i in range(numsteps):
            
        GPIO.output(ZSTEP, GPIO.HIGH)
        time.sleep(delay)    
        GPIO.output(ZSTEP, GPIO.LOW)        
        
    
    if direction == ZFORWARD: 
        GlobalZ += numsteps
    else:
        GlobalZ -= numsteps
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/" + str(ZMax))

def ZGoTo(ZDest, ZMin=0):
    """checks the place is valid and then calls MoveZ appropriately.
    At the home position there happens to be just about 2000 steps
    forward and 1000 steps back --- for 1 micron per step."""
    
    global GlobalZ
    global ZMax
    
    if not isinstance(ZDest,int):
        return ('Please input an integer for Z destination')
        
    if ZDest <= ZMax and ZDest >= ZMin:
        numsteps = ZDest - GlobalZ
        if numsteps > 0: #forward
            MoveZ(ZFORWARD,numsteps,FASTERER)
        else:
            MoveZ(ZBACKWARD,abs(numsteps),FASTERER) 
    else:
        print ('Destination out of range')

def MoveR(direction,numsteps,delay):

    GPIO.output(RDIR, direction)
    global GlobalR
    
    for i in range(numsteps):
        GPIO.output(RSTEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(RSTEP,GPIO.LOW)
    
    '''Count information like the others could be inserted here. 
    But we don't really have a way to define our "zero", except for wherever it is when we start the scan,
    which is problematic because what if we restart with our R in a different place? 
    If there are undiscovered problems, I think they would revolved around this area. FYI. '''

def RGoTo(RDest, RMin=0):
    """checks that it's within the proper range and calls MoveR. Note that I just added this because I noticed it was missing. 
    Not sure where it went or if I never made it for some reason, but then how was everything working...?"""
  
    global GlobalR
    global StepsPerRotation
    
    if not isinstance(RDest,int):
        return ('Please input an integer for R destination')
        
    if RDest <= StepsPerRotation and RDest >= RMin:
        distance = RDest - GlobalR
        if distance > 0: #forward
            MoveR(RFORWARD,distance,FAST)
        else:
            MoveR(RBACKWARD,abs(distance),FAST) 
    else:
        print ('I understand the desire to watch the motor spin around a lot... but between {} and {} please'.format(RMin,StepsPerRotation))
              
   
def DefineScan(XMin, XMax, YMin, YMax, ZMin, ZMax, RMin, RMax, XSteps=100, YSteps=100, ZSteps=1, RSteps=1):
    """
    Used to generate a dictionary with four keys, each of which maps to a list containing
    the absolute positions of X,Y,Z, and R, for every point of a scan.
    So if you don't want to move Z and R, just for instance set Zmin=Zmax=0 and ZSteps = 1.
 
    Core, of 2-axis control, from stack exchange. https://stackoverflow.com/questions/20872912/raster-scan-pattern-python
    
    """
    
    XMax = XMax+1 #its not inclusive in max and will break if min = max, so we add 1 to all maximums.
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
    my own code to account for Z now. Not efficient if there are a LOT of Z changes 
    (it does X/Y rastering and returns to initial position for each change in Z). Otherwise it's fine.    
    
    """
    
    NewXScan = []
    NewYScan = []
    NewZScan = []
    
    
    for i in range(len(zgrid)):
        for j in range(len(xscan)):
        
            NewXScan.append(xscan[j])
            NewYScan.append(yscan[j])
            NewZScan.append(zgrid[i]) #note i not j
        
    #Repeat for change in rotation

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


def GridScan(ScanLocations,conditions='default'):
 
 """the main loop that carries out an actual scan. Accepts the dictionary output of DefineScan, and an optional dictionary of conditions,
 which is necessary when performing a restart in the middle of the scan. """
     
    XCoord = ScanLocations['X'] #simple list of axis location at each point in scan
    YCoord = ScanLocations['Y']
    ZCoord = ScanLocations['Z']
    RCoord = ScanLocations['R']
    
    start_time = time.time()
    
    if conditions == 'default': #usually the case!
        save_location = filedialog.askdirectory() #pop up screen asking where to save files like flash drive
        filetype = ".png" #jpgs are honestly ok too and might make things easier/faster
        resolution = "640x480" #for crappy microscope, not necessarily reliable, though
        timeallowed = 30 #number of seconds you have to save the scan if the USB is failing before auto restart!
        num_failures = 0 #times restarted so far
        original_pics = len(XCoord) 
        original_time = start_time
        original_locations = ScanLocations
        failed_pics=[] #keeps track of which pic we were on when restart happens
        failure_times=[] #keeps track of when failure happens
        
    else: #generally, inputted automatically after a restart
        save_location = conditions['save_location']
        filetype = conditions['filetype']
        resolution = conditions['resolution']
        timeallowed=0 #after one restart we don't bother trying to save scan.
        num_failures=conditions['num_failures']
        failed_pics=conditions['failed_pics']
        failure_times=conditions['failure_times']
        original_pics=conditions['original_pics']
        original_time=conditions['original_time']
        original_locations=conditions['original_locations']
        
    num_pictures = len(XCoord) #remaining pics, not originally
    NumberOfRotations = len(set(RCoord)) #1 means no rotation
    stepsPerRotation = ((max(RCoord)-min(RCoord))/len(set(RCoord)))
    
    print("Stepping {} per image".format(str(StepsPerRotation))) #for debugging
    print("has failed and restarted {} times so far".format(str(num_failures)))
    
    #Initialize locations
    
    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    ZGoTo(int(ZCoord[0]))
    RGoTo(int(RCoord[0]))
    
    
        
    for i in range(num_pictures):
        
        #beep!
        if i % 100 == 0: #Should be percentage of remaining but this is ok
            print("{} of {} pictures remaining".format((num_pictures-i),original_pics))
            GPIO.output(BEEP,GPIO.HIGH) 
            time.sleep(0.3) #can eliminate if you're pinching seconds
            GPIO.output(BEEP,GPIO.LOW)
            
        #make new folder every time you change Z and R:
        folder = save_location + "/Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3) 
        if not os.path.exists(folder):
            os.makedirs(folder)
                
            
        #go to locations                    
        XGoTo(int(XCoord[i]))
        YGoTo(int(YCoord[i]))
        ZGoTo(int(ZCoord[i]))
        RGoTo(int(RCoord[i]))
            
        time.sleep(0.1) #VIBRATION CONTROL! 
               
            
            
        name = "X" + str(XCoord[i]).zfill(4) + "Y" + str(YCoord[i]).zfill(4) + "Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3) + "of" + str(NumberOfRotations).zfill(3) + filetype

        """begin filesaving block"""
        
        try: #Largely, problems are due to USB disconnecting or just not being in.
            for w in range(3): #try to take pic with fswebcam
                
                proc = subprocess.Popen(["fswebcam", "-r " + resolution, "--no-banner", folder + "/" + name, "-q"], stdout=subprocess.PIPE) #like check_call(infinite timeout)
                output = proc.communicate(timeout=10)[0]
                
                if os.path.isfile(folder + "/" + name): #check if file was created 
                    if w > 0: #AKA, USB was broken but fixed in time
                        print ('Okay thanks bozo. Restarting with {}'.format(name))
                        
                    break #move on to next picture
                
                elif (w <= 1): #usb got unplugged aaaaggghhhhh
                
                    #attempt to catch USB from https://stackoverflow.com/questions/1335507/keyboard-input-with-timeout-in-python  
                    print('HEY BOZO THE USB GOT UNPLUGGED UNPLUG IT AND PLUG IT BACK IN WITHIN {} SECONDS OR WE REBOOT'.format(timeallowed))
                    print('check if {} failed'.format(name))
                
                    GPIO.output(BEEP,GPIO.HIGH) #beep and bibrate
                
                    time.sleep(timeallowed) #Sorry, it will beep the full time, even if you restart it immediately
                
                    GPIO.output(BEEP,GPIO.LOW)
                
                else: #Begin saving current scan data for restart. This could be reworked for periodic backup
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
                    print(scan_params) #for debugging if sitting there
                    time.sleep(2)
                    
                    scan_file = open('/home/pi/Desktop/ladybug/scandata.pkl', 'wb') #SCAN DATA LOCATION HARDCODED ONTO DESKTOP
                    #Sorry about this, but it's because the auto restart cron script needs to know where to look. 
                         
                    pickle.dump(scan_params,scan_file)
                    scan_file.close()
                    
                    print('restarting sorryyyyyy')
                        
                    restart()
                        
        except subprocess.TimeoutExpired: #does not catch USB UNPLUG. Catches if it takes too long because of lag. Rarely happens
    
            print ("{} failed :( ".format(name))
            proc.terminate() #corrective measure?
            continue #move on. In true loop, it keeps trying the same picture since it shouldn't matter which one

            
            
    print ('scan completed successfully after {} seconds! {} images taken and {} restarts'.format
           (time.strftime("%H:%M:%S", time.gmtime(time.time() - original_time)), str(original_pics),str(num_failures)))
    try:
        os.rename('/home/pi/Desktop/ladybug/scandata.pkl','/home/pi/Desktop/ladybug/scandataold.pkl') 
      #if you don't rename this, it can form an infinite loop! Should rename to reflect scan data or something
    except FileNotFoundError: #meaning it never restarted and created scandata file
        pass
    
    for i in range(5): #beep beep beep beep beep
        GPIO.output(BEEP,GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BEEP,GPIO.LOW)

    a = input('press any key to exit') #hang to await confirmation scan completed if run in autoclosing shell

#end main scan procedure. 
    
def XRepeatTest(num_trials=100):
    """this will move a lot and then home, to check to make sure we're not skipping steps or something. 
    You can probably ignore this. """
  
    HomeX()
    HomeX() #twice just to make sure it's good
    HomeX() #one more for good luck? 
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
    #same as X, you can probably ignore this or even remove entirely
  
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
    """calls y and x repeat many many times with random numbers so we can plot stuff"""
    X_History = [] #populated with list of lists. 
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
    for i in range(2500): #some number that's noticably larger than the range, but also will eventually stop in case something goes wrong 
    
    #check if button is pressed
        
        
        if CheckPress(XLimit): #button pressed once. need to move forward and back again to ensure correct start position
            MoveX(1,300,0.01) #move forward
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
    for i in range(2500): #some number that's noticably larger than the range, but also will eventually stop in case something goes wrong 
    
    #check if button is pressed
        
        
        if CheckPress(YLimit): #button pressed once. need to move forward and back again to ensure correct start position
            MoveY(YFORWARD,300,SLOW) #move forward
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
    
    for i in range(2500): #some number that's noticably larger than the range, but also will eventually stop in case something goes wrong 
    
    #check if button is pressed
        
    
        if CheckPress(ZLimit): #button pressed once. need to move forward and back again to ensure correct start position
            MoveZ(ZFORWARD,1200,FAST) #move forward -- at least 1k b/c neg range
            for j in range(1400): #move back and check again
                if CheckPress(ZLimit): #again
                    
                    MoveZ(ZBACKWARD, 1000, FAST) #START AT MINIMUM RANGE for easier calculating

                    print('Optical switch has been tripped after {} steps!'.format(i))
                    print('was already homed check: took {} out of 1200 steps on the second bounce'.format(j))
                    
                    
                    GlobalZ = 0
                    ZPosition.configure(text="Z: "+str(GlobalZ) + "/3000")
                    return (i) #break away essentially
                MoveZ(ZBACKWARD,1,FAST)
            #do stepping protocol (second in case button already pressed)
        MoveZ(ZBACKWARD,1,FAST)#dir dis delay

def GuiScan():
    
    
    
    GridScan(XScanMin,XScanMax,YScanMin,YScanMax,ZScanMin,ZScanMax,XScanStep,YScanStep,ZScanStep,RScanNumber)
    

def SetR():
    #gets entry from dropdown for rotations and passes to global variable 
    global RScanNumber
    RScanNumber = int(RSetVar.get())
    print ('viewing {} points of view'.format(str(RScanNumber)))
    


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

def SetXLowerBound():
    global XScanMin
    XScanMin = GlobalX
    print("Lower Boundary for X Scan has been set to {}".format(XScanMin))

def SetXUpperBound():
    global XScanMax
    XScanMax = GlobalX
    print("Upper Boundary for X Scan has been set to {}".format(XScanMax))


def SetYLowerBound():
    global YScanMin
    YScanMin = GlobalY
    print("Lower Boundary for Y Scan has been set to {}".format(YScanMin))

def SetYUpperBound():
    global YScanMax
    YScanMax = GlobalY
    print("Upper Boundary for Y Scan has been set to {}".format(YScanMax))

def SetZLowerBound():
    #sets Z bound to whatever global Z is
    global ZScanMin
    ZScanMin = GlobalZ
    print("Lower Boundary for Z Scan has been set to {}".format(ZScanMin))

def SetZUpperBound():
    global ZScanMax
    ZScanMax = GlobalZ
    print("Upper Boundary for Z Scan has been set to {}".format(ZScanMax))

def SetZStep():
    global ZScanStep
    ZScanStep = GlobalZ #Yes I know I should be shot but this makes it more minimal
    print("Step size for Z has been set to {}".format(ZScanStep))

def SetXStep():
    global XScanStep
    XScanStep = GlobalX
    print("Step size for X has been set to {}".format(YScanStep))
    
def SetYStep():
    global YScanStep
    YScanStep = GlobalY
    print("Step size for Y has been set to {}".format(YScanStep))

#Begin disgusting block of instructions for keypress. Complicated by fact we want to be able to hold Down.
#Modified from https://stackoverflow.com/questions/12994796/how-can-i-control-keyboard-repeat-delay-in-a-tkinter-root-window
#main changes are not displaying the Label and also only enabling key control when checkbox is checked (allow_keypress)


def LeftStep(*event): #X
    MoveYForwardSmall()
    #pyrint('Left')

    if LeftLabel._repeat_on:
        win.after(LeftLabel._repeat_freq, LeftStep)

def LeftStop(*event):
    if LeftLabel._repeat_on:
        LeftLabel._repeat_on = False
        win.after(LeftLabel._repeat_freq + 1, LeftStop)
    else:
        LeftLabel._repeat_on = True


def RightStep(*event):
    MoveYBackSmall()

    if RightLabel._repeat_on:
        win.after(RightLabel._repeat_freq, RightStep)

def RightStop(*event):
    if RightLabel._repeat_on:
        RightLabel._repeat_on = False
        win.after(RightLabel._repeat_freq + 1, RightStop)
    else:
        RightLabel._repeat_on = True


def UpStep(*event):
    MoveXLeftSmall()

    if UpLabel._repeat_on:
        win.after(UpLabel._repeat_freq, UpStep)

def UpStop(*event):
    if UpLabel._repeat_on:
        UpLabel._repeat_on = False
        win.after(UpLabel._repeat_freq + 1, UpStop)
    else:
        UpLabel._repeat_on = True

def DownStep(*event):
    MoveXRightSmall()

    if DownLabel._repeat_on:
        win.after(DownLabel._repeat_freq, DownStep)

def DownStop(*event):
    if DownLabel._repeat_on:
        DownLabel._repeat_on = False
        win.after(DownLabel._repeat_freq + 1, DownStop)
    else:
        DownLabel._repeat_on = True

def AStep(*event): #note actual lowercase. FOr clock and counterclockwise rotation
    MoveRCCWSmall()

    if ALabel._repeat_on:
        win.after(ALabel._repeat_freq, AStep)

def AStop(*event):
    if ALabel._repeat_on:
        ALabel._repeat_on = False
        win.after(ALabel._repeat_freq + 1, AStop)
    else:
        ALabel._repeat_on = True

def DStep(*event): #note actual lowercase. FOr clock and counterclockwise rotation
    MoveRCWSmall()

    if DLabel._repeat_on:
        win.after(DLabel._repeat_freq, DStep)

def DStop(*event):
    if DLabel._repeat_on:
        DLabel._repeat_on = False
        win.after(DLabel._repeat_freq + 1, DStop)
    else:
        DLabel._repeat_on = True

def WStep(*event): #note actual lowercase. For Z AXIS W and S
    MoveZUpSmall()

    if WLabel._repeat_on:
        win.after(WLabel._repeat_freq, WStep)

def WStop(*event):
    if WLabel._repeat_on:
        WLabel._repeat_on = False
        win.after(WLabel._repeat_freq + 1, WStop)
    else:
        WLabel._repeat_on = True

def SStep(*event): #note actual lowercase. For Z AXIS S and S
    MoveZDownSmall()

    if SLabel._repeat_on:
        win.after(SLabel._repeat_freq, SStep)

def SStop(*event):
    if SLabel._repeat_on:
        SLabel._repeat_on = False
        win.after(SLabel._repeat_freq + 1, SStop)
    else:
        SLabel._repeat_on = True


def allow_keypress():
    #Checks if button is presed, if so, allows keycontrol
    
    if keypress_var.get(): #I can't believe this works. Button is pressed
        
        
        global Leftbound
        global Leftunbound
        global Rightbound
        global Rightunbound
        global Upbound
        global Upunbound
        global Downbound
        global Downunbound
        global Abound
        global Aunbound
        global Dbound
        global Dunbound
        global Wbound
        global Wunbound
        global Sbound
        global Sunbound
        
        
        
        
        Leftbound = win.bind('<KeyPress-Left>', LeftStep)
        Leftunbound = win.bind('<KeyRelease-Left>', LeftStop)
        Rightbound = win.bind('<KeyPress-Right>', RightStep)
        Rightunbound = win.bind('<KeyRelease-Right>', RightStop)
        Upbound = win.bind('<KeyPress-Up>', UpStep)
        Upunbound = win.bind('<KeyRelease-Up>', UpStop)
        Downbound = win.bind('<KeyPress-Down>', DownStep)
        Downunbound = win.bind('<KeyRelease-Down>', DownStop)
        Abound = win.bind('<KeyPress-a>', AStep)
        Aunbound = win.bind('<KeyRelease-a>', AStop)
        Dbound = win.bind('<KeyPress-d>', DStep)
        Dunbound = win.bind('<KeyRelease-d>', DStop)
        Wbound = win.bind('<KeyPress-w>', WStep)
        Wunbound = win.bind('<KeyRelease-w>', WStop)
        Sbound = win.bind('<KeyPress-s>', SStep)
        Sunbound = win.bind('<KeyRelease-s>', SStop)
        
    else:
        win.unbind('<KeyPress-Left>', Leftbound)
        win.unbind('<KeyRelease-Left>', Leftunbound)
        win.unbind('<KeyPress-Right>', Rightbound)
        win.unbind('<KeyRelease-Right>', Rightunbound)
        win.unbind('<KeyPress-Up>', Upbound)
        win.unbind('<KeyRelease-Up>', Upunbound)
        win.unbind('<KeyPress-Down>', Downbound)
        win.unbind('<KeyRelease-Down>', Downunbound)
        win.unbind('<KeyPress-a>', Abound)
        win.unbind('<KeyRelease-a>', Aunbound)   
        win.unbind('<KeyPress-d>', Dbound)
        win.unbind('<KeyRelease-d>', Dunbound)   
        win.unbind('<KeyPress-w>', Wbound)
        win.unbind('<KeyRelease-w>', Wunbound)   
        win.unbind('<KeyPress-s>', Sbound)
        win.unbind('<KeyRelease-s>', Sunbound)

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

XStepButton = tk.Button(LeftFrame, text = "Set XScan Stepsize ", font = myFont, command = SetXStep, height = 1, width =20 )
XStepButton.pack(side = tk.TOP, pady=5)
XLowerBoundButton = tk.Button(LeftFrame, text = "Set XScan Min", font = myFont, command = SetXLowerBound, height = 1, width =20 )
XLowerBoundButton.pack(side = tk.TOP, pady=5)
XUpperBoundButton = tk.Button(LeftFrame, text = "Set XScan Max", font = myFont, command = SetXUpperBound, height = 1, width =20 )
XUpperBoundButton.pack(side = tk.TOP, pady=5)

YStepButton = tk.Button(TopFrame, text = "Set YScan Stepsize ", font = myFont, command = SetYStep, height = 1, width =20 )
YStepButton.pack(side = tk.BOTTOM, pady=5)
YUpperBoundButton = tk.Button(TopFrame, text = "Set YScan Max ", font = myFont, command = SetYUpperBound, height = 1, width =20 )
YUpperBoundButton.pack(side = tk.BOTTOM, pady=5)
YLowerBoundButton = tk.Button(TopFrame, text = "Set YScan Min ", font = myFont, command = SetYLowerBound, height = 1, width =20 )
YLowerBoundButton.pack(side = tk.BOTTOM, pady=5)




ZStepButton = tk.Button(RightFrame, text = "Set ZScan Stepsize ", font = myFont, command = SetZStep, height = 1, width =20 )
ZStepButton.pack(side = tk.TOP, pady=5)
ZLowerBoundButton = tk.Button(RightFrame, text = "Set ZScan Min ", font = myFont, command = SetZLowerBound, height = 1, width =20 )
ZLowerBoundButton.pack(side = tk.TOP, pady=5)
ZUpperBoundButton = tk.Button(RightFrame, text = "Set ZScan Max ", font = myFont, command = SetZUpperBound, height = 1, width =20 )
ZUpperBoundButton.pack(side = tk.TOP, pady=5)



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

ScanButton = tk.Button(BottomFrame, text = "SCAN!!!", font = myBigFont, command = GuiScan, height = 1, width = 20)
ScanButton.pack(side = tk.TOP, pady=110)

SecondaryBottomFrame = tk.Frame(BottomFrame)
SecondaryBottomFrame.pack(side=tk.TOP)

RSetVar = tk.StringVar(SecondaryBottomFrame) #holds contents of dropdown? 
RSetVar.set(FactorsOf160[0])
RSetButton = tk.Button(SecondaryBottomFrame, text = "Set number of rotations", font = myFont, command = SetR, height = 1, width = 20)
RSetButton.pack(side = tk.LEFT, padx=5)
RSetDropdown = tk.OptionMenu(SecondaryBottomFrame, RSetVar, *FactorsOf160)
RSetDropdown.pack(side = tk.RIGHT, padx=5)

keypress_var = tk.IntVar() #1 if button is pressed
keypress_button = tk.Checkbutton(SecondaryBottomFrame, text="ENABLE KEYBOARD CONTROLS", variable=keypress_var, command=allow_keypress)
keypress_button.pack(side = tk.RIGHT)


LeftLabel = tk.Label(win)
LeftLabel._repeat_freq = int(SLOW*1000*10) #holding Down key, milisecond per repeat.. Delay should be how long it actually takes to move
LeftLabel._repeat_on = True

RightLabel = tk.Label(win)
RightLabel._repeat_freq = int(SLOW*1000*10) 
RightLabel._repeat_on = True

UpLabel = tk.Label(win)
UpLabel._repeat_freq = int(SLOW*1000*10) 
UpLabel._repeat_on = True

DownLabel = tk.Label(win)
DownLabel._repeat_freq = int(SLOW*1000*10)  
DownLabel._repeat_on = True

ALabel = tk.Label(win) #a nd d are rotation
ALabel._repeat_freq = int(SLOW*1000*10)  
ALabel._repeat_on = True

DLabel = tk.Label(win)
DLabel._repeat_freq = int(SLOW*1000*10)  
DLabel._repeat_on = True

WLabel = tk.Label(win)
WLabel._repeat_freq = int(SLOW*1000*10)  
WLabel._repeat_on = True

SLabel = tk.Label(win)
SLabel._repeat_freq = int(SLOW*1000*10)  
SLabel._repeat_on = True


"""BEGIN MAIN LOOP, beginning with an attempt to resume scan if it detects that a previous one failed 
(existence of scandata file)"""


try:
    GPIO.output(BEEP,GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(BEEP,GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(BEEP,GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(BEEP,GPIO.LOW)
    
    
    scan_file = open('/home/pi/Desktop/ladybug/scandata.pkl', 'rb')
        
    scan_params = pickle.load(scan_file)
    scan_file.close()    
            
    HomeX() 
    HomeY()
    HomeZ()
    
    locations = scan_params[0] #position data
    conditions = scan_params[1] #save location, filetype, resolution, timeout, numfailures
    
    """because R has no endstop we have to set it to what it was in the scan"""
    #global GlobalR #I'm not sure why this causes a syntax error, it wasn't before. 
    GlobalR = conditions['R_Location'] #I'm worried that pins would flip here during restart. Likely a source of error
    
    GridScan(locations,conditions)
    
except FileNotFoundError:
        
    print('No interrupted scans found. Welcome.')


    
