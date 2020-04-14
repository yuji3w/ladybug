#https://www.pyimagesearch.com/2015/09/21/opencv-track-object-movement/
#Converted to be a function with goal of following insects and stuff
#wayne 4/12/2020

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time


def BallTracker(frame, ColorLower = (29, 86, 6), ColorUpper = (64, 255, 255),
                buffer = 32,counter=0,pts='default',
                dX = 0, dY = 0, direction = ""):
        

        # initialize the list of tracked points, the frame counter,
        # and the coordinate deltas
        if pts == 'default': #initate the scan for the first time    
            pts = deque(maxlen=buffer)


        # resize the frame, blur it, and convert it to the HSV
        # color space
        frame = imutils.resize(frame, width=640)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # construct a mask for the color "green", then perform
        # a series of dilations and erosions to remove any small
        # blobs left in the mask
        mask = cv2.inRange(hsv, ColorLower, ColorUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None

        # only proceed if at least one contour was found
        if len(cnts) > 0:
                # find the largest contour in the mask, then use
                # it to compute the minimum enclosing circle and
                # centroid
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                # only proceed if the radius meets a minimum size
                if radius > 10:
                        #return(x,y)
                        # draw the circle and centroid on the frame,
                        # then update the list of tracked points
                        cv2.circle(frame, (int(x), int(y)), int(radius),
                                (0, 255, 255), 2)
                        cv2.circle(frame, center, 5, (0, 0, 255), -1)
                        pts.appendleft(center)

        elif len(cnts) == 0: #no contour
            counter+=1
            #return frame,x,y,direction,dX,dY,pts,counter
            return False
        
        # loop over the set of tracked points
        for i in np.arange(1, len(pts)):
                # if either of the tracked points are None, ignore
                # them
                if pts[i - 1] is None or pts[i] is None:
                        continue

                # check to see if enough points have been accumulated in
                # the buffer
                if counter >= 10 and i == 1 and pts[-10] is not None:
                        # compute the difference between the x and y
                        # coordinates and re-initialize the direction
                        # text variables
                        dX = pts[-10][0] - pts[i][0]
                        dY = pts[-10][1] - pts[i][1]
                        (dirX, dirY) = ("", "")

                        # ensure there is significant movement in the
                        # x-direction
                        if np.abs(dX) > 20:
                                dirX = "East" if np.sign(dX) == 1 else "West"

                        # ensure there is significant movement in the
                        # y-direction
                        if np.abs(dY) > 20:
                                dirY = "North" if np.sign(dY) == 1 else "South"

                        # handle when both directions are non-empty
                        if dirX != "" and dirY != "":
                                direction = "{}-{}".format(dirY, dirX)

                        # otherwise, only one direction is non-empty
                        else:
                                direction = dirX if dirX != "" else dirY

                # otherwise, compute the thickness of the line and
                # draw the connecting lines
                thickness = int(np.sqrt(buffer / float(i + 1)) * 2.5)
                #print(pts[i - 1], pts[i])
                #print('seperate')
                #print(type(pts[i-1]))
                #print(type(pts[i]))
                #return(frame,pts,thickness)
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

        # show the movement deltas and the direction of movement on
        # the frame
        cv2.putText(frame, direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 0, 255), 3)
        cv2.putText(frame, "dx: {}, dy: {}".format(dX, dY),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.35, (0, 0, 255), 1)
        counter+=1
        
        # show the frame to our screen and increment the frame counter
        return (frame,x,y,direction,dX,dY,pts,counter)
