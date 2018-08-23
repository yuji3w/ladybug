String[] findPort()
{
  String[] portDevices = Serial.list();//create array of available capture devices
  String[] tempList = new String[portDevices.length];
  String[] portArray;
  
  
  int j = 0;
  if (portDevices.length == 0) 
  {
    println("There are no ports available.");
    portArray = new String[1];
    portArray[0] = "no port";
  } else 
  {
    println("Available ports:");
    for (int i = 0; i < portDevices.length; i++) 
    {
        tempList[j] = portDevices[i];
        println(portDevices[i]);
        j++;
    }
    portArray = new String[j+1];
    portArray[0] = "no port";
    for (int i = 1; i < portArray.length; i++) 
    {
      portArray[i] = tempList[i-1];
    }
  }
  //video = new Capture(this, cameras[int(CameraSelection)]);
  //video.start();
  return portArray;
}
