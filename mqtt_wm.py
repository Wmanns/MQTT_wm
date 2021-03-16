#!/usr/bin/python3
# DHT Sensor Data-logging to remote MQTT Broker

import sys
import time
import Adafruit_DHT
import paho.mqtt.client as mqtt


#   python3 mqtt_wm.py 'DHT22'    'base_topic'   4     5
#                       Sensor     base topic    Pin   wait seconds

# DHT11, DHT22
# git clone https://github.com/adafruit/Adafruit_Python_DHT.git
# cd Adafruit_Python_DHT
# sudo apt-get install build-essential python-dev python-openssl
# sudo python3 setup.py install
# cd /home/rh/Adafruit_Python_DHT/examples
# sudo python3 ./AdafruitDHT.py 11 4    # ≡ DHT11 Pin 4


def set_sensor_topics(sensor_str):
    sensor_topics = {
        'DHT22': ['DHT22/Feuchtigkeit', 'DHT22/Temperatur']
    }
    return sensor_topics[sensor_str.upper()]

def get_sensor_value():
    pass

def set_MQTT_broker(MQTT_broker_name, MQTT_Port, MQTT_last_will, wait_secs):
    print('Connecting with MQTT: {0}'.format(MQTT_broker_name))
    mqttc = mqtt.Client(MQTT_broker_name)
    mqttc.will_set(MQTT_last_will, payload = 'offline', qos = 0, retain = True)
    mqttc.connect (MQTT_broker_name, MQTT_Port, keepalive = wait_secs + 10)
    mqttc.publish (MQTT_last_will, payload = 'online',  qos = 0, retain = True)
    return mqttc

def main():
    if (len(sys.argv) < 2):
        print ("\n\n Usage: ")
        print (" python3 mqtt_wm.py 'DHT22'    'base_topic'   4     5")
        print (" python3 mqtt_wm.py 'DHT22'    $(hostname)   4     5")
        raise  ValueError("python3 mqtt_wm.py 'DHT22'    'base_topic'   4     5")
    
    sensor_str = sys.argv[1]
    topics =  set_sensor_topics(sensor_str)
    print (topics)
    
    DHT_TYPE   = Adafruit_DHT.DHT22
    DHT_PIN    = sys.argv[3]
    
    wait_secs      = 1
    
    if (len(sys.argv) > 2):
        wait_secs = int(sys.argv[3])
    
    
    base_topic        = str(sys.argv[2])
    MQTT_last_will    = base_topic + '/LWT' #Create the last-will-and-testament topic
    print('MQTT LWT MSG {0}\n'.format(MQTT_last_will))
    
    mqttc = set_MQTT_broker(MQTT_broker_name = 'rh-rb-openhab',
                            MQTT_Port = 1883,
                            MQTT_last_will = MQTT_last_will,
                            wait_secs= wait_secs)
    
    for topic in topics:
        print (base_topic + '/' + topic)
    
    
    try:
        while True:
            # get sensor data
            # humidity, temperature = Adafruit_DHT.read_retry(DHT_TYPE, DHT_PIN)
            
            vals = Adafruit_DHT.read_retry(DHT_TYPE, DHT_PIN)
            
            # Publish
            try:
                ok = True
                for val, topic in zip (vals, topics):
                    val   = round(val, 3)
                    topic = base_topic + '/' + topic
                    # publish:
                    (result, mid) = mqttc.publish(topic, val)
                    print (val, '(' + topic + ')')
                    ok = ok or (result != 0)
                
                if not ok:
                    raise ValueError('Result for one message was not 0')
            
            except Exception as e:
                print('Error: ' + str(e))
                continue
            
            time.sleep(wait_secs)
    
    except Exception as e:
        print('Error connecting to the MQTT server: {0}'.format(e))

if __name__ == '__main__':
    main()

