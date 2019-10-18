
import signal

timeout = None

def main():
    inp = stdinWait("You have 5 seconds to type text and press <Enter>... ", "[no text]", 5, "Aw man! You ran out of time!!")
    if not timeout:
        print("You entered", inp)
    else:
        print("You didn't enter anything because I'm on a tight schedule!")
        
def stdinWait(text, default, time, timeoutDisplay = None, **kwargs):
    signal.signal(signal.SIGALRM, interrupt)
    signal.alarm(time) # sets timeout
    global timeout
    try:
        inp = raw_input(text)
        signal.alarm(0)
        timeout = False
    except (KeyboardInterrupt):
        printInterrupt = kwargs.get("printInterrupt", True)
        if printInterrupt:
            print("Keyboard interrupt")
        timeout = True # Do this so you don't mistakenly get input when there is none
        inp = default
    except:
        timeout = True
        if not timeoutDisplay is None:
            print(timeoutDisplay)
        signal.alarm(0)
        inp = default
    return inp

def interrupt(signum, frame):
    raise Exception("")

if __name__ == "__main__":
    main()