#I am reworking functions so that they produce a list of absolute locations for XYZR in list form throughout a scan
#that way we can both easily stop and resume a scan by just going back to where we left off,
#and also convert this function into creating a gcode that does the same thing.


from numpy import *

def DefineScan(XMin, XMax, YMin, YMax, ZMin, ZMax, RMin, RMax, XSteps=100, YSteps=100, ZSteps=1, RSteps=1):
    """core from stack exchange. https://stackoverflow.com/questions/20872912/raster-scan-pattern-python
    modified october 11 2018 to include Z and R, meaning R is now set in absolute positions
    Important: Because its not inclusive in max, it will break if for instance you say rmin = 0 rmax = 0, so we add 1 to all maximums
    so if you dont want to go more than one Z or R, set for instance Zmin=Zmax and ZSteps = 1."""
    
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
            
    return(NewNewXScan,NewNewYScan,NewNewZScan,NewNewRScan)

def GridScan(ScanLocations,conditions='default'):
     
    XCoord = ScanLocations[0]
    YCoord = ScanLocations[1]
    ZCoord = ScanLocations[2]
    RCoord = ScanLocations[3]
    
    """Note that we have already added 1 in the DefineScan to account for half intervals"""
    
    
    """conditions will contain save location, filetype, resolution. First time running default
    is passed which contains standard conditions, but you can always specify it if you want to."""
    
    if conditions == 'default':
        save_location = filedialog.askdirectory()
        filetype = ".png"
        resolution = "640x480" #fswebcam adjusts to be higher at least with alternate microscope I have
        timeout = 10 #number of seconds you have to save the scan.
    
    else:
        print('you should specify conditions are from the file')
        
    num_pictures = len(XCoord) #remaining, not originally
    NumberOfRotations = len(set(RCoord))
    stepsPerRotation = ((max(RCoord)-min(RCoord))/len(set(RCoord)))
    
    print("Stepping {} per image".format(str(StepsPerImage))) #just for debugging
    
    XGoTo(int(XCoord[0]))
    YGoTo(int(YCoord[0]))
    ZGoTo(int(ZCoord[0]))
    RGoTo(int(RCoord[0]))
    
    start_time = time.time()
    
        
    for i in range(num_pictures):
        
        if i % 100 == 0: #every 100 pics
            print("{} pictures remaining".format(num_pictures-i))
            GPIO.output(BEEP,GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(BEEP,GPIO.LOW)
    
        if i != 0:
            if ZCoord[i] != ZCoord[i+1]: #new Z height. Make a new folder and start saving
        
            
                folder = save_location + "/Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3)
                if not os.path.exists(folder): #should hopefully continue saving in the same folder after restart
                    os.makedirs(folder)
            
        #go to locations
                    
        XGoTo(int(XCoord[i]))
        YGoTo(int(YCoord[i]))
        ZGoTo(int(ZCoord[i]))
        RGoTo(int(RCoord[i]))
            
        time.sleep(0.1) #vibration control.
                
            
            
            
        name = "X" + str(XCoord[i]).zfill(4) + "Y" + str(YCoord[i]).zfill(4) + "Z" + str(ZCoord[i]).zfill(4) + "R" + str(RCoord[i]).zfill(3) + "of" + str(NumberOfRotations).zfill(3) + filetype

        """begin filesaving block"""
        
        for i in range(2): #I am wrapping the whole thing in a true loop to check if proc completed too fast (no usb), then waiting for user to reboot usb. 
            try:
                startpictime = time.time()
            
                proc = subprocess.Popen(["fswebcam", "-r " + resolution, "--no-banner", folder + "/" + name], stdout=subprocess.PIPE) #like check_call(infinite timeout)
                output = proc.communicate(timeout=10)[0]
                endpictime = time.time()
            
            
                if endpictime - startpictime >0.2: #a real picture
                    break
                else: #usb got unplugged effing #hell
                    
                    #attempt to catch USB from https://stackoverflow.com/questions/1335507/keyboard-input-with-timeout-in-python  
                    print('HEY BOZO THE USB GOT UNPLUGGED UNPLUG IT AND PLUG IT BACK IN WITHIN {} SECONDS OR WE REBOOT'.format(timeout))
                    
                    GPIO.output(BEEP,GPIO.HIGH) #beep and bibrate
                    
                    time.sleep(timeout)
                    
                    GPIO.output(BEEP,GPIO.LOW)
                    continue
                 
                   
            
            
            except subprocess.TimeoutExpired: #does not catch USB UNPLUG. Catches if it 
        
                print ("{} failed :( ".format(name))
                proc.terminate() #corrective measure?
                continue #move on. In true loop, it keeps trying the same picture since it shouldn't matter which one
    
            """begin restart block. if we got here, its because user was prompted too many times without fixing"""
            print('we should restart now')
            
        
    #QuitCamera()
    print ('scan completed successfully after {} seconds! {} images taken'.format(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)), str(num_pictures)))
    for i in range(5):
        GPIO.output(BEEP,GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BEEP,GPIO.LOW)

