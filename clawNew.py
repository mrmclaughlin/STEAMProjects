import pygame
import RPi.GPIO as GPIO
import vlc
import threading
import time
#note to fix the install issue
#pip3 install python-vlc  --break-system-package
GPIO.setwarnings(False)
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print("joystick initialized",joystick.get_name())
from time import sleep
#sensitivityNum number of steps to revolution.. bigger is faster
stepsForOneRevolution = 1600
numberOfrevolutions = 20
sensitivityNum = stepsForOneRevolution*numberOfrevolutions
#needed for stepper coil to have equal time to wind high and then wind low
delayRatio = .87

#smaller speeds makes stepper faster .001 is determined as optimal
speeds = .0001
# Direction pin from controller
DIR1 = 18
DIR2 = 11
# Step pin from controller
STEP1 = 8
STEP2 = 13


# 0/1 used to signify clockwise or counterclockwise.
CW = 1
CCW = 0

m1 = 5
m2 = 3
gamePower = 38
clawGrab = 40

# ---------------- ROTATION SENSOR (NEW) ----------------
# Signal wire from the rotation sensor (DO / OUT / C1 / A) goes to physical pin 16
ENCODER_PIN = 16

# How many pulses the sensor sends for ONE full turn of the shaft it watches.
#   Slotted disk: number of slots (common disks have 20)
#   Hall sensor + magnets: number of magnets
#   Motor with built-in encoder: check the motor's spec sheet (PPR)
PULSES_PER_REV = 20

# How many turns of the winch to lower the claw. CALIBRATE THIS:
# watch the printed counts during a drop and adjust until the claw just reaches the prizes.
DROP_REVOLUTIONS = 10
DROP_PULSES = int(PULSES_PER_REV * DROP_REVOLUTIONS)

# Safety limits so a broken wire or jammed line can never run the motor forever
MAX_DROP_TIME = 8      # seconds - longest the claw may go down
MAX_RAISE_TIME = 12    # seconds - longest the claw may go up
STALL_TIMEOUT = 1.0    # seconds with NO pulses while motor is on = stalled/sensor problem

# Position of the claw in pulses: 0 = fully up. Goes up while lowering, down while raising.
encoder_count = 0
encoder_lock = threading.Lock()
# +1 while lowering, -1 while raising. It is NOT reset on stop, so pulses
# from the motor coasting after it stops still count in the right direction.
claw_direction = 1

def encoder_pulse(channel):
    """Runs automatically (in the background) every time the sensor sends a pulse."""
    global encoder_count
    with encoder_lock:
        encoder_count += claw_direction

def get_count():
    with encoder_lock:
        return encoder_count
# --------------------------------------------------------

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

