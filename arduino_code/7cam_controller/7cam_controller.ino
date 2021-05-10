char serialData;

unsigned long fps;
int maxFrameCount;
unsigned long ExposureTime;
unsigned long currentMicros = 0;
int camState = 0;
int led=13;
int cam=12;
int light=8;
int motor=7;
String input;
int indstart;
int indend;

void setup() { 
  Serial.begin(9600);          //initialize serial at 9600 baudrate
  pinMode(led, OUTPUT);        //declare pin as output 
  pinMode(cam, OUTPUT);        //declare pin as output
  pinMode(light,OUTPUT);
  pinMode(motor, OUTPUT);
  }
  
void loop() {
  digitalWrite(led, LOW);
  digitalWrite(cam, LOW);  

  if(Serial.available()) {
    input = Serial.readString();
    digitalWrite(light, LOW);
    
    if(input.substring(0, 4) == "trig"){
      indstart = input.indexOf("_");
      
      // parse input
      for(int i = 0; i < 3; i++){
        indend = input.indexOf("_",indstart + 1);
        if(i==0){
          fps = input.substring(indstart+1, indend+1).toInt();
        }
        else if(i==1){
          maxFrameCount = input.substring(indstart+1, indend+1).toInt();
        }
        else if(i==2){
          ExposureTime = input.substring(indstart+1).toInt();
        }
        indstart = indend;
      }
      Serial.print(fps);
      Serial.print("_");
      Serial.print(maxFrameCount);
      Serial.print("_");
      Serial.print(ExposureTime);
      Serial.print("_");
      
      // start exposure
      digitalWrite(led, HIGH);

      if(maxFrameCount<10){
        digitalWrite(motor, HIGH);
        delay(500);
        digitalWrite(motor, LOW);
        delay(500);
      }
      
      unsigned long now = millis();
      unsigned long previousMicros = micros();
      int frameCount = 0;
      digitalWrite(cam, HIGH);
      camState = 1;
      
      while (frameCount < maxFrameCount){

        currentMicros=micros();

        if(currentMicros - previousMicros > ExposureTime){
          if(camState==1){
            digitalWrite(cam, LOW);
            camState = 0;
          }
        }
        
        if(currentMicros - previousMicros > fps){
          if(camState==0){
            digitalWrite(cam, HIGH);
            camState = 1;
            frameCount++;
            previousMicros = currentMicros;
          }
        }
                
        //turn ON light after 1s
        if((millis()- now)>1000){
          digitalWrite(light, HIGH);
        }
      }
      //turn OFF light after exposure
      digitalWrite(light, LOW);
    }
  }
}
