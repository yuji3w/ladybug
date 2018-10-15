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


