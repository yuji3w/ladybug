import controlP5.*;
import java.util.*;
import processing.serial.*;
import processing.video.*;
import gab.opencv.*;

//import static javax.swing.JOptionPane.*;//needed by the message box for selecting port

// serial object
Serial port;

ControlP5 GUI;  // controlP5 object

// lists for scrollable list 
List cameraList;
List portList;
// scrollable list objects
ScrollableList selectCamera;
ScrollableList selectPort;
ScrollableList save;

// button objects
Button refresh;
Button file;

Button Up;
Button Down;
Button Left;
Button Right;
Button NorthWest;
Button NorthEast;
Button SouthEast;
Button SouthWest;

int xPosition = 0;
int yPosition = 0;
int zPosition = 0;
int rPosition = 0;

int xGoto;
int yGoto;
int zGoto;
int rGoto;

static final int xOffsetValue = 0;
static final int yOffsetValue = 3000;
static final int zOffsetValue = 6000;
static final int rOffsetValue = 10000;




Capture video;  // capture object
PImage prev;  // previous frame for motion detection
float threshold = 25;  // motion detection threshold
OpenCV opencv;  // opencv object


// global variables
int bigTextSize = 32;  // univeral large text size
int blueText = #006699;  // universal blue text color
int greyBackround = 175;  // universal grey background 
int videoX = 320, videoY = 120, videoResX = 640, videoResY = 480;  // universal video parameters
int value = 100;  // parametric button value

String prevPort = "";  // holds old port name (static variable for Select_Port)


// universal flags
boolean motionFlag = false;
boolean arduinoResponse = false;
boolean videoStarted = false;
boolean portSelected = false;

String[] cameraArray;
String[] portArray;  // array for available port devices

void setup() 
{
  size(1280, 720);
  smooth();

  GUI = new ControlP5(this);

  Button_Setup();


  //cameraInit();
  opencv = new OpenCV(this, videoResX, videoResY);
  opencv.startBackgroundSubtraction(5, 3, 0.5);


  delay(3000);
}

void draw()
{
  background(240);
  if (videoStarted)
  {
    video.loadPixels();
    prev.loadPixels();
    image(video, videoX, videoY);
    threshold = map(mouseX, 0, width, 0, 100);
    if (motionFlag)
    {
      //Motion_Track();
    }
  } else
  {
    noStroke();
    fill(greyBackround);
    rect(videoX, videoY, videoResX, videoResY);
    textSize(bigTextSize);
    fill(blueText);
    textAlign(CENTER, CENTER);
    text("No Camera Selected", videoX + videoResX/2, videoY + videoResY/2);
  }
}



String romanNumeral(int m)
{
  String month = String.valueOf(m);
  switch(m)
  {
  case 1:
    month = "I";
    break;
  case 2:
    month = "II";
    break;
  case 3:
    month = "III";
    break;
  case 4:
    month = "IV";
    break;
  case 5:
    month = "V";
    break;
  case 6:
    month = "VI";
    break;
  case 7:
    month = "VII";
    break;
  case 8:
    month = "VIII";
    break;
  case 9:
    month = "IX";
    break;
  case 10:
    month = "X";
    break;
  case 11:
    month = "XI";
    break;
  case 12:
    month = "XII";
    break;
  default:
    println("ERROR:  romanNumeral Default");
  }
  return month;
}


void serialEvent (Serial port)
{
  println(port.readStringUntil('\n'));
  /*
  if ( port.readStringUntil('\n') == "OK")
   {
   arduinoResponse = true;
   }
   else
   {
   ;  // do nothing right now
   }*/
}
