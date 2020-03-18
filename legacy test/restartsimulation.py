'''#restart test

#we want to be able to restart if USB fails and resume where we left off
#so we have to save conditions to a file at checkpoints and then load them
#might make sense to also home procedure

#right now we're just going to count a sequence between 1-100 and resume where we left off
'''
import subprocess
import json
import random
import time

'''

Okay so first we have a scan that accepts a list of conditions (start and end number). it runs through these and will stop at a random point between (usb disconnect)
when it does so, it saves a json file of the conditions and restarts.
When the program boots up (which will be automatic), it checks to see if there is a json file there.
if not, do nothing
if there is, run the scan with the conditions loaded from json file. 

'''

def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

def simulated_scan(scan_conditions):
    
    start = scan_conditions[0]
    maxnum = scan_conditions[1]
    
    
    scan_fail = random.randrange(start,maxnum)
    
    
    for i in range(start, maxnum): #count through, save current state at fail num, and resume
        
        if i == scan_fail:
            print('restarting without printing {}'.format(i))
            
            with open('/home/pi/Desktop/ladybug/scandata.json', 'w') as scan_file:
                scan_conditions = [i,maxnum]
                json.dump(scan_conditions,scan_file)
        
            time.sleep(1)
            #restart() #works but will get caught in an infinite loop!
            
        time.sleep(0.05)        
        print(i)
        

try:
        with open('/home/pi/Desktop/ladybug/scandata.json', 'r') as scan_file:
        
            scan_conditions = json.load(scan_file)
            
            simulated_scan(scan_conditions)
            
except FileNotFoundError:
        
    print('no json file found. doing nothing')
        
        
