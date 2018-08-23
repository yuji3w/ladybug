public void Up()
{
  println("Up!");
  port.write("6RY+100");
  //delay(0);
  port.write("3CU1");
}

public void Down()
{
  println("Down!");
  port.write("6RY-100");
  //delay(2);
  port.write("3CU1");
}

public void Left()
{
  println("Left!");
  port.write("6RX-100");
  //delay(2);
  port.write("3CU1");
}

public void Right()
{
  println("Right!");
  port.write("6RX+100");
  //delay(2);
  port.write("3CU1");
}



public void NorthWest()
{
  println("NorthWest!");
  port.write("5RX-71");
  delay(5);
  port.write("5RY+71");
  port.write("3CU1");
}

public void NorthEast()
{
  println("NorthEast!");
  port.write("5RX+71");
  delay(5);
  port.write("5RY+71");
  port.write("3CU1");
}

public void SouthEast()
{
  println("SouthEast!");
  port.write("5RX+71");
  delay(5);
  port.write("5RY-71");
  port.write("3CU1");
}

public void SouthWest()
{
  println("SouthWest!");
  port.write("5RX-71");
  delay(5);
  port.write("5RY-71");
  port.write("3CU1");
}
