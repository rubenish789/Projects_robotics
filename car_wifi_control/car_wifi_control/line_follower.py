import RPi.GPIO as GPIO
import time

# === ���� ������� (BCM) ===
IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23
ENA = 18  # PWM ����� �����
ENB = 12  # PWM ������ �����

# === ���� �������� (BCM) ===
LEFT_SENSOR = 5
MIDDLE_SENSOR = 6
RIGHT_SENSOR = 13

# === �������� ===
SPEED_NORMAL = 34  # �������� ��� �������� ������
SPEED_TURN = 50       # �������� ����� � ������
SPEED_PUSH = 60     # �������� ������ � ������

# === GPIO setup ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ��������� ����� �������
motor_pins = [IN1, IN2, IN3, IN4, ENA, ENB]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# ��������� ����� ��������
sensor_pins = [LEFT_SENSOR, MIDDLE_SENSOR, RIGHT_SENSOR]
for pin in sensor_pins:
    GPIO.setup(pin, GPIO.IN)

# PWM
pwm_left = GPIO.PWM(ENA, 1000)
pwm_right = GPIO.PWM(ENB, 1000)
pwm_left.start(0)
pwm_right.start(0)

# ���������� ��������
def set_motors(lf, lb, rf, rb, l_speed, r_speed):
    GPIO.output(IN1, lf)
    GPIO.output(IN2, lb)
    GPIO.output(IN3, rf)
    GPIO.output(IN4, rb)
    pwm_left.ChangeDutyCycle(l_speed)
    pwm_right.ChangeDutyCycle(r_speed)

def forward():
    set_motors(0, 1, 0, 1, SPEED_NORMAL, SPEED_NORMAL)

def push_forward():
    set_motors(0, 1, 0, 1, SPEED_PUSH, SPEED_PUSH)
    time.sleep(0.2)
    set_motors(0, 1, 0, 1, SPEED_NORMAL, SPEED_NORMAL)

def left_turn():
    set_motors(0, 1, 0, 0, SPEED_TURN, 0)

def right_turn():
    set_motors(0, 1, 0, 1, 0, SPEED_TURN)

def hard_left():
    set_motors(1, 0, 0, 1, SPEED_TURN, SPEED_TURN)

def hard_right():
    set_motors(0, 1, 1, 0, SPEED_TURN, SPEED_TURN)

def stop():
    set_motors(0, 0, 0, 0, 0, 0)

running = True
first_push_done = False

# �������� ������� Line Follower
def line_follower():
    global running, first_push_done
    running = True
    first_push_done = False

    try:
        while running:
            left = GPIO.input(LEFT_SENSOR)
            right = GPIO.input(RIGHT_SENSOR)

            if left == 0 and right == 0:
                if not first_push_done:
                    push_forward()
                    first_push_done = True
                else:
                    forward()

            elif left == 1 and right == 0:
                left_turn()
                first_push_done = True  # ��� ����������, ����� ������ �����
            elif left == 0 and right == 1:
                right_turn()
                first_push_done = True
            else:
                forward()
                first_push_done = False  # ��������, ������� � ����� � ��������� � ������ ������

            time.sleep(0.05)

    except Exception as e:
        print("������ � line follower:", e)
        stop()

# ������
line_follower()
