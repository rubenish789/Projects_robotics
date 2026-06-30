import RPi.GPIO as GPIO
import time

SENSOR_PIN1 = 5
SENSOR_PIN2 = 6 
SENSOR_PIN3 = 13 

GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN1, GPIO.IN)
GPIO.setup(SENSOR_PIN2, GPIO.IN)
GPIO.setup(SENSOR_PIN3, GPIO.IN)


try:
    while True:
        sensor1_value = GPIO.input(SENSOR_PIN1)
        sensor2_value = GPIO.input(SENSOR_PIN2)
        sensor3_value = GPIO.input(SENSOR_PIN3)
        
        
        print(f"SENSOR_PIN1: {sensor1_value}")
        print(f"SENSOR_PIN2: {sensor2_value}")
        print(f"SENSOR_PIN3: {sensor3_value}")
        
        time.sleep(0.5)
except KeyboardInterrupt:
    print("interrupted")
finally:
    GPIO.cleanup()

