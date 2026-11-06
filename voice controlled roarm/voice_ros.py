#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_serial_ros.py
Voice -> Serial controller for RoArm M2 + ROS2 publisher for /joint_states (Isaac Sim).
Features:
 - VOSK offline recognition (rus)
 - numbers as digits and words (русские числа)
 - absolute commands for shoulder/elbow inverted (минус -> опустить)
 - relative commands ("подними"/"опусти") use REL_STEP_DEG
 - safe serial open, graceful shutdown
 - publishes JointState: ["base_to_L1","L1_to_L2","L2_to_L3","L3_to_L4"]
"""

import json
import math
import time
import signal
import sys
import re

# audio / vosk / serial
import pyaudio
from vosk import Model, KaldiRecognizer
import serial

# try import rclpy (optional fallback if ROS2 not available)
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    ROS_AVAILABLE = True
except Exception:
    ROS_AVAILABLE = False

# ---------------- CONFIG ----------------
SERIAL_PORT = "/dev/ttyUSB1"
BAUDRATE = 115200

SPD_DEFAULT = 700
ACC_DEFAULT = 700

MODEL_PATH = "model"
RATE = 16000
CHUNK = 4000

# Steps
BASE_STEP_DEG = 20.0       # шаг для влево/вправо
REL_STEP_DEG = 15.0        # шаг для подними/опусти

# Limits (radians) — из документации RoArm
JOINT_LIMITS_RAD = {
    "base_to_L1": (-math.pi, math.pi),
    "L1_to_L2": (-math.pi/2, math.pi/2),
    "L2_to_L3": (-1.11, math.pi),
    "L3_to_L4": (1.08, 3.14),
}

# Hand mapping constants
HAND_ISAAC_MIN = math.radians(-135.0)
HAND_ISAAC_MAX = 0.0
HAND_M2_OPEN = 1.08
HAND_M2_CLOSED = 3.14

# ----------------------------------------

running = True
ros_node = None  # will hold ROS publisher node if available


def signal_handler(sig, frame):
    global running
    print("\n[main] received interrupt, stopping...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


def deg2rad(d): return d * math.pi / 180.0


def clamp_rad(name: str, rad: float) -> float:
    if name in JOINT_LIMITS_RAD:
        low, high = JOINT_LIMITS_RAD[name]
        return max(low, min(high, rad))
    return rad


def map_isaac_hand_to_m2(isaac_rad: float) -> float:
    r = max(HAND_ISAAC_MIN, min(HAND_ISAAC_MAX, isaac_rad))
    t = (r - HAND_ISAAC_MIN) / (HAND_ISAAC_MAX - HAND_ISAAC_MIN)
    return HAND_M2_OPEN + t * (HAND_M2_CLOSED - HAND_M2_OPEN)


def safe_open_serial(port, baud, timeout=0.1):
    try:
        s = serial.Serial(port, baud, timeout=timeout)
        print(f"[serial] opened {port} @{baud}")
        return s
    except Exception as e:
        print(f"[serial] open failed: {e} — will run without serial (only logging)")
        return None


# --- ROS2 wrapper node (simple publisher) ---
if ROS_AVAILABLE:
    class RosPublisher(Node):
        def __init__(self):
            super().__init__("voice_joint_publisher")
            self.pub = self.create_publisher(JointState, "/joint_states", 10)

        def publish_joints(self, base, shoulder, elbow, hand):
            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = ["base_to_L1", "L1_to_L2", "L2_to_L3", "L3_to_L4"]
            msg.position = [base, shoulder, elbow, hand]
            self.pub.publish(msg)
else:
    RosPublisher = None


def send_angles(ser, base, shoulder, elbow, hand, spd=SPD_DEFAULT, acc=ACC_DEFAULT):
    """Send JSON to serial and publish same values to ROS (if available)."""
    payload = {
        "T": 102,
        "base": base,
        "shoulder": shoulder,
        "elbow": elbow,
        "hand": hand,
        "spd": spd,
        "acc": acc
    }
    text = json.dumps(payload) + "\n"

    if ser and getattr(ser, "is_open", False):
        try:
            ser.write(text.encode("utf-8"))
            print("[serial] Sent:", text.strip())
        except Exception as e:
            print("[serial] Write failed:", e)
    else:
        print("[serial] (mock) Sent:", text.strip())

    # Publish to ROS if node exists
    if ros_node is not None:
        try:
            ros_node.publish_joints(base, shoulder, elbow, hand)
        except Exception as e:
            print("[ros] publish failed:", e)


# --- Русский words->number (поддержка до тысяч) ---
_UNITS = {
    "ноль": 0, "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9
}
_TEENS = {
    "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13, "четырнадцать": 14,
    "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18, "девятнадцать": 19
}
_TENS = {
    "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90
}
_HUNDREDS = {
    "сто": 100, "двести": 200, "триста": 300, "четыреста": 400,
    "пятьсот": 500, "шестьсот": 600, "семьсот": 700, "восемьсот": 800, "девятьсот": 900
}
_MULTIPLIERS = {"тысяча": 1000, "тысячи": 1000, "тысяч": 1000}


def words_to_number_ru(text: str):
    """Пытаемся распарсить число, написанное словами (рус.). Возвращаем int или None."""
    tokens = re.findall(r"[а-яА-ЯёЁ\-]+", text.lower())
    if not tokens:
        return None
    total = 0
    current = 0
    negative = False
    found_any = False
    for tok in tokens:
        if tok in ("минус", "−"):
            negative = True
            found_any = True
            continue
        if tok in _HUNDREDS:
            current += _HUNDREDS[tok]; found_any = True; continue
        if tok in _TENS:
            current += _TENS[tok]; found_any = True; continue
        if tok in _TEENS:
            current += _TEENS[tok]; found_any = True; continue
        if tok in _UNITS:
            current += _UNITS[tok]; found_any = True; continue
        if tok in _MULTIPLIERS:
            mult = _MULTIPLIERS[tok]
            if current == 0:
                current = 1
            total += current * mult
            current = 0
            found_any = True
            continue
        # ignore other words
    total += current
    if not found_any:
        return None
    return -total if negative else total


def parse_number(text: str):
    """
    Находит первое число (целое или десятичное) и возвращает (float, is_percent).
    Поддерживает цифры и слова по-русски.
    """
    # проценты с цифрами
    p = re.search(r"(-?\d+(\.\d+)?)\s*%", text)
    if p:
        return float(p.group(1)), True

    # числа в цифрах (первое вхождение)
    m = re.search(r"(-?\d+(\.\d+)?)", text)
    if m:
        return float(m.group(1)), False

    # пробуем слова
    n = words_to_number_ru(text)
    if n is not None:
        return float(n), False

    return None, False


def main():
    global ros_node

    # init VOSK
    print("[vosk] loading model...")
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, RATE)

    # init ROS if available
    if ROS_AVAILABLE:
        try:
            rclpy.init()
            ros_node = RosPublisher()
            print("[ros] initialized publisher node")
        except Exception as e:
            print("[ros] failed to init: ", e)
            ros_node = None
    else:
        print("[ros] ROS2 not available — running without ROS publishing")

    # open serial
    ser = safe_open_serial(SERIAL_PORT, BAUDRATE)

    # audio init
    pa = pyaudio.PyAudio()
    try:
        stream = pa.open(
            rate=RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print("[audio] failed to open input stream:", e)
        if ser:
            ser.close()
        pa.terminate()
        if ROS_AVAILABLE:
            try: rclpy.shutdown()
            except: pass
        return

    print("Говори. Примеры команд:")
    print("  'домой', 'открыть', 'закрыть', 'влево', 'вправо'")
    print("  'подними локоть', 'опусти локоть', 'подними плечо', 'опусти плечо'")
    print("  'локоть 30' или 'локоть тридцать' (числа в градусах)")
    print("  'рука 50' — процент (0=open,100=closed)")
    print("  'скорость 500', 'ускорение 300', 'стоп'")

    # текущие состояния (радианы)
    base = 0.0
    shoulder = 0.0
    elbow = 1.57
    hand = HAND_M2_CLOSED
    spd = SPD_DEFAULT
    acc = ACC_DEFAULT

    try:
        while running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except IOError as e:
                print("[audio] read error:", e)
                continue
            except Exception as e:
                if not running:
                    break
                print("[audio] unexpected error:", e)
                break

            if rec.AcceptWaveform(data):
                res = rec.Result()
                try:
                    j = json.loads(res)
                    text = j.get("text", "").strip()
                except Exception:
                    text = ""
                if not text:
                    continue

                print("Вы сказали:", text)
                num, is_pct = parse_number(text)

                # HOME
                if "домой" in text:
                    base, shoulder, elbow, hand = 0.0, 0.0, 1.57, HAND_M2_CLOSED
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue

                # HAND
                if "открыть" in text and ("рук" in text or "рука" in text or text == "открыть"):
                    hand = HAND_M2_OPEN
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue
                if "закрыть" in text and ("рук" in text or "рука" in text or text == "закрыть"):
                    hand = HAND_M2_CLOSED
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue
                if ("рука" in text or "кисть" in text or "клещ" in text) and num is not None:
                    pct = max(0.0, min(100.0, num)) if not is_pct else max(0.0, min(100.0, num))
                    isaac = HAND_ISAAC_MIN + (pct/100.0) * (HAND_ISAAC_MAX - HAND_ISAAC_MIN)
                    m2 = map_isaac_hand_to_m2(isaac)
                    hand = clamp_rad("L3_to_L4", m2)
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue

                # BASE absolute or step
                if ("база" in text or "осн" in text) and num is not None:
                    r = deg2rad(num)
                    base = clamp_rad("base_to_L1", r)
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue
                if "влево" in text:
                    base = clamp_rad("base_to_L1", base + deg2rad(BASE_STEP_DEG))
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue
                if "вправо" in text:
                    base = clamp_rad("base_to_L1", base - deg2rad(BASE_STEP_DEG))
                    send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                    continue

                # SHOULDER (L1_to_L2)
                if ("плечо" in text or "плеч" in text):
                    if num is not None:
                        # invert absolute: человек говорит "-30" -> опустить -> внутренняя логика invert
                        corrected = -num
                        r = deg2rad(corrected)
                        shoulder = clamp_rad("L1_to_L2", r)
                        send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                        continue
                    # relative inverted: 'подними' -> decrease angle, 'опусти' -> increase angle
                    if "подним" in text or "вверх" in text:
                        shoulder = clamp_rad("L1_to_L2", shoulder - deg2rad(REL_STEP_DEG))
                        send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                        continue
                    if "опуст" in text or "вниз" in text:
                        shoulder = clamp_rad("L1_to_L2", shoulder + deg2rad(REL_STEP_DEG))
                        send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                        continue

                # ELBOW (L2_to_L3)
                if ("локоть" in text or "лок" in text):
                    if num is not None:
                        # invert absolute
                        corrected = -num
                        r = deg2rad(corrected)
                        elbow = clamp_rad("L2_to_L3", r)
                        send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                        continue
                    # relative inverted: 'подними' -> decrease angle, 'опусти' -> increase angle
                    if "подним" in text or "вверх" in text:
                        elbow = clamp_rad("L2_to_L3", elbow - deg2rad(REL_STEP_DEG))
                        send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                        continue
                    if "опуст" in text or "вниз" in text:
                        elbow = clamp_rad("L2_to_L3", elbow + deg2rad(REL_STEP_DEG))
                        send_angles(ser, base, shoulder, elbow, hand, spd=spd, acc=acc)
                        continue

                # speed/acc
                if "скорость" in text and num is not None:
                    spd = max(0, int(num))
                    print(f"[cfg] speed set to {spd}")
                    continue
                if "ускорени" in text and num is not None:
                    acc = max(0, int(num))
                    print(f"[cfg] acc set to {acc}")
                    continue

                # stop (send current with spd=0, acc=0)
                if "стоп" in text:
                    send_angles(ser, base, shoulder, elbow, hand, spd=0, acc=0)
                    continue

                print("[voice] команда не распознана")

            else:
                # partial = rec.PartialResult()  # можно выводить если нужно
                pass

    finally:
        # cleanup audio
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        pa.terminate()

        # cleanup serial
        if ser:
            try:
                ser.close()
                print("[serial] closed.")
            except Exception:
                pass

        # shutdown ROS
        if ROS_AVAILABLE and ros_node is not None:
            try:
                ros_node.destroy_node()
                rclpy.shutdown()
                print("[ros] shutdown complete")
            except Exception:
                pass

        print("[main] stopped, exiting.")


if __name__ == "__main__":
    main()
