import configparser
import paho.mqtt.client as mqtt
from amqp.publisher import Publisher
import json
from utils.utils import xor, toHexArrayInt, toHexArrayStr
import threading
import time

config = None
key = None
mqttc = None
publisher = None


def on_connect(client, userdata, flags, rc):
    client.subscribe("atlas/+/up")


def on_message(client, userdata, msg):
    try:
        frame = json.loads(msg.payload.decode('utf-8'))
        decryption_flag, decryptionStr = checkAuth(frame["DATA"])
        if decryption_flag:
            frame["DATA"] = decryptionStr.upper()
            frame["GW_ID"] = msg.topic.split("/")[1]
            publisher.publish(json.dumps(frame))
        else:
            print("Does not belongs to the network")
    except Exception as ex:
        print(ex)
        return



def checkAuth(message):
    try:
        encryptedMsg = bytearray.fromhex(message)
        decryptedMsg = xor(encryptedMsg, len(encryptedMsg), key, len(key))
        decryptedStr = toHexArrayStr(toHexArrayInt(decryptedMsg))
        decryptedArray = bytearray.fromhex(decryptedStr)
        return (decryptedArray[0] == 43 & decryptedArray[1] == 43), decryptedStr
    except Exception as e:
        print(e)
        return False, ''
    # Returns True only if the first 2 bytes are 0x2B. That means that everything is OK and the message was encrypted
    # with the proper network key

def mqttc_keep_alive(mqttc):
    while 1:
        mqttc.publish('atlas/keep_alive', "heartbeat")
        time.sleep(30)

def initClients():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config['mqtt_ip'], 1883, 60)
    return client


if __name__ == "__main__":
    try:
        config = configparser.ConfigParser()
        config.read('../config.ini')
        config_amqp = config['AMQP']
        config = config.defaults()
        publisher = Publisher(config_amqp)
        key = bytearray.fromhex(config["nw_key"])
        mqttc = initClients()
        threading.Thread(target=mqttc_keep_alive, args=(mqttc,)).start()
        print("[check_auth]: Start of the program")
    except Exception as e:
        print(e)
        raise exit(1)
    print("[check_auth]: End of INIT")
    try:
        mqttc.loop_forever()
    except KeyboardInterrupt:
        mqttc.disconnect()
        publisher.stop()
        print("[check_auth]: Exit")
