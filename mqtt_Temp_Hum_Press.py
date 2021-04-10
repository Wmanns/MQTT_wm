#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Raspberry:
# Pinout:
# sudo apt install -y python3-gpiozero
# pinout                         // show pinout
#
# i2c-tools:
# sudo apt install -y i2c-tools  // install i2c-tools
#
# allow user to use i2c:
# sudo gpasswd -a {USERNAME} i2c // add to group i2c
#                                // {USERNAME} logout - login (to take effect !)
#
# sudo i2cdetect -y 1            // show i2c devices
# ls -l /dev/spidev*             // show SPI bus
#
# MQTT:
# pip3 install paho-mqtt         // install MQTT client
#
# Adafruit:
# pip3 install adafruit-circuitpython-bme280
# pip3 install adafruit-circuitpython-bme680

# nohup python3 ./mqtt_Temp_Hum_Press.py 'system_name'   'bme680' 0x76 5 >/dev/null 2>&1 &
# nohup python3 ./mqtt_Temp_Hum_Press.py 'moode-pcm5122' 'bme280' 0x76 5 >/dev/null 2>&1 &

import sys
import time
import mqtt_connect

# Adafruit
import board
import digitalio
import busio
# Adafruit BME280
# pip3 install adafruit-circuitpython-bme280
import adafruit_bme280
# Adafruit BME680
# pip3 install adafruit-circuitpython-bme680
import adafruit_bme680

# DHT11, DHT22
# pip3 install Adafruit-DHT
# import Adafruit_DHT


def print_usage_message():
	print ("\n\n Usage: ")
	print (" python3 ./mqtt_Temp_Hum_Press.py  'Topic'        'Sensor_Type'   GPIO-PIN / address      WAIT_SECONDS")
	print (" python3 ./mqtt_Temp_Hum_Press.py  $(hostname)    'bme680'        0x76                    60")
	print (" python3 ./mqtt_Temp_Hum_Press.py  $(hostname)    'bme280'        0x76                    10")
	print (" python3 ./mqtt_Temp_Hum_Press.py  test-host 'bme280' 0x76 5" )

def get_mqtt_connection(base_topic, wait_secs):
	MQTT_last_will    = base_topic + '/LWT: rh-rb-testsystem' #Create the last-will-and-testament topic
	print('MQTT LWT MSG {0}\n'.format(MQTT_last_will))
	
	mqttc = mqtt_connect.set_MQTT_broker(
			MQTT_broker_name = 'rh-rb4-redcase',
			MQTT_Port = 1883,
			MQTT_last_will = MQTT_last_will,
			wait_secs= wait_secs)
	print('Connecting ok.\n')
	return mqttc

def get_sensor_topics(sensor_str):
	sensor_topics = {
		'DHT22':  ['DHT22/Feuchtigkeit', 'DHT22/Temperatur'],
		'BME280': ['bme280/Feuchtigkeit', 'bme280/Temperatur', 'bme280/Luftdruck', 'bme280/Meereshöhe' ],
		'BME680': ['bme680/Feuchtigkeit', 'bme680/Temperatur', 'bme680/Luftdruck', 'bme680/Meereshöhe',  'bme680/Gas [Ohm]' ]
	}
	return sensor_topics[sensor_str.upper()]

def print_topics(base_topic, topics, poll_intervall):
	lgth = 15
	print ('\n' + '-' * lgth)
	print ('Topics:')
	for topic in topics:
		print (base_topic + '/' + topic)
	print ('Polling intervall: ', poll_intervall, 'sec')
	print ('-' * lgth, '\n')

def sensor_values_function(sensor_str):
	# print ('sensor_str =', sensor_str)
	if False:
		pass
	
	# elif sensor_str == 'DHT22':
	# 	return Adafruit_DHT.read_retry
	
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
	
	elif sensor_str == 'bme680':
		i2c = busio.I2C(board.SCL, board.SDA)
		# print ('i2c = ', i2c)
		bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False, address=0x76)
		# bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
		bme680.sea_level_pressure = 1013.25
		def get_bme680_values():
			vals = (bme680.temperature,
			        bme680.relative_humidity,
			        bme680.pressure,
			        bme680.altitude,
			        bme680.gas)
			# print (vals)
			return vals
		return get_bme680_values   # KEINE KLAMMERN! => Funktion wird zurückgegeben !
	
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
	poll_intervall = int(sys.argv[4])
	print_topics(base_topic, topics, poll_intervall)
	
	# DHT_TYPE   = Adafruit_DHT.DHT22
	# DHT_PIN    = sys.argv[3]
	
	# Connect to MQTT Broker
	mqttc = get_mqtt_connection(base_topic, wait_secs = 10)
	
	# Get sensor function
	get_sensor_values = sensor_values_function(sensor_str)
	
	
	try:
		while True:
			try:
				# print ('Try: read sensor values')
				sensor_values = get_sensor_values()
				# print ('Try: got  sensor values')
				# Publish
				try:
					# print ('Try: publish')
					# print(time.strftime("%H:%M:%S", time.localtime()))
					ok = True
					for val, topic in zip (sensor_values, topics):
						val   = round(val, 1)
						topic = base_topic + '/' + topic
						# publish -- nb: a result of 0 indicates success
						(result, mid) = mqttc.publish(topic, val)
						# print (result, ok, val, '(' + topic + ')')
						ok = ok and (result == 0)
						if (result != 0):
							print ('Result for MQTT-message != 0: result, val, topic: ', result, ok, val, '(' + topic + ')')
					# print()
					
					if not ok:
						raise ValueError('Result for at least one of various MQTT-messages was not 0.')
					else:
						print ('.', end='')
						sys.stdout.flush()
				
				except Exception as e:
					print('Error during publishing to MQTT: ' + str(e))
					continue
			
			except Exception as e:
				print('\nError: reading sensor data.')
			
			# print ('Sleep: ', poll_intervall, 'sec')
			time.sleep(poll_intervall)
	
	except Exception as e:
		print('Error connecting to the MQTT server: {0}'.format(e))

if __name__ == '__main__':
	main()

