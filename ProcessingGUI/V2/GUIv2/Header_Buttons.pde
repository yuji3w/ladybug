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
}

void Save(int n) 
{

  println(n, GUI.get(ScrollableList.class, "Save").getItem(n));
  //PImage save;
  switch(n)
  {
  case 0:
    saveFrame("Output/screenshot_####.png");
    break;
  case 1:
    break;
  default:
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
