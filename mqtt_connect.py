#!/usr/bin/python3
import paho.mqtt.client as mqtt

def set_MQTT_broker(MQTT_broker_name, MQTT_Port, MQTT_qos, MQTT_last_will, wait_secs):
    print('Connecting with MQTT: {0}'.format(MQTT_broker_name))
    mqttc = mqtt.Client(MQTT_broker_name)
    mqttc.will_set(MQTT_last_will, payload = 'offline', qos = MQTT_qos, retain = True)
    mqttc.connect (MQTT_broker_name, MQTT_Port, keepalive = wait_secs + 10)
    mqttc.publish (MQTT_last_will, payload = 'online',  qos = MQTT_qos, retain = True)
    return mqttc

def main():
    mqttc = set_MQTT_broker(MQTT_broker_name = 'rh-rb-openhab',
                            MQTT_Port = 1883,
                            MQTT_last_will = MQTT_last_will,
                            wait_secs= wait_secs)
    return mqttc

if __name__ == '__main__':
    main()


