/*void Motion_Track()
{
  float avgX = 0;
  float avgY = 0;

  int count = 0;
  loadPixels();
  // Begin loop to walk through every pixel
  for (int x = 0; x < video.width; x++ ) {
    for (int y = 0; y < video.height; y++ ) {
      int loc = x + y * video.width;
      // What is current color
      color currentColor = video.pixels[loc];
      float r1 = red(currentColor);
      float g1 = green(currentColor);
      float b1 = blue(currentColor);
      color prevColor = prev.pixels[loc];
      float r2 = red(prevColor);
      float g2 = green(prevColor);
      float b2 = blue(prevColor);


      float d = distSq(r1, g1, b1, r2, g2, b2); 

      if (d < threshold*threshold)
      {
        //stroke(255);
        //strokeWeight(1);
        // point(x, y);
        //avgX += x;
        //avgY += y;
        //count++;
        pixels[loc] = color(0);
      } else {
        pixels[loc] = color(255);
      }
    }
  }
  updatePixels();
}*/

float distSq(float x1, float y1, float z1, float x2, float y2, float z2)
{
  float d = (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1) +(z2-z1)*(z2-z1);
  return d;
}
