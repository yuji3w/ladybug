public void Save(int n) {
  /* request the selected item based on index n */
  println(n, GUI.get(ScrollableList.class, "Save").getItem(n));
  PImage save;
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
