public void File()
{
  println("Button0 pressed");
  if (motionFlag)
    motionFlag = false;
  else
    motionFlag = true;
}


void Refresh()
{
  selectCamera.removeItems(cameraList);
  cameraArray = findCameras();
  cameraList = Arrays.asList(cameraArray);
  selectCamera.addItems(cameraList);

  selectPort.removeItems(portList);
  portArray = findPort();
  portList = Arrays.asList(portArray);
  selectPort.addItems(portList);
}

void Save(int n) 
{
  println(n, GUI.get(ScrollableList.class, "Save").getItem(n));
  if (videoStarted)
  {
    switch(n)
    {
    case 0:
      save("Output/screenshot_####.png");
      break;
    case 1:
      String folderName = String.valueOf(year()) + "-" + romanNumeral(month()) + "-" + String.valueOf(day());  // generate date string for folder name 
      String imageName = String.valueOf(hour()) + "h" + String.valueOf(minute()) + "m" + String.valueOf(second()) + "s";  // generate time string for file name
      video.save("images/" + folderName + "/" + imageName + ".jpg");  // save current image
      //video.save("images/helloWorld.jpg");  // test save

      break;
    case 2:

      break;
    default:
    }
  }
}  // end of Save(int)


void Select_Port(int n)
{
  //static int prevPort = 0;  // port currently in use
  if (portSelected)
  {
    portSelected= false;
    port.stop();
    println("Communication with " + prevPort + " closed");
  }
  if (n != 0)
  {
    port = new Serial(this, portArray[n], 115200);
    port.bufferUntil('\n');
    println("Communication with " + portArray[n] + " opened");
    prevPort = portArray[n];
    portSelected = true;
  }
}


void Select_Camera(int n)
{
  if (videoStarted)
  {
    videoStarted = false;
    video.stop();
  }
  if (n != 0)
  {
    video = new Capture(this, cameraArray[n]);
    video.start();
    prev = createImage(video.width, video.height, RGB);
    videoStarted = true;
  }
}
