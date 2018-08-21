public void Up()
{
  yGoto = yPosition + yOffsetValue + 100;
  println("Up!");
 // port.write(yGoto);
  yPosition += 100;
}

public void Down()
{
  yGoto = yPosition + yOffsetValue - 100;
  println("Down!");
 // port.write(yGoto);
  yPosition -= 100;
}

public void Left()
{
  xGoto = xPosition + xOffsetValue - value;
  println("xGoto " + xGoto);
  //port.write(xGoto);
  xPosition -= 100;
}

public void Right()
{
  xGoto = xPosition + xOffsetValue + 100;
  println("xGoto " + xGoto);
  port.write(xGoto);
  xPosition += 100;
  delay(100);
  port.write(-13);
}
