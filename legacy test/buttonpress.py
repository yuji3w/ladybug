import time

try:                        # In order to be able to import tkinter for
    import tkinter as tk    # either in python 2 or in python 3
except ImportError:
    import Tkinter as tk


#Begin disgusting block of instructions for keypress. Complicated by fact we want to be able to hold Down.
#Modified from https://stackoverflow.com/questions/12994796/how-can-i-control-keyboard-repeat-delay-in-a-tkinter-root-window
#main changes are not displaying the Label and also only enabling key control when checkbox is checked (allow_keypress)

def LeftStep(*event): #X
    print('Left')

    if LeftLabel._repeat_on:
        win.after(LeftLabel._repeat_freq, LeftStep)

def LeftStop(*event):
    if LeftLabel._repeat_on:
        LeftLabel._repeat_on = False
        win.after(LeftLabel._repeat_freq + 1, LeftStop)
    else:
        LeftLabel._repeat_on = True


def RightStep(*event):
    print('Right')

    if RightLabel._repeat_on:
        win.after(RightLabel._repeat_freq, RightStep)

def RightStop(*event):
    if RightLabel._repeat_on:
        RightLabel._repeat_on = False
        win.after(RightLabel._repeat_freq + 1, RightStop)
    else:
        RightLabel._repeat_on = True


def UpStep(*event):
    print('Up')

    if UpLabel._repeat_on:
        win.after(UpLabel._repeat_freq, UpStep)

def UpStop(*event):
    if UpLabel._repeat_on:
        UpLabel._repeat_on = False
        win.after(UpLabel._repeat_freq + 1, UpStop)
    else:
        UpLabel._repeat_on = True

def DownStep(*event):
    print('Down')

    if DownLabel._repeat_on:
        win.after(DownLabel._repeat_freq, DownStep)

def DownStop(*event):
    if DownLabel._repeat_on:
        DownLabel._repeat_on = False
        win.after(DownLabel._repeat_freq + 1, DownStop)
    else:
        DownLabel._repeat_on = True

def AStep(*event): #note actual lowercase. FOr clock and counterclockwise rotation
    print('A')

    if ALabel._repeat_on:
        win.after(ALabel._repeat_freq, AStep)

def AStop(*event):
    if ALabel._repeat_on:
        ALabel._repeat_on = False
        win.after(ALabel._repeat_freq + 1, AStop)
    else:
        ALabel._repeat_on = True

def DStep(*event): #note actual lowercase. FOr clock and counterclockwise rotation
    print('D')

    if DLabel._repeat_on:
        win.after(DLabel._repeat_freq, DStep)

def DStop(*event):
    if DLabel._repeat_on:
        DLabel._repeat_on = False
        win.after(DLabel._repeat_freq + 1, DStop)
    else:
        DLabel._repeat_on = True

def WStep(*event): #note actual lowercase. For Z AXIS W and S
    print('W')

    if WLabel._repeat_on:
        win.after(WLabel._repeat_freq, WStep)

def WStop(*event):
    if WLabel._repeat_on:
        WLabel._repeat_on = False
        win.after(WLabel._repeat_freq + 1, WStop)
    else:
        WLabel._repeat_on = True

def SStep(*event): #note actual lowercase. For Z AXIS S and S
    print('S')

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
if __name__ == '__main__':
    win = tk.Tk()
    
    #begin dummy Labels for each keyboard control. 
    
    LeftLabel = tk.Label(win)
    LeftLabel._repeat_freq = 10 #holding Down key, milisecond per repeat. 
    LeftLabel._repeat_on = True
    
    RightLabel = tk.Label(win)
    RightLabel._repeat_freq = 10 
    RightLabel._repeat_on = True
    
    UpLabel = tk.Label(win)
    UpLabel._repeat_freq = 10 
    UpLabel._repeat_on = True
   
    DownLabel = tk.Label(win)
    DownLabel._repeat_freq = 10  
    DownLabel._repeat_on = True
    
    ALabel = tk.Label(win) #a nd d are rotation
    ALabel._repeat_freq = 10  
    ALabel._repeat_on = True
    
    DLabel = tk.Label(win)
    DLabel._repeat_freq = 10  
    DLabel._repeat_on = True
    
    WLabel = tk.Label(win)
    WLabel._repeat_freq = 10  
    WLabel._repeat_on = True
    
    SLabel = tk.Label(win)
    SLabel._repeat_freq = 10  
    SLabel._repeat_on = True
    
    YLabel = tk.Label(win)
    
    #for testing
    win.geometry('300x300')
    
    
    
    keypress_var = tk.IntVar() #1 if button is pressed
    keypress_button = tk.Checkbutton(win, text="Expand", variable=keypress_var, command=allow_keypress)
    keypress_button.pack()
    
    #Label.pack()
    #win.mainloop()