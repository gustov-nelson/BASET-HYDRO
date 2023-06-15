#Import the necessary modules 
from flask import Flask, render_template, request, Response, jsonify
import threading
import time
import serial
import cv2
import RPi.GPIO as GPIO
from extras import grap_prices
#from Flask-HTTPAuth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
import datetime
import bom
#Setcamera index and the number of retires, it is explained below
camera_index = 0
max_retries = 5

#Set device ouput pins 
Fan = 14
VDC = 15
Pump = 18
Water_Heater = 23
Lights = 24
Heater = 25

Acid = 8
Base = 7
Nutrients = 1


# Initialize GPIO pins
GPIO.setwarnings(False) #Ignores a common warning
GPIO.setmode(GPIO.BCM)  #Sets the layout of pins to be BCM instead of Board. 
GPIO.setup(VDC, GPIO.OUT, initial=GPIO.LOW)  # VDC
GPIO.setup(Lights, GPIO.OUT, initial=GPIO.HIGH)  # Lights
GPIO.setup(Pump, GPIO.OUT, initial=GPIO.HIGH)  # Pump
GPIO.setup(Water_Heater, GPIO.OUT, initial=GPIO.LOW)  # Water Heater
GPIO.setup(Heater, GPIO.OUT, initial=GPIO.HIGH)  # Heater
GPIO.setup(Acid, GPIO.OUT, initial=GPIO.LOW)  # Acid
GPIO.setup(Base, GPIO.OUT, initial=GPIO.LOW)  # Base
GPIO.setup(Nutrients, GPIO.OUT, initial=GPIO.LOW)  # Nutrients
GPIO.setup(Fan, GPIO.OUT, initial=GPIO.LOW)  # Fan


# Initialize Serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1) #'/dev/ttyACM0' is usally the name of an Arduino Uno in the port
ser.flush()

# Global variables are established right now so there are no errors of being called before assignment
temp = float(0.0)
pH = float(0.0)
ec = float(0.0)
pH_high = float(7.0)
pH_low = float(6.0)
ec_high = float(1.8)
ec_low = float(1.5)
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
products = []
#establish names for Flask Server
app = Flask(__name__)
auth = HTTPBasicAuth()
#Create the username and password needed to access the Flask Server
users = {
    "admin": "password",
}

#Path that brings up request for authentication
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username



#Creates the img that is used in video_feed() function
def generate_frames():
    for i in range(max_retries): #This code is just in case the camera index isn't 0. Without this even a momentary change causes the feed to stop
        camera = cv2.VideoCapture(camera_index)
        if not camera.isOpened():
            print(f"Failed to open camera on try {i+1} of {max_retries}")
            time.sleep(1)  # Wait a bit before retrying
        else:
            break
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame) #sets file to .jpg and saves frame data into buffer 
            frame = buffer.tobytes() #converts the array of bytes into a byte string, which is used by html 
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') # yields the image with added code to make it work in html

#This is the main path for the server 
@app.route('/', methods=['GET','POST'])
@auth.login_required
def combine():  #values must be stated as global so that they are updated when changed elsewhere in the program
    global pH_high, pH_low, ec_high, ec_low, water_temp_high, water_temp_low, light_timer_on, light_timer_off, ec, pH, temp, light_state, pump_state, water_heater_state, VDC_state, fan_state, heater_state
    if request.method == 'POST':  #This executes when a POST request is sent, POST means data is coming into the python code
        form_name = request.form.get('form_name')

        if form_name == 'settings':      #This executes if the post was made by the settings' submit button   
            pH_high = float(request.form['pH_high'])
            pH_low = float(request.form['pH_low'])
            ec_high = float(request.form['ec_high'])
            ec_low = float(request.form['ec_low'])                #All the variables are updated
            water_temp_high = float(request.form['water_temp_high'])
            water_temp_low = float(request.form['water_temp_low'])
            light_timer_on = int(request.form['light_timer_on'])
            light_timer_off = int(request.form['light_timer_off'])

        elif form_name == 'device_control': #This executes if the post was made by the device_control's submit button 
            light_state = request.form.get('light_state') == 'on'
            pump_state = request.form.get('pump_state') == 'on'
            water_heater_state = request.form.get('water_heater_state') == 'on'     #All the variables are updated
            VDC_state = request.form.get('VDC_state') == 'on'
            fan_state = request.form.get('fan_state') == 'on'
            heater_state = request.form.get('heater_state') == 'on'   #The return below gives the html document all the updated values
    return render_template('index.html',pH_high=pH_high, pH_low=pH_low, ec_high=ec_high, ec_low=ec_low, water_temp_high=water_temp_high, water_temp_low=water_temp_low, light_timer_on=light_timer_on, light_timer_off=light_timer_off,temp=temp,pH=pH,ec=ec, light_state=light_state,pump_state=pump_state,water_heater_state=water_heater_state,VDC_state=VDC_state,fan_state=fan_state,heater_state=heater_state)

# Displays the BOM and estimated cost:

def product_list():
    global products
    products = grap_prices()
    now = datetime.datetime.now()
    print("BOM ready")
    while True:
        if now.hour == 0 and now.minute ==0:  
            products = grap_prices() #uses the grap_prices() function in extras.py to create the list of products with current prices
    
@app.route('/products')
@auth.login_required
def bom_page():
    global products
    return render_template('bom.html', products=products)

