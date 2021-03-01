#!/usr/bin/python3
# DHT Sensor Data-logging to remote MQTT Broker

import sys
import time
import Adafruit_DHT
import paho.mqtt.client as mqtt


#   python3 rh_mqtt.py 'DHT22'    'base_topic'   4     5
#                       Sensor     base topic    Pin   wait seconds

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
       print ("\n\n Usage: \n")
       print (" python3 rh_mqtt.py 'DHT22'    'base_topic'   4     5")
       print ("                     Sensor     base topic    Pin   wait seconds \n")
       raise  ValueError("python3 rh_mqtt.py 'DHT22'    'base_topic'   4     5")

    sensor_str = sys.argv[1]
    topics =  set_sensor_topics(sensor_str)
    print (topics)

    DHT_TYPE   = Adafruit_DHT.DHT22
    DHT_PIN    = sys.argv[3]
    
    wait_secs      = 1
    
    if (len(sys.argv) > 2):
        wait_secs = int(sys.argv[3])


    # temperature_topic = str(sys.argv[2]) # temperature channel
    # humidity_topic    = str(sys.argv[3]) # humidity    channel

    # print('\nMQTT Temp MSG {0}'.format(temperature_topic))
    # print('MQTT Humidity MSG {0}'.format(humidity_topic))


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
            # humidity     = round(humidity, 3)
            # temperature  = round(temperature, 3)

            vals = Adafruit_DHT.read_retry(DHT_TYPE, DHT_PIN)
            
            # for val, topic in zip (vals, topics):
            #     print (round(val, 3), topic)
                
            # Publish
            try:
                ok = True
                for val, topic in zip (vals, topics):
                    val   = round(val, 3)
                    topic = base_topic + '/' + topic
                    # publish:
                    (result, mid) = mqttc.publish(topic, val)
                    print (val, topic)
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

