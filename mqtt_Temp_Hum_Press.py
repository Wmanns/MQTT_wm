#!/usr/bin/python3
# -*- coding: utf-8 -*-

# git clone https://github.com/Wmanns/MQTT_wm.git
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

# nohup python3 ./mqtt_Temp_Hum_Press.py  MQTT-URL  topic  bme280 stdout 5 >/dev/null 2>&1 &

import sys
import os
import time
import mqtt_connect

# Adafruit
import board
import digitalio
import busio

def print_usage_message():
	print ("\n\n Usage: ")
	print (" python3 ./mqtt_Temp_Hum_Press.py  MQTT-URL  Topic        Sensor_Type   log_target   Delay")
	print (" ------- ------------------------  --------  -----        -----------   -------      -----")
	print (" python3 ./mqtt_Temp_Hum_Press.py  MQTT-URL  topic        bme280        stdout       60")
	print (" python3 ./mqtt_Temp_Hum_Press.py  MQTT-URL  $(hostname)  bme680        null          5")


def get_mqtt_connection(mqtt_URL, mqtt_qos, base_topic, wait_secs):
	MQTT_last_will = base_topic + '/LWT: ' +  base_topic # Create the last-will-and-testament topic
	print('mqtt_URL:           > {0} <'.format(mqtt_URL))
	print('mqtt LWT_MSG:       > {0} <'.format(MQTT_last_will))
	
	mqttc = mqtt_connect.set_MQTT_broker(
			MQTT_client_name = base_topic,
			MQTT_broker_name = mqtt_URL,
			MQTT_Port        = 1883,
			MQTT_qos         = mqtt_qos,
			MQTT_last_will   = MQTT_last_will,
			wait_secs        = wait_secs)
	print('Connecting ok.')
	return mqttc

def get_sensor_topics(sensor_str):
	sensor_topics = {
		'DHT11' : ['Feuchtigkeit', 'Temperatur'],
		'DHT22' : ['Feuchtigkeit', 'Temperatur'],
		'BME280': ['Feuchtigkeit', 'Temperatur', 'Luftdruck', 'Meereshöhe' ],
		'BME680': ['Feuchtigkeit', 'Temperatur', 'Luftdruck', 'Meereshöhe',  'Gas [Ohm]' ]
		}
	
	sensor_str = sensor_str.upper()
	for cnt, item in enumerate (sensor_topics[sensor_str]):
		sensor_topics[sensor_str][cnt] = sensor_str + '/' + item
	
	return sensor_topics[sensor_str]

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
	# import Adafruit_DHT
	# DHT_TYPE   = Adafruit_DHT.DHT22
	# DHT_PIN    = sys.argv[3]
	# 	return Adafruit_DHT.read_retry
	# DHT11, DHT22
	# pip3 install Adafruit-DHT
	
	elif sensor_str == 'BME280':
		import adafruit_bme280
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
	
	elif sensor_str == 'BME680':
		import adafruit_bme680
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

def redirect_stdout_to_dev_null(log_target, log_target_par):
	print ('log_target = ', log_target)
	if log_target not in ['stdout', 'null']:
		print_usage_message()
		print ('\n Parameter #{:d} should be "stdout" or "null"! -> exit\n'.format(log_target_par) )
		exit()
	elif (log_target == 'null'):
		f = open(os.devnull, 'w')
		sys.stdout = f
	return

def get_mqtt_error_message(idx):
	errors = {
		'0': 'Connection successful',
		'1': 'Connection refused – incorrect protocol version',
		'2': 'Connection refused – invalid client identifier',
		'3': 'Connection refused – server unavailable',
		'4': 'Connection refused – bad username or password',
		'5': 'Connection refused – not authorised'
		}
	return ('"' + errors[idx] + '"')


def main():
	# print (" python3 ./mqtt_Temp_Hum_Press.py  'Topic'        'Sensor_Type'   GPIO-PIN / address      WAIT_SECONDS")
	par_cnt = 1
	mqtt_URL_par        = par_cnt; par_cnt += 1
	mqtt_base_topic_par = par_cnt; par_cnt += 1
	sensor_str_par      = par_cnt; par_cnt += 1
	log_target_par      = par_cnt; par_cnt += 1
	delay_str_par       = par_cnt;

	if (len(sys.argv) < par_cnt):
		print_usage_message()
		raise  ValueError("\nMissing parameters?\n")
	
	mqtt_URL        = sys.argv[mqtt_URL_par]
	mqtt_base_topic = sys.argv[mqtt_base_topic_par]
	sensor_str      = sys.argv[sensor_str_par].upper()
	log_target      = sys.argv[log_target_par]
	delay_str       = sys.argv[delay_str_par]
	
	delay           = int(delay_str)
	
	# Get sensor topics
	topics          = get_sensor_topics(sensor_str)
	print_topics(mqtt_base_topic, topics, delay)
	# Connect to MQTT Broker
	mqttc = get_mqtt_connection(mqtt_URL, mqtt_qos = 1, base_topic = mqtt_base_topic, wait_secs = 5)
	# Get sensor function
	get_sensor_values = sensor_values_function(sensor_str)
	# Redirect output according to parameter
	redirect_stdout_to_dev_null(log_target, log_target_par)
	
	try:
		cnt_total = 1
		cnt_ok    = 1
		while True:
			try:
				# print ('Try: read sensor values')
				sensor_values = get_sensor_values()
				cnt_total += 1
				
				# print ('Try: got  sensor values')
				# Publish
				try:
					# print ('Try: publish')
					# print(time.strftime("%H:%M:%S", time.localtime()))
					ok = True
					for val, topic in zip (sensor_values, topics):
						val   = round(val, 1)
						topic = mqtt_base_topic + '/' + topic
						# publish -- nb: a result of 0 indicates success
						(result, mid) = mqttc.publish(topic, val)
						# print (result, ok, val, '(' + topic + ')')
						ok = ok and (result == 0)
						if (result != 0):
							# print ('\n Result for MQTT-message != 0: result, val, topic: ', result, ok, val, ' >' + topic + '<')
							print(' Error during publishing to MQTT: ' + str(result) + ' == ' \
							      + get_mqtt_error_message(str(result)) \
							      + '; >' + topic + '<'
							      )
							sys.stdout.flush()
							mqttc = get_mqtt_connection(mqtt_URL, mqtt_qos = 1, base_topic = mqtt_base_topic, wait_secs = 5)
					# print()
					
					if not ok:
						raise ValueError('Result for at least one of various MQTT-messages was not 0.')
					else:
						print ('.', end='')
						sys.stdout.flush()
				
				except Exception as e:
					print('Error during publishing to MQTT: ' + str(e) + ' == ' + get_mqtt_error_message(str(e)))
					mqttc = get_mqtt_connection(mqtt_URL, mqtt_qos = 1, base_topic = mqtt_base_topic, wait_secs = 5)
					# continue
			
				cnt_ok += 1
			except Exception as e:
				print('\n Error reading sensor data after {:d} consecutive measurements. {:d} measurements in total.'.format(cnt_ok - 1, cnt_total), end='')
				if (cnt_ok - 1 == 0):
					print(' Waiting {:d} seconds.'.format(delay * 2))
					time.sleep(delay * 2)
				else:
					print()
				cnt_ok = 1
				
			# print ('Sleep: ', poll_intervall, 'sec')
			time.sleep(delay)
	
	except Exception as e:
		print('Error connecting to the MQTT server: {0}'.format(e))

if __name__ == '__main__':
	main()