@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Turns the devices on and off based on the states set by the html webpage.
# Everything will always be on if checked except for the lights, which are also controlled by a timer.
def device_control():
    global temp, ec, pH, light_state, pump_state, Water_Heater, VDC_state, fan_state #setting these variables at global allows them to update when other functions change them
    while True:
        #GPIO.output(Lights, GPIO.HIGH if light_state else GPIO.LOW)
        GPIO.output(Pump, GPIO.HIGH if pump_state else GPIO.LOW)
        GPIO.output(Water_Heater, GPIO.HIGH if water_heater_state else GPIO.LOW)
        GPIO.output(VDC, GPIO.HIGH if VDC_state else GPIO.LOW)
        GPIO.output(Fan, GPIO.HIGH if fan_state else GPIO.LOW)
        GPIO.output(Heater, GPIO.HIGH if heater_state else GPIO.LOW)
        #print(temp)    These print functions are for debugging 
        #print(ec)
        #print(pH)
        #time.sleep(5)

# Reads the incoming serial data from the Arduino and updates the variables 
def read_serial():
#    global temp, pH, ec
    while True:
        if ser.in_waiting > 0:   #Activates everytime there is a new serial output from the Arduino
            line = ser.readline().decode('utf-8').rstrip() #The data is sent in the format tempXpHXecX to simplify serial communication   
            temp, pH, ec = map(float, line.split('X'))     #This line splits the single string into three floating values. 
                                                        

# Adds acid, base or nutrients as needed
def add_buffer():
    global ec, pH, ec_high, ec_low, pH_high, pH_low  #Makes sure the sensor values and settings are updated with sensor data and user input
    ec_target = ((ec_high + ec_low) / 2)
    while True:
        ec_target = ec_low #Nutrients is given when EC is below mid-point of the recommended range so it never gets too low
#        print("ec: " + ec)
#        print("pH: " + pH)
#        print("ec high: " + ec_high)
#        print("ec low: " + ec_low)      #These print commands are for debugging
#        print("ph high: " + pH_high)
#        print("ph low: " + pH_low)
        if ec < ec_target:
            GPIO.output(Nutrients, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(Nutrients, GPIO.LOW)
        if pH <= (pH_low + 0.1):
            GPIO.output(Base, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(Base, GPIO.LOW)
        if pH >= (pH_high - 0.1):
            GPIO.output(Acid, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(Acid, GPIO.LOW)
        time.sleep(1) #the sleep function takes arguments of seconds, 600 means this function will execute every 10 minutes

'''def light_timer_control():     #Turns lights on and off based on timer
    global light_timer_on, light_timer_off, light_state # Makes sure the timer changes based on user input
    while True:
        if light_state: # Program will skip this code if user wants lights to stay off using device_control()
            current_hour = int(datetime.datetime.now().hour) #Graps the current hour,between 0(midnight) and 23 (11pm)
            if (light_timer_on <= current_hour) and (current_hour < light_timer_off): #Compares the current time with the hours of operation
                GPIO.output(Lights, GPIO.HIGH)
            else:
                GPIO.output(Lights, GPIO.LOW)
        else:
            GPIO.output(Lights, GPIO.LOW)  #If program skips the rest of the code becasue light_state is False: this turns the lights off
        time.sleep(1)'''
def light_timer_control():     #Turns lights on and off based on timer
    global light_timer_on, light_timer_off, light_state # Makes sure the timer changes based on user input
    while True:
        if light_state: # Program will skip this code if user wants lights to stay off using device_control()
            current_hour = int(datetime.datetime.now().hour) #Graps the current hour,between 0(midnight) and 23 (11pm)
            if light_timer_on < light_timer_off: #Executed if the time of operation does NOT span midnight
                if (light_timer_on <= current_hour) and (current_hour < light_timer_off): #Compares the current time with the hours of operation
                    GPIO.output(Lights, GPIO.HIGH)
                else:
                    GPIO.output(Lights, GPIO.LOW)
            else: #Executed if the time of operation spans midnight
                if (current_hour >= light_timer_on) or (current_hour < light_timer_off): #Checks if hour is after start of first day or before end of second day 
                    GPIO.output(Lights, GPIO.HIGH)
                else:
                    GPIO.output(Lights, GPIO.LOW)
        else:
            GPIO.output(Lights, GPIO.LOW)  #If program skips the rest of the code becasue light_state is False: this turns the lights off
        time.sleep(1)

#This is the path that the html files calls on when updating the sensor data
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

@app.before_request      #Begins read_serial() function before others. Was added because of issue establishing serial communication
def initialize_serial():
    if not hasattr(threading.current_thread(), '_started'):
        threading.current_thread()._started = True
        read_serial_thread = threading.Thread(target=read_serial)
        read_serial_thread.start()

#This is where all the functions are threaded together and activated so they can run simultaneously 
read_serial_thread = threading.Thread(target=read_serial)
read_serial_thread.start()
product_list_thread = threading.Thread(target=product_list)
product_list_thread.start()
add_buffer_thread = threading.Thread(target=add_buffer)
add_buffer_thread.start()
light_timer_control_thread = threading.Thread(target=light_timer_control) 
light_timer_control_thread.start()
device_control_thread = threading.Thread(target=device_control)
device_control_thread.start()
init_serial_thread = threading.Thread(target=initialize_serial)
init_serial_thread.start()  
app.run(host='0.0.0.0', port='5000', threaded=True) #Activates Flask server, host is set so other devices can use