# Rotation sensor input. The pull-up keeps the pin from "floating" when the
# sensor isn't pulling it low. bouncetime (ms) filters electrical noise;
# lower it if counts seem low when the motor spins fast.
GPIO.setup(ENCODER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(ENCODER_PIN, GPIO.RISING, callback=encoder_pulse, bouncetime=1)

def motorClaw_forward():
    GPIO.output(m1, GPIO.HIGH)
    GPIO.output(m2, GPIO.LOW)

def motorClaw_backward():
    GPIO.output(m1, GPIO.LOW)
    GPIO.output(m2, GPIO.HIGH)
    
def motorClaw_stop():
    GPIO.output(m1, GPIO.LOW)
    GPIO.output(m2, GPIO.LOW)

def runClawUntil(isDone, maxTime, label):
    """Keep the claw motor running until isDone() is True, the time limit
    is hit, or the pulses stop coming (stall). Then stop the motor."""
    start = time.time()
    lastCount = get_count()
    lastChange = start
    while not isDone():
        now = time.time()
        count = get_count()
        if count != lastCount:
            lastCount = count
            lastChange = now
        if now - start > maxTime:
            print(label, "- time limit reached, stopping (count =", count, ")")
            break
        if now - lastChange > STALL_TIMEOUT:
            print(label, "- no pulses, motor stalled or sensor problem (count =", count, ")")
            break
        sleep(.005)
    motorClaw_stop()
    print(label, "done, count =", get_count())

def lowerClaw():
    global claw_direction, encoder_count
    with encoder_lock:
        encoder_count = 0          # claw is fully up at the start of every drop
    claw_direction = 1
    motorClaw_forward()
    runClawUntil(lambda: get_count() >= DROP_PULSES, MAX_DROP_TIME, "Lowering")

def raiseClaw():
    global claw_direction
    claw_direction = -1
    motorClaw_backward()
    # Wind back up the same number of turns it went down (coasting included)
    runClawUntil(lambda: get_count() <= 0, MAX_RAISE_TIME, "Raising")

def dropClaw():
    lowerClaw()
    sleep(1)                       # let it settle; any coasting pulses still get counted
    GPIO.output(clawGrab, True)
    sleep(.1)
    raiseClaw()
    prizeDrop()
    
def prizeDrop():
    # CCW or CW for direction to home
    GPIO.output(DIR1,CCW)
    GPIO.output(DIR2,CW)
    homeReachedX = False
    homeReachedY = False
    # keep going until BOTH axes are home
    while not (homeReachedX and homeReachedY):
        if  not homeReachedX and bumperTest(CCW,1) <.9:
            stepperMoveNoJoy(CCW,1)
        elif not homeReachedX:
            print("Reached Home in X direction")
            homeReachedX = True
            
        if  not homeReachedY and bumperTest(CW,2) <.9:
            stepperMoveNoJoy(CW,2)
        elif not homeReachedY:
            print("Reached Home in y direction")
            homeReachedY = True
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
    bumperSafe3 = buttons[4]
    bumperSafe4 = buttons[3]
    if (theDirection == 1) and (motorNum ==1):
        return bumperSafe1
    if (theDirection == 0) and (motorNum ==1):
        return bumperSafe2
    if (theDirection == 1) and (motorNum ==2):
        return bumperSafe3
    if (theDirection == 0) and (motorNum ==2):
        return bumperSafe4

    return 0

def stepperMoveNoJoy(TheDirection,motorNum):
    """Change Direction: Changing direction requires time to switch. The
    time is dictated by the stepper motor and controller. """
    if motorNum == 1:
        #Esablish the direction you want to go
        GPIO.output(DIR1,TheDirection)
    else:
        GPIO.output(DIR2,TheDirection)
    for x in range(sensitivityNum):
        GPIO.output(gamePower, False)
        sleep(speeds)
        GPIO.output(gamePower,True)
        pygame.event.pump()            
       
        if motorNum == 1:
            if bumperTest(TheDirection,motorNum) <.9:
                GPIO.output(STEP1,GPIO.HIGH)
                sleep(speeds) # Dictates how fast stepper motor will run
                GPIO.output(STEP1,GPIO.LOW)
                sleep(speeds-speeds*delayRatio)
            else:
                print("NOT SAFE")
                break
        if motorNum == 2:
            if bumperTest(TheDirection,motorNum) <.9:
                GPIO.output(STEP2,GPIO.HIGH)
                sleep(speeds) # Dictates how fast stepper motor will run
                GPIO.output(STEP2,GPIO.LOW)
                sleep(speeds-speeds*delayRatio)
            else:
                print("NOT SAFE")
                break

def stepperMove(TheDirection,motorNum):
    """Change Direction: Changing direction requires time to switch. The
    time is dictated by the stepper motor and controller. """
    if motorNum == 1:
        #Esablish the direction you want to go
        GPIO.output(DIR1,TheDirection)
    else:
        GPIO.output(DIR2,TheDirection)
    for x in range(sensitivityNum):
        GPIO.output(gamePower, False)
        sleep(speeds)
        GPIO.output(gamePower,True)
        pygame.event.pump()            
        axis = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        if all(abs(a) < 0.1 for a in axis):
            # Stop motor if joystick is at center position
            break
        
        if motorNum == 1:
            if bumperTest(TheDirection,motorNum) <.9:
                GPIO.output(STEP1,GPIO.HIGH)
                sleep(speeds) # Dictates how fast stepper motor will run
                GPIO.output(STEP1,GPIO.LOW)
                sleep(speeds-speeds*delayRatio)
            else:
                print("NOT SAFE")
                break
        if motorNum == 2:
            if bumperTest(TheDirection,motorNum) <.9:
                GPIO.output(STEP2,GPIO.HIGH)
                sleep(speeds) # Dictates how fast stepper motor will run
                GPIO.output(STEP2,GPIO.LOW)
                sleep(speeds-speeds*delayRatio)
            else:
                print("NOT SAFE")
                break

def main():
    try:
        p = vlc.MediaPlayer("/media/stiefeladam/068F-EE41/arcade.mp3")
        
        GPIO.output(clawGrab, True)
        motorClaw_stop()
        gamePlaying = False
        timer_active = False
        timer_start = 0
        timerLength = 30000 # 30 seconds
        pygame.event.pump()           
        GPIO.output(gamePower, False)
        sleep(2)
        GPIO.output(clawGrab, False)
        sleep(2)    
        while True:
            pygame.event.get()
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
                p.play()
            if gamePlaying:
                if buttons[5] >= .9:
                    timer_active = False
                    gamePlaying = False
                    dropClaw()
                if axes[0] == -1:
                    print("Right - CW")              
                    stepperMove(CW,1)
                if axes[0] >= .9:
                    print("Left- CCW")
                    stepperMove(CCW,1)
                if axes[1] == -1:
                    print("Down - CCW")
                    stepperMove(CW,2)
                if axes[1] >= .9:
                    print("Up - CW")
                    stepperMove(CCW,2)
            if timer_active and pygame.time.get_ticks() - timer_start >= timerLength:  # 30 seconds
                gamePlaying = False
                timer_active = False
                GPIO.output(gamePower, False)
                p.stop()
            if timer_active:
                print("{:.0f}".format((pygame.time.get_ticks() - timer_start)/1000))
            pygame.time.wait(100)
    except KeyboardInterrupt:
        pass
    finally:
        motorClaw_stop()
        GPIO.cleanup()
        pygame.quit()

if __name__=="__main__":
    main()
