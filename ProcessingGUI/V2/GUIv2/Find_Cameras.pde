String[] findCameras()
{
  String[] cameras = Capture.list();//create array of available capture devices
  String[] tempList = new String[cameras.length];
  String[] cameraArray;
  int j = 0;
  if (cameras.length == 0) 
  {
    println("There are no cameras available for capture.");
    cameraArray = new String[1];
    cameraArray[0] = "no camera";
  } else 
  {
    println("Available filtered cameras:");
    for (int i = 0; i < cameras.length; i++) 
    {
      if (cameras[i].contains("size=640x480") && cameras[i].contains("fps=25"))// && cameras[i].contains("name=Logitech HD Webcam C270")
      //if (cameras[i].contains("name=USB2.0 UVC PC Camera")) //&& cameras[i].contains("fps=30") && cameras[i].contains("name=Logitech HD Webcam C270")

      {
        tempList[j] = cameras[i];
        println(cameras[i]);
        j++;
      }
    }
    cameraArray = new String[j+1];
    cameraArray[0] = "no camera";
    for (int i = 1; i < cameraArray.length; i++) 
    {
      cameraArray[i] = tempList[i-1];
    }
  }
  //video = new Capture(this, cameras[int(CameraSelection)]);
  //video.start();
  return cameraArray;
}
