
from numpy import *
import random
import time
import math
import os
from tkinter import font
import tkinter as tk
import RPi.GPIO as GPIO
import subprocess #For taking a picture with fswebcam
import pygame #will be replace with opencv stuff. EFF YOU PYGAME
import pygame.camera

from pygame.locals import *

pygame.init()

GPIO.setmode(GPIO.BOARD)

GlobalX = 0 #X distance from home in steps
GlobalY = 0
GlobalZ = 0
GlobalR = 0 #keep same naming scheme, but R = rotation


#These are set by the GUI and passed off to scan configuration
XScanMin = 0
XScanMax = 0
YScanMin = 0
YScanMax = 0
ZScanMin = 0
ZScanMax = 0
XScanStep = 0
YScanStep = 0
ZScanStep = 0
RScanNumber = 0

FactorsOf160 = [1,2,4,5,8,10,16,20,32,40,80,160] #for drop down menu of rotations of R


YDIR = 26 #SAMPLE
XDIR = 18 #CAMERA
ZDIR = 40
RDIR = 19 #for clock and counterclock

YSTEP = 24 #stepping pin 
XSTEP = 16
ZSTEP = 38
RSTEP = 23

BEEP = 33 #GPIO pin to beep for pleasing yujie

XMax = 1800 #max range. Affected by choice of sled
YMax = 1800
StepsPerRotation = 160 #for 8th microstepping on the R axis we have

XLimit = 7 #limit switch pin input
YLimit = 13
ZLimit = 15 #optical switch. Goes low but there is a transition

ZSleep = 31 #Low, Z is OFF. High, it is ON. Currently unused

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
GPIO.setup(ZLimit, GPIO.IN) #no pull up. Direct sense

#GPIO.setup(XENABLE, GPIO.OUT)
#GPIO.setup(YENABLE, GPIO.OUT)
GPIO.setup(ZSleep, GPIO.OUT) #low off high ON

#GPIO.output(YENABLE, GPIO.HIGH)
#GPIO.output(XENABLE, GPIO.HIGH)


win = tk.Tk()
myFont = tk.font.Font(family='Helvetica', size=12, weight='bold')
myBigFont = tk.font.Font(family='Helvetica', size=20,weight='bold')
font.families()

def DefineScan(XMin, XMax, YMin, YMax, XSteps=100, YSteps=100):
    """core from stack exchange. https://stackoverflow.com/questions/20872912/raster-scan-pattern-python"""
    
    # define some grids
    xgrid = arange(XMin, XMax,XSteps) 
    ygrid = arange(YMin, YMax,YSteps)

    xscan = []
    yscan = []

    for i, yi in enumerate(ygrid):
        xscan.append(xgrid[::(-1)**i]) # reverse when i is odd
        yscan.append(ones_like(xgrid) * yi)   

    # squeeze lists together to vectors
    xscan = concatenate(xscan)
    yscan = concatenate(yscan)

    return(xscan,yscan)

