import configparser
import paho.mqtt.client as mqtt
from publisher import Publisher


config = None
key = None
mqttc = None
pub = None

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("atlas/up")


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    decryption_flag, decryptionStr = checkAuth(msg.payload.decode('utf-8'))
    if decryption_flag:
        pub.publish(decryptionStr.upper())
        print("Belongs to the network")
    else:
        print("Does not belongs to the network")


def xor(input, inSize, key, keySize):
    strs = ""
    for i in range(inSize):
        j = i % keySize
        strs = strs + "0x" + str(input[i] ^ key[j])
    return strs


def toHexArrayInt(input):
    hexArray = input.split("0x")[1:]
    for i in range(len(hexArray)):
        hexArray[i] = hex(int(hexArray[i]))
    return hexArray


def toHexArrayStr(input):
    ret = ""
    for i in range(len(input)):
        ret = ret + input[i].split("0x")[1]
    return ret


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
        config.read('config.ini')
        config_amqp = config['AMQP']
        config = config.defaults()
        pub = Publisher(config_amqp)
        key = bytearray.fromhex(config["nw_key"])
        mqttc = initClients()
    except Exception as e:
        print(e)
    print("[check_auth]: End of INIT")
    mqttc.loop_forever()
