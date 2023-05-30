from flask import Flask, render_template, request, Response, jsonify
#from camera import VideoCamera
import threading
import time
import serial
import cv2
import RPi.GPIO as GPIO
from extras import setup_gpio, grap_prices
from flask_httpauth import HTTPBasicAuth
import datetime
camera_index = 0
max_retries = 5


VDC = 14
Lights = 15
Pump = 18
Water_Heater = 23
Heater = 24
Fan = 25
Acid = 8
Base = 7
Nutrients = 1


# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(VDC, GPIO.OUT, initial=GPIO.HIGH)  # VDC
GPIO.setup(Lights, GPIO.OUT, initial=GPIO.HIGH)  # Lights
GPIO.setup(Pump, GPIO.OUT, initial=GPIO.HIGH)  # Pump
GPIO.setup(Water_Heater, GPIO.OUT, initial=GPIO.HIGH)  # Water Heater
GPIO.setup(Heater, GPIO.OUT, initial=GPIO.HIGH)  # Heater
GPIO.setup(Acid, GPIO.OUT, initial=GPIO.LOW)  # Acid
GPIO.setup(Base, GPIO.OUT, initial=GPIO.LOW)  # Base
GPIO.setup(Nutrients, GPIO.OUT, initial=GPIO.LOW)  # Nutrients
GPIO.setup(Fan, GPIO.OUT, initial=GPIO.HIGH)  # Fan


# Initialize Serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.flush()

# Global variables
temp = float(0.0)
pH = float(0.0)
ec = float(0.0)

pH_high = float(7.0)
pH_low = float(6.0)
ec_high = float(50)
ec_low = float(40)
water_temp_high = 0.0
water_temp_low = 0.0
light_timer_on = 0
light_timer_off = 20
light_state = True
pump_state = True
water_heater_state = True
heater_state = True
VDC_state = True
fan_state = True

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "admin": "password",
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username




def generate_frames():
    for i in range(max_retries):
        camera = cv2.VideoCapture(camera_index)
        if not camera.isOpened():
            print(f"Failed to open camera on try {i+1} of {max_retries}")
            time.sleep(1)  # Wait a bit before retrying
        else:
            break
    #camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
"""
# To access the website
@app.route('/')
@auth.login_required
def index():
        return render_template('combine.html')
    """

@app.route('/', methods=['GET','POST'])
@auth.login_required
def combine():
    global pH_high, pH_low, ec_high, ec_low, water_temp_high, water_temp_low, light_timer_on, light_timer_off, ec, pH, temp, light_state, pump_state, water_heater_state, VDC_state, fan_state, heater_state
    if request.method == 'POST':
        form_name = request.form.get('form_name')

        if form_name == 'settings':
            pH_high = float(request.form['pH_high'])
            pH_low = float(request.form['pH_low'])
            ec_high = float(request.form['ec_high'])
            ec_low = float(request.form['ec_low'])
            water_temp_high = float(request.form['water_temp_high'])
            water_temp_low = float(request.form['water_temp_low'])
            light_timer_on = int(request.form['light_timer_on'])
            light_timer_off = int(request.form['light_timer_off'])

        elif form_name == 'device_control':
            light_state = request.form.get('light_state') == 'on'
            pump_state = request.form.get('pump_state') == 'on'
            water_heater_state = request.form.get('water_heater_state') == 'on'
            VDC_state = request.form.get('VDC_state') == 'on'
            fan_state = request.form.get('fan_state') == 'on'
            heater_state = request.form.get('heater_state') == 'on'
    return render_template('combine.html',pH_high=pH_high, pH_low=pH_low, ec_high=ec_high, ec_low=ec_low, water_temp_high=water_temp_high, water_temp_low=water_temp_low, light_timer_on=light_timer_on, light_timer_off=light_timer_off,temp=temp,pH=pH,ec=ec, light_state=light_state,pump_state=pump_state,water_heater_state=water_heater_state,VDC_state=VDC_state,fan_state=fan_state,heater_state=heater_state)

# To change the parameters of the automatic devices
@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def settings():
    global pH_high, pH_low, ec_high, ec_low, water_temp_high, water_temp_low, light_timer_on, light_timer_off
    if request.method == 'POST':
        pH_high = float(request.form['pH_high'])
        pH_low = float(request.form['pH_low'])
        ec_high = float(request.form['ec_high'])
        ec_low = float(request.form['ec_low'])
        water_temp_high = float(request.form['water_temp_high'])
        water_temp_low = float(request.form['water_temp_low'])
        light_timer_on = int(request.form['light_timer_on'])
        light_timer_off = int(request.form['light_timer_off'])
    return render_template('settings.html', pH_high=pH_high, pH_low=pH_low, ec_high=ec_high, ec_low=ec_low, water_temp_high=water_temp_high, water_temp_low=water_temp_low, light_timer_on=light_timer_on, light_timer_off=light_timer_off,temp=temp,pH=pH,ec=ec,light_state=light_state, pump_state=pump_state, water_heater_state=water_heater_state, VDC_state=VDC_state, fan_state=fan_state)

