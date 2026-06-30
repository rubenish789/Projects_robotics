
from flask import Flask, render_template, request, redirect
from motor_control import forward, backward, left, right, stop
import threading
import time

app = Flask(__name__)


current_mode = 'remote'
line_thread = None
line_active = False


@app.route('/')
def index():
    return render_template('index.html', mode=current_mode)


@app.route('/mode', methods=['POST'])
def switch_mode():
    global current_mode, line_thread, line_active

    if current_mode == 'remote':
        current_mode = 'line'
        line_active = True
        line_thread = threading.Thread(target=line_follower)
        line_thread.start()
    else:
        current_mode = 'remote'
        line_active = False 

    return redirect('/')


@app.route('/move', methods=['POST'])
def move():
    if current_mode != 'remote':
        return '', 204

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


def line_follower():
    while line_active:
       
        sensors = read_sensors()
        if sensors == [0, 1, 0]:
            forward()
        elif sensors == [1, 0, 0]:
            left()
        elif sensors == [0, 0, 1]:
            right()
        else:
            stop()

        time.sleep(0.05)  

    stop()  


def read_sensors():
    
    
    return [0, 1, 0]  


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""
from flask import Flask, render_template, request, redirect
from motor_control import forward, backward, left, right, stop

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
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
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""