def GridScan(XMin=0,XMax=1000,YMin=0,YMax=1000,ZMin = GlobalZ,ZMax=GlobalZ,XSteps=100,YSteps=100, ZSteps=1,NumberOfRotations = 1):
    '''Does the actual THREEd moving for a scan. Default Zmin to Zmax set up to only take one picture (current Z value). Pretty hacky.
If you want to rotate but not z step, set steps to 1 and max and min to the Z height you want to scan.

This one uses the original 2d raster scan from stack. 
'''
    XYCoord = DefineScan(XMin,XMax+1,YMin,YMax+1,XSteps,YSteps)
    
    
    '''ADD ONE BECAUSE HALF INTERVAL and people often round to whole numbers.
    
    '''
    XCoord = XYCoord[0]
    YCoord = XYCoord[1]
    ZCoord = list(arange(ZMin, ZMax+1, ZSteps)) #again add one because people often round and you want at least 1
    
    filetype = ".jpg"
    num_pictures = len(XCoord)*len(ZCoord)*NumberOfRotations
    
    StepsPerImage = int(160/NumberOfRotations)
    
    #generate Z positions
    
    
    # goto start position
    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    ZGoTo(int(ZCoord[0]))
    
    start_time = time.time()

    for j in range(NumberOfRotations): #right now only does a complete circle. 160 microsteps per rotation; 160/Number of Rotations = step size
        
        print("Starting 2D scan {} of {}".format(str(j+1),str(NumberOfRotations)))
        
        for w in range(len(ZCoord)):
            
            folder = 'Z' + str(ZCoord[w]) + "R" + str(j+1)
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            ZGoTo(int(ZCoord[w]))
        
            for i in range(len(XCoord)): 
            

            
                XGoTo(int(XCoord[i]))
                YGoTo(int(YCoord[i]))
                
                time.sleep(0.1) #vibration control.
            
            
            
            
                name = "X" + str(XCoord[i]) + "Y" + str(YCoord[i]) + "Z" + str(ZCoord[w]) + "R" + str(j+1) + "of" + str(NumberOfRotations) + filetype
            
            #sometimes process fails possibly because USB webcam fails.
            #This will see if ending the processing and moving on fixes it.
                while True: #I am wrapping the whole thing in a true loop to check if proc completed too fast (no usb), then waiting for user to reboot usb. BAD
                    try:
                        startpictime = time.time()
                    
                        proc = subprocess.Popen(["fswebcam", "-r 640x480", "--no-banner", folder + "/" + name], stdout=subprocess.PIPE) #like check_call(infinite timeout)
                        output = proc.communicate(timeout=10)[0]
                        endpictime = time.time()
                    
                    
                        if endpictime - startpictime >0.3: #a real picture
                            break
                        else: #usb got unplugged effing hell
                        
                            GPIO.output(BEEP,GPIO.HIGH)

                            a = input('HEY BOZO THE USB GOT UNPLUGGED UNPLUG IT AND PLUG IT BACK IN AND THEN PRESS ENTER')
                            print('okay thanks bozo. restarting with {}'.format(name))
                            GPIO.output(BEEP,GPIO.LOW)

                            continue
                    
                    except subprocess.TimeoutExpired: #does not catch USB UNPLUG. Catches if it 
                
                        print ("{} failed :( ".format(name))
                        proc.terminate() #corrective measure?
                        continue #move on. In true loop, it keeps trying the same picture since it shouldn't matter which one
            
    
            
            
        MoveR(RFORWARD,StepsPerImage,SLOW)
        
    #QuitCamera()
    print ('scan completed successfully after {} seconds! {} images taken'.format(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)), str(num_pictures)))

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

def StartCamera():
    """starts the camera. Separated from take pic so doesn't have to be loaded multiple times"""
    pygame.camera.init()
    cam = pygame.camera.Camera(pygame.camera.list_cameras()[0])
    cam.start()
    return cam #and pass it off to TakePic. Hopefully faster than creating it every time

def QuitCamera():
    """Quits the camera. Should this really be a function?"""
    pygame.camera.quit()
    
def TakePic(cam):
    
    img = cam.get_image()

    #pygame.image.save(img, "todaysdate" + "X" + X + "Y" + Y + "Z" + Z + ".png")
    
    return img #save a batch of them at once

#def SavePics(ImgLists):
#    #receives a list of lists of form [img,x,y,z] and saves file with those coordinates
#    for imlist 


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
            MoveX(XFORWARD,distance,FAST)
        else:
            MoveX(XBACKWARD,abs(distance),FAST) 
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
            MoveY(YFORWARD,distance,FAST)
        else:
            MoveY(YBACKWARD,abs(distance),FAST) 
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
         
    for i in range(numsteps):
            
        GPIO.output(ZSTEP, GPIO.HIGH)
        time.sleep(delay)    
        GPIO.output(ZSTEP, GPIO.LOW)        
        
    
    if direction == ZFORWARD: #totally arbitrary 
        GlobalZ += numsteps
    else:
        GlobalZ -= numsteps
    ZPosition.configure(text="Z: "+str(GlobalZ) + "/3000")

def ZGoTo(ZDest, ZMin=0, ZMax=3000):
    """checks the place is valid and then calls MoveZ appropriately.
    At the home position there happens to be just about 2000 steps
    forward and 1000 steps back --- for 1 micron per step.
    
    Reworked to start at 0 and end at 3000"""
    
    global GlobalZ
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
        
def SetR():
    #gets entry from dropdown for rotations and passes to global variable 
    global RScanNumber
    RScanNumber = int(RSetVar.get())
    


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
    MoveZ(ZBACKWARD,50,FAST)
    print("Z moved down a little!")

def MoveZUpBig():
    MoveZ(ZFORWARD,250,FASTER)
    print("Z moved up a lot!")
    
def MoveZUpSmall():
    MoveZ(ZFORWARD,50,FAST)
    print("Z moved up a little!")

def MoveRCWSmall():
    #cw when staring down at spindle or object
    MoveR(RFORWARD, 10, SLOW)
    print("You rotated something clockwise a bit!")
    
def MoveRCCWSmall(): #counterclockwise
    MoveR(RBACKWARD, 10, SLOW)
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

def GuiScan():
    
    GridScan(XScanMin,XScanMax,YScanMin,YScanMax,ZScanMin,ZScanMax,XScanStep,YScanStep,ZScanStep,RScanNumber)
    
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



#mainloop()
    