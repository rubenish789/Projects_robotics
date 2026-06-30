# 🚗 Wi-Fi Controlled Robot Car

A Raspberry Pi based robotic car that can be controlled through a web browser over Wi-Fi. The project supports both **manual remote control** and **autonomous line following** modes.

## Features

- 🌐 Web-based control interface
- 📡 Wi-Fi remote control
- 🤖 Line Follower mode
- 🔄 Switch between Manual and Autonomous modes
- ⚡ Real-time motor control using Raspberry Pi GPIO
- 🐍 Built with Python and Flask

---

## Project Structure

```
car_wifi_control/
│
├── app.py                  # Main Flask application
├── motor_control.py        # GPIO motor control
├── line_follower.py        # Line following algorithm
├── templates/
│   └── index.html          # Web interface
├── line.py
├── mot.py
├── server.py               # Older development version
└── ...
```

---

## Technologies

- Python 3
- Flask
- Raspberry Pi GPIO
- HTML
- JavaScript (Fetch API)

---

## Hardware Requirements

- Raspberry Pi
- Motor Driver (L298N or similar)
- DC Motors
- Chassis
- Line Tracking Sensors
- Power Supply
- Wi-Fi connection

---

## GPIO Pin Configuration

| Motor | GPIO Pins |
|--------|-----------|
| Left Motor | GPIO 17, GPIO 27 |
| Right Motor | GPIO 22, GPIO 23 |

The GPIO configuration can be modified inside `motor_control.py`.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/car_wifi_control.git
cd car_wifi_control
```

Install dependencies:

```bash
pip install flask RPi.GPIO
```

---

## Running the Project

Start the Flask server:

```bash
python app.py
```

Open a browser and navigate to:

```
http://<RaspberryPi_IP>:5000
```

Example:

```
http://192.168.1.100:5000
```

---

## Operating Modes

### 🎮 Remote Control

The robot is controlled directly from the web interface.

Available commands:

- Forward
- Backward
- Left
- Right
- Stop

---

### 🤖 Line Follower

In this mode the robot automatically follows a line using tracking sensors.

The mode can be activated directly from the web interface.

---

## Web Interface

The browser interface provides:

- Direction control buttons
- Mode switching button
- Current operating mode display

---

## Future Improvements

- PWM motor speed control
- Live camera streaming
- Obstacle avoidance
- Mobile-friendly interface
- Battery level monitoring
- PID-based line following
- WebSocket communication for lower latency

---

## License

This project is created for educational purposes.
