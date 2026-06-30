import RPi.GPIO as GPIO
import time

# ��������� GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ���� ����������� (������)
IN1 = 17  # ����� �����
IN2 = 27
ENA = 18  # PWM �����

IN3 = 22  # ������ �����
IN4 = 23
ENB = 12  # PWM ������

# ��������� ����� ��� ������
motor_pins = [IN1, IN2, ENA, IN3, IN4, ENB]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# �������� ���-��������
pwm_left = GPIO.PWM(ENA, 100)  # ������� 100 ��
pwm_right = GPIO.PWM(ENB, 100)

pwm_left.start(0)
pwm_right.start(0)


def stop():
    GPIO.output(IN1, False)
    GPIO.output(IN2, False)
    GPIO.output(IN3, False)
    GPIO.output(IN4, False)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)

def forward(speed=30):
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def slow_left(speed=30, turn_speed=20):
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)
    pwm_left.ChangeDutyCycle(turn_speed)
    pwm_right.ChangeDutyCycle(speed)

def slow_right(speed=30, turn_speed=20):
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(turn_speed)


try:
    slow_left(20)
    time.sleep(60)

finally:
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
