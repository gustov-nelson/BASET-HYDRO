  #include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>

//Plant targets
const float pHhigh = 7.0;
const float pHlow = 6.0;
const float EChigh = 2.3;
const float EClow = 1.8;  
float ECaverage = (EChigh+EClow)/2;

//Pump Code
const int base = 9;
const int acid = 10;
const int nuts = 11;

//EC code 
int R1= 1000;
int Ra=25; //Resistance of powering Pins
int ECPin= A4;
int ECGround=A3;
int ECPower =A5;
float PPMconversion=0.7;
float TemperatureCoef = 0.019; //this changes depending on what chemical we are measuring
float K=3.2;
float EC=0;
float EC25 =0;
int ppm =0;
float raw= 0;
float Vin= 5;
float Vdrop= 0;
float Rc= 0;
float buffer=0;

//pH code
const int pHsensorPin = A0;
const int temp_sensor_pin = 13;
OneWire oneWire(temp_sensor_pin);         // setup a oneWire instance
DallasTemperature tempSensor(&oneWire); // pass oneWire to DallasTemperature library
float calibration_value = 26.84;
int phval = 0; 
unsigned long int avgval; 
int buffer_arr[10],temp;

void setup() 
{
  Serial.begin(9600);
  tempSensor.begin();    // initialize the sensor
  delay(2000);
  pinMode(ECPin,INPUT);
  pinMode(ECPower,OUTPUT);//Setting pin for sourcing current
  pinMode(ECGround,OUTPUT);//setting pin for sinking current
  digitalWrite(ECGround,LOW);//We can leave the ground connected permanantly
  delay(100);// gives sensor time to settle
  delay(100);
  //** Adding Digital Pin Resistance to [25 ohm] to the static Resistor *********//
  // Consule Read-Me for Why, or just accept it as true
  R1=(R1+Ra);// Taking into acount Powering Pin Resitance
  analogWrite(base,0);
  analogWrite(acid,0);
  analogWrite(nuts,0);
};

void loop()
  {
   tempSensor.requestTemperatures(); 
   float Temperature = tempSensor.getTempCByIndex(0);
   Serial.print("Temperature: ");
   Serial.println(Temperature);    // print the temperature in Celsius
   delay(100);
   FindpH();
   GetEC();
   delay(1000);
   //delay(120000);
  }

void GetEC(){
  tempSensor.requestTemperatures(); 
  float Temperature = tempSensor.getTempCByIndex(0);
  digitalWrite(ECPower,HIGH);
  raw= analogRead(ECPin);
  raw= analogRead(ECPin);// This is not a mistake, First reading will be low beause if charged a capacitor
  digitalWrite(ECPower,LOW);
  Vdrop= (Vin*raw)/1024.0;
  Rc=(Vdrop*R1)/(Vin-Vdrop);
  Rc=Rc-Ra; //acounting for Digital Pin Resitance
  EC = 1000/(Rc*K);
  EC25  =  EC/ (1+ TemperatureCoef*(Temperature-25.0));
  ppm=(EC25)*(PPMconversion*1000*1000);
  Serial.print(EC25);
  Serial.println(" microSimens  ");
  if (EC25 < ECaverage){
    addnuts();
  }
  if (EC25 < EClow){
    Serial.println("Nutrients is too low!!!");
  }else if (EC25 > EChigh){
    Serial.println("Nutrients is too high!!!");
  }

}


void FindpH(){
  for(int i=0;i<10;i++) 
 { 
 buffer_arr[i]=analogRead(pHsensorPin);
 delay(30);
 }
 for(int i=0;i<9;i++)
 {
 for(int j=i+1;j<10;j++)
 {
 if(buffer_arr[i]>buffer_arr[j])
 {
 temp=buffer_arr[i];
 buffer_arr[i]=buffer_arr[j];
 buffer_arr[j]=temp;
 }
 }
 }
 avgval=0;
 for(int i=2;i<8;i++)
 avgval+=buffer_arr[i];
 float volt=(float)avgval*5.0/1024/6;
 float ph_act = -5.70 * volt + calibration_value;
 Serial.print("pH Val:");
 Serial.println(ph_act);
 if (ph_act > pHhigh + .25){
  Serial.println("pH is too high");
  pHdown();
 }else if (ph_act < pHlow - .25){
  Serial.println("pH is too low");
  pHup();
 } else{
  Serial.println("pH is good...for now");
 }
}

void pHup(){
  digitalWrite(base,1);
  delay(1000);
  digitalWrite(base,0);}
void pHdown(){
  digitalWrite(acid,1);
  delay(1000);
  digitalWrite(acid,0);}
void addnuts(){
  digitalWrite(nuts,1);
  delay(1000);
  digitalWrite(nuts,0);
}