'''# This changes the 'state' of each device based on a checkbox from the appropiate webpage
@app.route('/device-control', methods=['GET', 'POST'])
@auth.login_required
def control():
    global light_state, pump_state, water_heater_state, VDC_state, fan_state
    if request.method == 'POST':
        light_state = request.form.get('light_state') == 'on'
        pump_state = request.form.get('pump_state') == 'on'
        heater_state = request.form.get('water_heater_state') == 'on'
        VDC_state = request.form.get('VDC_state') == 'on'
        fan_state = request.form.get('fan_state') == 'on'
    return render_template('device_control.html', light_state=light_state, pump_state=pump_state, water_heater_state=water_heater_state, VDC_state=VDC_state, fan_state=fan_state)
'''
@app.route('/my_form', methods=['POST'])
def handle_form():
    checkbox_value = request.form.get('my_checkbox') is not None
    # If the checkbox is checked, checkbox_value will be True. Else, it will be False.
    return redirect(url_for('combine'))



# To display the BOM and estimated cost:
@app.route('/products')
@auth.login_required
def product_list():
    products= grap_prices()
    return render_template('bom.html', products=products)

@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Turns the devices on and off based on the states set by the html webpage.
# Everything will always be on if checked except for the lights, which are also controlled by a timer.

def device_control():
    global temp, ec, pH, light_state, pump_state, Water_Heater, VDC_state, fan_state
    while True:
        #GPIO.output(Lights, GPIO.HIGH if light_state else GPIO.LOW)
        GPIO.output(Pump, GPIO.HIGH if pump_state else GPIO.LOW)
        GPIO.output(Water_Heater, GPIO.HIGH if water_heater_state else GPIO.LOW)
        GPIO.output(VDC, GPIO.HIGH if VDC_state else GPIO.LOW)
        GPIO.output(Fan, GPIO.HIGH if fan_state else GPIO.LOW)
        GPIO.output(Heater, GPIO.HIGH if heater_state else GPIO.LOW)
        #print(temp)
        #print(ec)
        #print(pH)
        #time.sleep(5)

# Reads the incoming serial data from the Arduino and updates the variables 
def read_serial():
#    global temp, pH, ec
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            temp, pH, ec = map(float, line.split('X'))
            

# Adds acid, base or nutrients as needed
def add_buffer():
    global ec, pH, ec_high, ec_low, pH_high, pH_low
    ec_target = ((ec_high + ec_low) / 2)
    while True:
        ec_target = ((ec_high + ec_low) / 2)
#        print("ec: " + ec)
#        print("pH: " + pH)
#        print("ec high: " + ec_high)
#        print("ec low: " + ec_low)
#        print("ph high: " + pH_high)
#        print("ph low: " + pH_low)
        if ec < ec_target:
            GPIO.output(Nutrients, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(Nutrients, GPIO.LOW)
        if pH <= (pH_low + 0.5):
            GPIO.output(Base, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(Base, GPIO.LOW)
        if pH >= (pH_high - 0.5):
            GPIO.output(Acid, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(Acid, GPIO.LOW)
        time.sleep(1)

'''
# Turns the lights on and off based on the time
def light_timer_control():
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
'''
def light_timer_control():
    global light_timer_on, light_timer_off, light_state
    while True:
        # only control the lights based on time if light_state is True
        if light_state:
            current_hour = int(datetime.datetime.now().hour)
            
            # if current_hour is between light_timer_on and light_timer_off, considering the midnight-spanning interval
            if (light_timer_on <= current_hour) and (current_hour < light_timer_off):
                GPIO.output(Lights, GPIO.HIGH)  # turn lights on
            else:
                GPIO.output(Lights, GPIO.LOW)  # turn lights off
        else:
            GPIO.output(Lights, GPIO.LOW)  # if light_state is False, turn off the lights
        time.sleep(1)

@app.route('/current_values')
@auth.login_required
def current_values():
    return jsonify({'ec': ec, 'pH': pH, 'temp': temp})

# Reads the incoming serial data from the Arduino and updates the variables 
def read_serial():
    global temp, pH, ec    
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            temp, pH, ec = map(float, line.split('X'))
            #print(temp)
            #print(pH)
            #print(ec)
            #print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx')

@app.before_request
def initialize_serial():
    if not hasattr(threading.current_thread(), '_started'):
        threading.current_thread()._started = True
        read_serial_thread = threading.Thread(target=read_serial)
        read_serial_thread.start()


if __name__ == '__main__':
    read_serial_thread = threading.Thread(target=read_serial)
    read_serial_thread.start()
    add_buffer_thread = threading.Thread(target=add_buffer)
    add_buffer_thread.start()
    light_timer_control_thread = threading.Thread(target=light_timer_control)
    light_timer_control_thread.start()
    device_control_thread = threading.Thread(target=device_control)
    device_control_thread.start()
#    read_serial_thread = threading.Thread(target=read_serial)
#    read_serial_thread.start()
    init_serial_thread = threading.Thread(target=initialize_serial)
    init_serial_thread.start()
    app.run(host='0.0.0.0', port='5000', threaded=True)


