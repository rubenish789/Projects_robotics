import RPi.GPIO as GPIO
import time

# === BCM ===
IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23
ENA = 18  # PWM
ENB = 12  # PWM

# === Sensors ===
LEFT_SENSOR = 5
MIDDLE_SENSOR = 6
RIGHT_SENSOR = 13

# === PWM ===
SPEED_NORMAL = 50
SPEED_TURN = 50
SPEED_SLIGHT = 50

# === GPIO ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup motor pins
motor_pins = [IN1, IN2, IN3, IN4, ENA, ENB]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# Setup sensor pins
sensor_pins = [LEFT_SENSOR, MIDDLE_SENSOR, RIGHT_SENSOR]
for pin in sensor_pins:
    GPIO.setup(pin, GPIO.IN)

# PWM setup
pwm_left = GPIO.PWM(ENA, 1000)
pwm_right = GPIO.PWM(ENB, 1000)
pwm_left.start(0)
pwm_right.start(0)

# Motor control function with inverted directions
def set_motors(lf, lb, rf, rb, l_speed, r_speed):
    GPIO.output(IN1, lf)
    GPIO.output(IN2, lb)
    GPIO.output(IN3, rf)
    GPIO.output(IN4, rb)
    pwm_left.ChangeDutyCycle(l_speed)
    pwm_right.ChangeDutyCycle(r_speed)

# Inverted movement functions
def forward():
    set_motors(0, 1, 0, 1, SPEED_NORMAL, SPEED_NORMAL)  # INVERTED: 1 -> 0, 0 -> 1

def slight_left():
    set_motors(0, 1, 0, 1, SPEED_SLIGHT, SPEED_NORMAL)  # INVERTED: 1 -> 0, 0 -> 1

def slight_right():
    set_motors(0, 1, 0, 1, SPEED_NORMAL, SPEED_SLIGHT)  # INVERTED: 1 -> 0, 0 -> 1

def hard_left():
    set_motors(1, 0, 0, 1, SPEED_TURN, SPEED_TURN)  # INVERTED: 0 -> 1, 1 -> 0

def hard_right():
    set_motors(0, 1, 1, 0, SPEED_TURN, SPEED_TURN)  # INVERTED: 0 -> 1, 1 -> 0

def stop():
    set_motors(0, 0, 0, 0, 0, 0)

# Line Follower with inverted movement
running = True

def line_follower():
    global running
    running = True
    try:
        while running:
            left = GPIO.input(LEFT_SENSOR)
            middle = GPIO.input(MIDDLE_SENSOR)
            right = GPIO.input(RIGHT_SENSOR)

            if middle == 1 and left == 0 and right == 0:
                forward()
            elif middle == 1 and left == 1 and right == 0:
                slight_left()
            elif middle == 1 and left == 0 and right == 1:
                slight_right()
            elif middle == 0 and left == 1:
                hard_left()
            elif middle == 0 and right == 1:
                hard_right()
            else:
                stop()

            time.sleep(0.05)

    except Exception as e:
        print("Error in line follower:", e)
        stop()

def stop_line_follower():
    global running
    running = False
    stop()

line_follower()
