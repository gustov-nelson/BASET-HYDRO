from flask import Flask, render_template, request, Response, jsonify
from camera import VideoCamera
import time
import serial
import RPi.GPIO as GPIO
from extras import setup_gpio, grap_prices
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "admin": "password",
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username



# Initialize GPIO
"""GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.OUT, initial=GPIO.LOW)  # VDC
GPIO.setup(3, GPIO.OUT, initial=GPIO.LOW)  # Lights
GPIO.setup(4, GPIO.OUT, initial=GPIO.LOW)  # Pump
GPIO.setup(17, GPIO.OUT, initial=GPIO.LOW)  # Water Heater
GPIO.setup(27, GPIO.OUT, initial=GPIO.LOW)  # Heater
GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)  # Acid
GPIO.setup(10, GPIO.OUT, initial=GPIO.LOW)  # Base
GPIO.setup(9, GPIO.OUT, initial=GPIO.LOW)  # Nutrients
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)  # Fan
"""
# Initial GPIO
setup_gpio

# Initialize Serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.flush()

# Global variables
temp = 0.0
pH = 0.0
ec = 0.0

pH_high = 0.0
pH_low = 0.0
ec_high = 0.0
ec_low = 0.0
water_temp_high = 0.0
water_temp_low = 0.0
light_timer = 0

light_state = True
pump_state = True
heater_state = True
VDC_state = True
fan_state = True

# To access the website
@app.route('/')
@auth.login_required
def index():
        return render_template('index.html')


# To change the parameters of the automatic devices
@app.route('/settings', methods=['GET', 'POST'])
@auth.login_required
def settings():
    global pH_high, pH_low, ec_high, ec_low, water_temp_high, water_temp_low
    if request.method == 'POST':
        pH_high = float(request.form['pH_high'])
        pH_low = float(request.form['pH_low'])
        ec_high = float(request.form['ec_high'])
        ec_low = float(request.form['ec_low'])
        water_temp_high = float(request.form['water_temp_high'])
        water_temp_low = float(request.form['water_temp_low'])
        light_timer = int(request.form['light_timer'])
    return render_template('settings.html', pH_high=pH_high, pH_low=pH_low, ec_high=ec_high, ec_low=ec_low, water_temp_high=water_temp_high, water_temp_low=water_temp_low, light_timer=light_timer)

# This changes the 'state' of each device based on a checkbox from the appropiate webpage
@app.route('/control', methods=['GET', 'POST'])
@auth.login_required
def control():
    global light_state, pump_state, heater_state, VDC_state, fan_state
    if request.method == 'POST':
        light_state = request.form.get('light_state') == 'True'
        pump_state = request.form.get('pump_state') == 'True'
        heater_state = request.form.get('heater_state') == 'True'
        VDC_state = request.form.get('VDC_state') == 'True'
        fan_state = request.form.get('fan_state') == 'True'
    return render_template('control.html', light_state=light_state, pump_state=pump_state, heater_state=heater_state, VDC_state=VDC_state, fan_state=fan_state)


# To display the BOM and estimated cost:
@app.route('/products')
@auth.login_required
def product_list():
    products= grap_prices()
    return render_template('bom.html', products=products)

@app.route('/livefeed')
@auth.login_required
def live_feed():
    return render_template('livefeed.html')

# Turns the devices on and off based on the states set by the html webpage.
# Everything will always be on if checked except for the lights, which are also controlled by a timer.

def device_control():
    GPIO.output(3, GPIO.HIGH if light_state else GPIO.LOW)
    GPIO.output(4, GPIO.HIGH if pump_state else GPIO.LOW)
    GPIO.output(27, GPIO.HIGH if heater_state else GPIO.LOW)
    GPIO.output(2, GPIO.HIGH if VDC_state else GPIO.LOW)
    GPIO.output(11, GPIO.HIGH if fan_state else GPIO.LOW)

# Reads the incoming serial data from the Arduino and updates the variables 
def read_serial():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            temp, pH, ec = map(float, line.split('X'))

# Adds acid, base or nutrients as needed
def add_buffer():
    ec_target = (ec_high + ec_low) / 2
    while True:
        if ec < ec_target:
            GPIO.output(9, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(9, GPIO.LOW)
        if pH <= (pH_low + 0.5):
            GPIO.output(10, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(10, GPIO.LOW)
        elif pH >= (pH_high - 0.5):
            GPIO.output(22, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(22, GPIO.LOW)
        time.sleep(600)


# Turns the lights on and off based on the time
def light_timer_control(light_timer, light_state):
    while True:
        # only control the lights based on time if light_state is True
        if light_state:
            current_hour = datetime.datetime.now().hour
            if current_hour < light_timer:
                GPIO.output(Lights, GPIO.HIGH)
            else:
                GPIO.output(Lights, GPIO.LOW)
        else:
            GPIO.output(Lights, GPIO.LOW)  # if light_state is False, turn off the lights
        time.sleep(1)


if __name__ == '__main__':
    read_serial_thread = threading.Thread(target=read_serial)
    read_serial_thread.start()
    add_buffer_thread = threading.Thread(target=add_buffer)
    add_buffer_thread.start()
    light_timer_thread = threading.Thread(target=light_timer_control)
    light_timer_thread.start()
    device_control_thread = threading.Thread(target=device_control)
    device_control_thread.start()
    app.run(host='0.0.0.0', port='5000', threaded=True)
