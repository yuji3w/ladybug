
#include <AccelStepper.h>
#include <MultiStepper.h>


AccelStepper stepperX(AccelStepper::DRIVER, 2, 5); //(Mode, step, direction)
AccelStepper stepperY(AccelStepper::DRIVER, 3, 6);

// Up to 10 steppers can be handled as a group by MultiStepper
MultiStepper steppers;

void setup() {
  Serial.begin(115200);

  // Configure each stepper
  stepperX.setMaxSpeed(500);
  stepperY.setMaxSpeed(500);
  stepperX.setSpeed(1000); 
  stepperY.setSpeed(1000);   

  // Then give them to MultiStepper to manage
  steppers.addStepper(stepperX);
  steppers.addStepper(stepperY);

    int position = 100;
    stepperX.moveTo(position);
}

void loop() {
  /*long positions[2]; // Array of desired stepper positions
  
  positions[0] = 1000;
  positions[1] = 1000;
  steppers.moveTo(positions);
  steppers.runSpeedToPosition(); // Blocks until all are in position
  delay(1000);
  
  // Move to a different coordinate
  positions[0] = 0;
  positions[1] = 0;
  steppers.moveTo(positions);
  steppers.runSpeedToPosition(); // Blocks until all are in position
  delay(1000);
  */
stepperX.runSpeed();
  
}
