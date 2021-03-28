#!/usr/bin/python3
# DHT Sensor Data-logging to remote MQTT Broker

import sys
import time
import mqtt_connect

# Adafruit BME280
# pip3 install adafruit-circuitpython-bme280
import board
import digitalio
import busio
import adafruit_bme280

# DHT11, DHT22
# pip3 install Adafruit-DHT
import Adafruit_DHT

# bme680
# pip3 install bme680
import bme680

# nota
# Raspberry:
# sudo i2cdetect -y 1 // show i2c devices
# ls -l /dev/spidev*  // show SPI bus
# pinout              // show pinout  // sudo apt install python3-gpiozero


def print_usage_message():
    print ("\n\n Usage: ")
    print (" python3 mqtt_wm.py  'Topic'        'Sensor_Type'   GPIO-PIN / address      WAIT_SECONDS")
    print (" python3 mqtt_wm.py  'base_topic'   'DHT22'         4                       30")
    print (" python3 mqtt_wm.py  $(hostname)    'DHT11'         17                      60")
    print (" python3 mqtt_wm.py  $(hostname)    'bme280'        0x76                    10")
    

def get_mqtt_connection(base_topic, wait_secs):
    MQTT_last_will    = base_topic + '/LWT: rh-rb-testsystem' #Create the last-will-and-testament topic
    print('MQTT LWT MSG {0}\n'.format(MQTT_last_will))
    
    mqttc = mqtt_connect.set_MQTT_broker(
            MQTT_broker_name = 'rh-rb-openhab',
            MQTT_Port = 1883,
            MQTT_last_will = MQTT_last_will,
            wait_secs= wait_secs)
    return mqttc


def get_sensor_topics(sensor_str):
    sensor_topics = {
        'DHT22':  ['DHT22/Feuchtigkeit', 'DHT22/Temperatur'],
        'BME280': ['bme280/Feuchtigkeit', 'bme280/Temperatur', 'bme280/Luftdruck', 'bme280/Meereshöhe' ]
    }
    return sensor_topics[sensor_str.upper()]

def sensor_values_function(sensor_str):
    if sensor_str   == 'DHT22':
        return Adafruit_DHT.read_retry

    elif sensor_str == 'bme280':
        i2c = busio.I2C(board.SCL, board.SDA)
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
        bme280.sea_level_pressure = 1013.25
        
        def get_bme280_values():
            vals = (bme280.temperature,
                    bme280.relative_humidity,
                    bme280.pressure,
                    bme280.altitude)
            # print (vals)
            return vals
        
        return get_bme280_values   # KEINE KLAMMERN! => Funktion wird zurückgegeben !
        # return adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    else:
        raise  ValueError("\ndef get_sensor_values: Keine Sensorfunktion gefunden \n")
    return


def main():
    if (len(sys.argv) < 2):
        print_usage_message()
        raise  ValueError("\nMissing parameters?\n")
    
    base_topic = sys.argv[1]
    sensor_str = sys.argv[2]
    
    topics     = get_sensor_topics(sensor_str)
    print (topics)
    
    DHT_TYPE   = Adafruit_DHT.DHT22
    DHT_PIN    = sys.argv[3]
    
    
    if (len(sys.argv) > 3):
        poll_intervall = int(sys.argv[4])
    else:
        poll_intervall      = 60

    mqttc = get_mqtt_connection(base_topic, wait_secs = 10)

    lgth = 15
    print ('\n' + '-' * lgth)
    print ('Topics:')
    for topic in topics:
        print (base_topic + '/' + topic)
    print ('Polling intervall: ', poll_intervall, 'sec')
    print ('-' * lgth, '\n')

    get_sensor_values = sensor_values_function(sensor_str)
    
    try:
        while True:
            try:
                print ('Try: read_retry')
                # sensor_values = Adafruit_DHT.read_retry(DHT_TYPE, DHT_PIN)
                sensor_values = get_sensor_values()
                # Publish
                try:
                    # print ('Try: publish')
                    ok = True
                    # print (topics, sensor_values)
                    for val, topic in zip (sensor_values, topics):
                        val   = round(val, 3)
                        topic = base_topic + '/' + topic
                        # publish:
                        (result, mid) = mqttc.publish(topic, val)
                        print (val, '(' + topic + ')')
                        ok = ok or (result != 0)
                    
                    if not ok:
                        raise ValueError('Result for one MQTT-message was not 0')
                
                except Exception as e:
                    print('Error: during publishing to MQTT' + str(e))
                    continue
            
            except Exception as e:
                print('Error: reading sensor data.')

            # print ('Sleep: ', poll_intervall, 'sec')
            time.sleep(poll_intervall)
    
    except Exception as e:
        print('Error connecting to the MQTT server: {0}'.format(e))

if __name__ == '__main__':
    main()

