from flask import Flask, render_template, request, jsonify
import threading
import time

from motor_control import forward, backward, left, right, stop
from line_follower import line_follower, stop_line_follower

app = Flask(__name__)

current_mode = 'remote'
follower_thread = None

@app.route('/')
def index():
    return render_template('index.html', mode=current_mode)

@app.route('/move', methods=['POST'])
def move():
    global current_mode
    if current_mode != 'remote':
        return jsonify({'error': 'Not in remote mode'}), 400

    direction = request.form['direction']
    if direction == 'forward':
        forward()
    elif direction == 'backward':
        backward()
    elif direction == 'left':
        left()
    elif direction == 'right':
        right()
    elif direction == 'stop':
        stop()
    return '', 204

@app.route('/mode', methods=['POST'])
def set_mode():
    global current_mode, follower_thread

    data = request.get_json()
    mode = data.get('mode', 'remote')

    if mode == current_mode:
        return jsonify({'status': 'same mode'})

    current_mode = mode

    if mode == 'line':
        stop()
        follower_thread = threading.Thread(target=line_follower)
        follower_thread.start()
        print("Line Follower started")
    else:
        stop_line_follower()
        print("Switched to Remote Control")

    return jsonify({'status': 'mode set'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
