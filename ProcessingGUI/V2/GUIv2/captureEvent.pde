void captureEvent(Capture video)
{
 // prev.copy(video, 0, 0, video.width, video.height, 0, 0, prev.width, prev.height);
  prev.copy(video, 0, 0, video.width, video.height, 0, 0, video.width, video.height);

  prev.updatePixels();
  video.read();
}
