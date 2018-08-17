import controlP5.*;
import java.util.*;

import gab.opencv.*;
import processing.video.*;

import static javax.swing.JOptionPane.*;//needed by the message box for selecting port



ControlP5 GUI;
Capture video;
OpenCV opencv;

int bigTextSize = 32;
int blueText = #006699;
int greyBackround = 175;
int videoX = 320, videoY = 120, videoResX = 640, videoResY = 480;

boolean videoStarted = false;
String[] cameraArray;

void setup() {
  size(1280, 720);
  smooth();
  GUI = new ControlP5(this);

  GUI.addButton("File")
    .setValue(0)
    .setPosition(0, 0)
    .setSize(50, 30)
    ;


  List s = Arrays.asList("screenshot", "save image", "video");

  GUI.addScrollableList("Save")
    .setPosition(50, 0)
    .setSize(150, 150)
    .setBarHeight(30)
    .setItemHeight(30)
    .addItems(s)
    .setOpen(false)
    .setType(ScrollableList.DROPDOWN) // currently supported DROPDOWN and LIST
    ;


  cameraArray = findCameras();
  List cameraList = Arrays.asList(cameraArray);

  GUI.addScrollableList("Select_Camera")
    .setPosition(200, 0)
    .setSize(250, 300)
    .setBarHeight(30)
    .setItemHeight(30)
    .addItems(cameraList)
    .setOpen(false)
    .setType(ScrollableList.DROPDOWN) // currently supported DROPDOWN and LIST
    ;

  //cameraInit();
  opencv = new OpenCV(this, videoResX, videoResY);
  opencv.startBackgroundSubtraction(5, 3, 0.5);


  delay(3000);
}

void draw() {
  background(240);
  if (videoStarted)
  {
    image(video, videoX, videoY);
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

public void File() {
  println("File button pressed");
}
