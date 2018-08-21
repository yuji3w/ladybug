void parseCommand(char alpha, char beta, char sign, int value)
{
  long movement = 0;
  int newLocation = 0;  // variable for case R of switch alpha

  switch (alpha)
  {

    case 'A':  // absolute location
      switch (beta)
      {
        case 'X':
          if (value < X_LOWER_BOUNDARY || value > X_UPPER_BOUNDARY)
            Serial.println('m' + value + " out of bounds!");
          else
          {
            movement = value - CXP;
            prepareMovement(0, movement);
            CXP = value;
          }
          break;
        case 'Y':
          if (value < Y_LOWER_BOUNDARY || value > Y_UPPER_BOUNDARY)
            Serial.println('m' + value + " out of bounds!");
          else
          {
            movement = value - CYP;
            prepareMovement(1, movement);
            CYP = value;
          }
          break;
        case 'Z':
          if (value < Z_LOWER_BOUNDARY || value > Z_UPPER_BOUNDARY)
            Serial.println('m' + value + " out of bounds!");
          else
          {
            movement = value - CZP;
            prepareMovement(2, movement);
            CZP = value;
          }
          break;
        case 'R':

          break;
        default:

          break;
      }
      break;
    case 'R':  // relative location
      if (sign == '-')
        value *= -1;
      switch (beta)
      {
        case 'X':
          newLocation = CXP + value;
          if (newLocation < X_LOWER_BOUNDARY)
          {
            Serial.println("mX Boundary Met!");
            value = X_LOWER_BOUNDARY - CXP;
            newLocation = X_LOWER_BOUNDARY;
          }
          else if (newLocation > X_UPPER_BOUNDARY)
          {
            Serial.println("mX Boundary Met!");
            value = X_UPPER_BOUNDARY - CXP;
            newLocation = X_UPPER_BOUNDARY;
          }
          if (CXP != newLocation)
          {
            prepareMovement(0, value);
            CXP = newLocation;
          }
          break;
        case 'Y':
          newLocation = CYP + value;
          if (newLocation < Y_LOWER_BOUNDARY)
          {
            Serial.println("mY Boundary Met!");
            value = Y_LOWER_BOUNDARY - CYP;
            newLocation = Y_LOWER_BOUNDARY;
          }
          else if (newLocation > Y_UPPER_BOUNDARY)
          {
            Serial.println("mY Boundary Met!");
            value = Y_UPPER_BOUNDARY - CYP;
            newLocation = Y_UPPER_BOUNDARY;
          }
          if (CYP != newLocation)
          {
            prepareMovement(1, value);
            CYP = newLocation;
          }
          break;
          break;
        case 'Z':
          newLocation = CZP + value;
          if (newLocation < Z_LOWER_BOUNDARY)
          {
            Serial.println("mZ Boundary Met!");
            value = Z_LOWER_BOUNDARY - CZP;
            newLocation = Z_LOWER_BOUNDARY;
          }
          else if (newLocation > Z_UPPER_BOUNDARY)
          {
            Serial.println("mZ Boundary Met!");
            value = Z_UPPER_BOUNDARY - CZP;
            newLocation = Z_UPPER_BOUNDARY;
          }
          if (CZP != newLocation)
          {
            prepareMovement(2, value);
            CZP = newLocation;
          }
          break;
          break;
        case 'R':

          break;
        default:

          break;
      }
      break;
    case 'C':
      if (beta == 'U')  // just for testing
      {
        Serial.print("mrunning...");
        runAndWait();
        Serial.println(" run complete");
      }
      break;
    default:

      break;
  }
}

/*
  long steps(int whichMotor, long steps, int interval)
  {
  long stepsMoved = 0;
  if (steps < 0)
    set_direction(whichMotor, 0);
  else
    set_direction(whichMotor, 1);

  for (int i = 0; i < steps; i++)
  {
    step(whichMotor);
    delayMicroseconds(interval);
  }
  return stepsMoved;
  }*/


void loop()
{
  if (Serial.available())
  {
    //Serial.println(millis());
    byte checkSum = Serial.read() - '0';
    //Serial.println(checkSum);
    while (Serial.available() < checkSum) {} // wait until all data has arrived
    long numberInput = 0;  // varialble for reading in the numeric value in the command
    char sign = '0';
    char CMDA = Serial.read();
    char CMDB = Serial.read();
    if (CMDA == 'R') // if position info is reletive...
      sign = Serial.read();  // ...read in sign
    //read in value
    while (Serial.available() > 0)
    {
      //delay(1);
      numberInput *= 10;
      numberInput += (Serial.read() - '0');
    }

    //Serial.println(millis());

    Serial.print("e");
    Serial.print(CMDA);
    Serial.print(CMDB);
    if (CMDA == 'R')
      Serial.print(sign);
    Serial.print(numberInput);
    Serial.print(" (");
    Serial.print(checkSum);
    Serial.println(")");
    parseCommand(CMDA, CMDB, sign, numberInput);
  }

}
//void serialEvent()
//{


//}







