import configparser
import paho.mqtt.client as mqtt
from src.amqp.publisher import Publisher
import json
from src.utils.utils import *

config = None
key = None
mqttc = None
publisher = None


def on_connect(client, userdata, flags, rc):
    client.subscribe("atlas/up")


def on_message(client, userdata, msg):
    frame = json.loads(msg.payload.decode('utf-8'))
    decryption_flag, decryptionStr = checkAuth(frame["DATA"])
    if decryption_flag:
        frame["DATA"] = decryptionStr.upper()
        publisher.publish(json.dumps(frame))
        print(frame)
        print("Belongs to the network")
    else:
        print("Does not belongs to the network")


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


def initClients():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config['mqtt_ip'], 1883, 60)
    return client


if __name__ == "__main__":
    print("[check_auth]: Start of the program")
    try:
        config = configparser.ConfigParser()
        config.read('../config.ini')
        config_amqp = config['AMQP']
        config = config.defaults()
        publisher = Publisher(config_amqp)
        key = bytearray.fromhex(config["nw_key"])
        mqttc = initClients()
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
