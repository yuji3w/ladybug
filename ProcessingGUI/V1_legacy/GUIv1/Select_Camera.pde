void Select_Camera(int n) {
  /* request the selected item based on index n */
  println(n, GUI.get(ScrollableList.class, "Select_Camera").getItem(n));

  /* here an item is stored as a Map  with the following key-value pairs:
   * name, the given name of the item
   * text, the given text of the item by default the same as name
   * value, the given value of the item, can be changed by using .getItem(n).put("value", "abc"); a value here is of type Object therefore can be anything
   * color, the given color of the item, how to change, see below
   * view, a customizable view, is of type CDrawable 
   */

  /*CColor c = new CColor();
  c.setBackground(color(255, 0, 0));
  GUI.get(ScrollableList.class, "Select_Camera").getItem(n).put("color", c);
  */
  if (videoStarted)
  {
    videoStarted = false;
    video.stop();
  }
  if (n != 0)
  {
  video = new Capture(this, cameraArray[n]);
  video.start();
  videoStarted = true;
  }
}
