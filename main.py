import time
import ubinascii
from umqtt.simple import MQTTClient
import machine
import random
import onewire
import ds18x20

# Default  MQTT_BROKER to connect to
MQTT_BROKER = "192.168.0.84"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
SUBSCRIBE_TOPIC = b"zigbee2mqtt/pico2/set"
PUBLISH_TOPIC = "zigbee2mqtt/pico2"

# Setup built in PICO LED as Output
led = machine.Pin("LED",machine.Pin.OUT)

led_green = machine.Pin(21,machine.Pin.OUT)
led_red = machine.Pin(10,machine.Pin.OUT)

# Publish MQTT messages after every set timeout
last_publish = time.time()
publish_interval = 10

# czujknik temp

ds_pin = machine.Pin(28)
 
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
 
roms = ds_sensor.scan()
 
#print('Found DS devices: ', roms)

#odczyt napecia z dzielnika na adc2
bat_v = machine.ADC(0)
conversion_factor = 3.3 / (65535)




# Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg):
    print((topic, msg))
    if msg.decode() == "ON":
        led_red.value(1)
    else:
        led_red.value(0)


def reset():
    print("Resetting...")
    time.sleep(10)
    machine.reset()
    
# Generate random temperature readings from ds18b20   
def get_temperature_reading():
    #return random.randint(20, 50)
    for rom in roms:
        ds_sensor.convert_temp()
        time.sleep_ms(750)
        print(rom)
        ds_temp = ds_sensor.read_temp(rom)
        ds_temperature = "{:.2f}".format(ds_temp)
        return ds_temperature 
    
def main():
    print(f"Begin connection with MQTT Broker :: {MQTT_BROKER}")
    mqttClient = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
    mqttClient.set_callback(sub_cb)
    mqttClient.connect()
    mqttClient.subscribe(SUBSCRIBE_TOPIC)
    print(f"Connected to MQTT  Broker :: {MQTT_BROKER}, and waiting for callback function to be called!")
    while True:
            # Non-blocking wait for message
            mqttClient.check_msg()
            global last_publish
            if (time.time() - last_publish) >= publish_interval:            
                now_temp = get_temperature_reading()
                reading_bat = round(1.45 + (bat_v.read_u16() * conversion_factor), 2)
                print(reading_bat, now_temp, publish_interval)
                mqttClient.publish(PUBLISH_TOPIC, b'{"temperature":' + str(now_temp).encode() + b',"battery":' + str(reading_bat).encode() + b',"interval":' + str(publish_interval).encode() + b'}' )
                last_publish = time.time()
            time.sleep(1)


if __name__ == "__main__":
    while True:
        try:
            main()
        except OSError as e:
            print("Error: " + str(e))
            reset()