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
sensitivityNum = 100000
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

m1 = 5
m2 = 3
gamePower = 38
clawGrab = 40

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

GPIO.setup(m1, GPIO.OUT)
GPIO.setup(m2, GPIO.OUT)
GPIO.setup(gamePower, GPIO.OUT)
GPIO.setup(clawGrab, GPIO.OUT)
def motorClaw_forward():
    GPIO.output(m1, GPIO.HIGH)
    GPIO.output(m2, GPIO.LOW)

def motorClaw_backward():
    GPIO.output(m1, GPIO.LOW)
    GPIO.output(m2, GPIO.HIGH)
    
def motorClaw_stop():
    GPIO.output(m1, GPIO.LOW)
    GPIO.output(m2, GPIO.LOW)
def dropClaw():
    motorClaw_forward()
    sleep(3)	
    motorClaw_stop()
    sleep(1)
    GPIO.output(clawGrab, True)
    sleep(.1)
    motorClaw_backward()
    sleep(3)
    motorClaw_stop()
    prizeDrop()
    
def prizeDrop():
    #Set CCW or CW for direction to home
    GPIO.output(DIR1,CCW)
    GPIO.output(DIR2,CW)
    homeReachedX = False
    homeReachedY = False
    # Run for 200 steps. This will change based on how you set you controller
    for x in range(sensitivityNum):
        pygame.event.pump()            
        if bumperTest(CCW,1) <.9:
            GPIO.output(STEP1,GPIO.HIGH)
            # Allow it to get there.
            sleep(speeds) # Dictates how fast stepper motor will run
            # Set coil winding to low
            GPIO.output(STEP1,GPIO.LOW)
            sleep(speeds) # Dictates how fast stepper motor will run
        else:
            print("Reached Home in X direction")
            homeReachedX = True
            if homeReachedX and homeReachedY:
                break
     
        if bumperTest(CW,2) <.9:
            GPIO.output(STEP2,GPIO.HIGH)
            # Allow it to get there.
            sleep(speeds) # Dictates how fast stepper motor will run
            # Set coil winding to low
            GPIO.output(STEP2,GPIO.LOW)
            sleep(speeds) # Dictates how fast stepper motor will run        
        else:
            print("Reach Home in Y direction")
            homeReachedY = True
            if homeReachedX and homeReachedY:
                break
    sleep(2)
    GPIO.output(clawGrab, False)
    print("Prize Dropped")
    GPIO.output(gamePower, False)
        
def bumperTest(theDirection,motorNum):
    bumperSafe1 = 0
    bumperSafe2 = 0
    bumperSafe3 = 0
    bumperSafe4 = 0
    pygame.event.pump()
    buttons =  [joystick.get_button(i) for i in  range(joystick.get_numbuttons())]
    #check and set bumper flags here...            
    bumperSafe1 = buttons[1]
    bumperSafe2 = buttons[2]
    bumperSafe3 = buttons[3]
    bumperSafe4 = buttons[4]
    if (theDirection == 1) and (motorNum ==1):
        #print("bummper 1 test")
        return bumperSafe1
    if (theDirection == 0) and (motorNum ==1):
        #print("bummper 2 test")
        return bumperSafe2
    if (theDirection == 1) and (motorNum ==2):
        #print("bummper 3 test")
        return bumperSafe3
    if (theDirection == 0) and (motorNum ==2):
        #print("bummper 4 test")
        return bumperSafe4

    return 0

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
            if bumperTest(TheDirection,motorNum) <.9:
                GPIO.output(STEP1,GPIO.HIGH)
                # Allow it to get there.
                sleep(speeds) # Dictates how fast stepper motor will run
                # Set coil winding to low
                GPIO.output(STEP1,GPIO.LOW)
                sleep(speeds) # Dictates how fast stepper motor will run
            else:
                print("NOT SAFE")
                break
        if motorNum == 2:
            if bumperTest(TheDirection,motorNum) <.9:
                GPIO.output(STEP2,GPIO.HIGH)
                # Allow it to get there.
                sleep(speeds) # Dictates how fast stepper motor will run
                # Set coil winding to low
                GPIO.output(STEP2,GPIO.LOW)
                sleep(speeds) # Dictates how fast stepper motor will run        
            else:
                print("NOT SAFE")
                break

def main():
    try:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print("joystick initialized",joystick.get_name())
        gamePlaying = False
        timer_active = False
        timer_start = 0
        timerLength = 30000 # 30 seconds
        pygame.event.pump()           
        buttons =  [joystick.get_button(i) for i in  range(joystick.get_numbuttons())]
        #check and set bumper flags here...
        GPIO.output(gamePower, False)
        sleep(2)
        GPIO.output(clawGrab, False)
        sleep(2)    
        while True:
            pygame.event.pump()
            axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
            buttons =  [joystick.get_button(i) for i in  range(joystick.get_numbuttons())]
            
            if buttons[0] >= .9:
                print("button pressed")
                #turn on motors
                gamePlaying = True
                timer_active = True
                timer_start = pygame.time.get_ticks()
                GPIO.output(gamePower, True)
            if gamePlaying:
                if buttons[5] >= .9:
                    timer_active = False
                    dropClaw()
                if axes[0] == -1:
                    print("Right - CW")              
                    stepperMove(CW,1)
                if axes[0] >= .9:
                    print("Left- CCW")
                    stepperMove(CCW,1)
                if axes[1] == -1:
                    print("Down - CCW")
                    stepperMove(CCW,2)
                if axes[1] >= .9:
                    print("Up - CW")
                    stepperMove(CW,2)
            #print("Button states:", buttons)
            #print("axes values:", axes)
            if timer_active and pygame.time.get_ticks() - timer_start >= timerLength:  # 30 seconds = 30000 milliseconds
                gamePlaying = False  # Reset gamePlaying flag
                timer_active = False
                GPIO.output(gamePower, False)
                #turn off motor
            if timer_active:
                print("{:.0f}".format((pygame.time.get_ticks() - timer_start)/1000))
            pygame.time.wait(100)
    except KeyboardInterrupt:
        pygame.quit()
        joystick.quit()
if __name__=="__main__":
    main()
    