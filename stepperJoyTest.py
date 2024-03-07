import pygame
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print("joystick initialized",joystick.get_name())
from time import sleep
#sensitivityNum number of steps to revolution.. bigger is faster
sensitivityNum = 2000
#smaller is faster
speeds = .0005
# Direction pin from controller
DIR1 = 10
DIR2 = 10
# Step pin from controller
STEP1 = 8
STEP2 = 11
# 0/1 used to signify clockwise or counterclockwise.
CW = 1
CCW = 0

# Setup pin layout on PI
GPIO.setmode(GPIO.BOARD)

# Establish Pins in software
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(STEP1, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(STEP2, GPIO.OUT)
# Set the first direction you want it to spin
GPIO.output(DIR1, CW)
GPIO.output(DIR2, CW)


def stepperMove(TheDirection,motorNum):
    """Change Direction: Changing direction requires time to switch. The
    time is dictated by the stepper motor and controller. """
    #sleep(.001)
    if motorNum == 1:
        #Esablish the direction you want to go
        GPIO.output(DIR1,TheDirection)
    else:
        GPIO.output(DIR2,TheDirection)
    # Run for 200 steps. This will change based on how you set you controller
    for x in range(sensitivityNum):
        pygame.event.pump()            
        axis = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        if all(abs(a) < 0.1 for a in axis):
            #print(a)# Stop motor if joystick is at center position
            break
        # Set one coil winding to high
        if motorNum == 1:
            GPIO.output(STEP1,GPIO.HIGH)
            # Allow it to get there.
            sleep(speeds) # Dictates how fast stepper motor will run
            # Set coil winding to low
            GPIO.output(STEP1,GPIO.LOW)
            sleep(speeds) # Dictates how fast stepper motor will run
        if motorNum == 2:
            GPIO.output(STEP1,GPIO.HIGH)
            # Allow it to get there.
            sleep(.00001) # Dictates how fast stepper motor will run
            # Set coil winding to low
            GPIO.output(STEP1,GPIO.LOW)
            sleep(.00001) # Dictates how fast stepper motor will run        
def main():
    
    try:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print("joystick initialized",joystick.get_name())
        while True:
            pygame.event.pump()
            axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
            
            if axes[0] == -1:
                print("Right - CW")              
                GPIO.output(DIR1,CW)
                stepperMove(CW,1)
            if axes[0] >= .9:
                print("Left- CCW")
                stepperMove(CCW,1)
                #GPIO.output(DIR1,CCW)
                #GPIO.output(STEP1,GPIO.HIGH)
            if axes[1] == -1:
                print("Down - CCW")
                stepperMove(CCW,2)
            if axes[1] >= .9:
                print("Up - CW")
                stepperMove(CW,2)
            buttons =  [joystick.get_button(i) for i in  range(joystick.get_numbuttons())]
            #print("Button states:", buttons)
            #print("axes values:", axes)
            pygame.time.wait(100)
    except KeyboardInterrupt:
        pygame.quit()
        joystick.quit()
if __name__=="__main__":
    main()
    