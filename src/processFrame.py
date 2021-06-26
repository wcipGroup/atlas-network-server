from amqp.consumer import Consumer
import configparser
import json
from persist.mongodb import MongoDB
import paho.mqtt.client as mqtt
from datetime import datetime
from utils.utils import xor, toHexArrayStr, toHexArrayInt, pad2Hex
import threading
import time
import struct

consumer = None
db = None
mqttc = None
key = None


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    payload = prepare_payload(json.loads(body))



def prepare_payload(frame):
    data = frame['DATA']
    payload = {'crc': data[0:4],
               'msgType': data[4:6],
               'snrUl': frame['SNR'],
               'rssiUl': frame['RSSI'],
               'tmstmp': frame['TMSTMP']}
    if payload['msgType'] == '01':
        payload['msgTypeH'] = "joinRequest"
        join_request(payload, data)
    elif payload['msgType'] == '02':
        payload['msgTypeH'] = "joinAccept"
        join_accept(payload, data)
    elif payload['msgType'] == '03':
        payload['msgTypeH'] = "confirmedData"
        confirmed_data(payload, data)
    elif payload['msgType'] == '04':
        payload['msgTypeH'] = "unconfirmedData"
        unconfirmed_data(payload, data)
    elif data[5] == '5':
        payload['msgTypeH'] = "macCommand"
        mac_command(payload, data)
    else:
        print('Unknown message type')
        return
    return payload


def join_request(payload, data):
    print("Join Request: ", data)
    payload['devAddr'] = str(int(data[6:8], 16))
    payload['len'] = str(int(data[18:20], 16))
    device = db.find('devices', {'devAddr': payload['devAddr']})
    # device: {'devAddr': '', 'devName': '', 'ownerId': '', 'appId': '', 'dateCreated': '', 'lastSeen': ''}
    if len(device) == 0:
        print('unknown device')
        return
    device = device[0]
    application = db.find('applications', {'appId': device['appId']})
    # application: {'appId': '', appName: '', 'ownerId': '', 'appKey': '', 'hasAppKey': Boolean, 'dateCreated': Date, 'devices': []}
    if len(application) == 0:
        print('application of the device does not exist')
        return
    application = application[0]
    if payload['devAddr'] not in application['devices']:
        print('the devices does not belong to the application')
        return
    try:
        last_seen_date = datetime.now()
        update_last_seen(payload["devAddr"], last_seen_date)
        payload["date"] = last_seen_date
        db.insert('device_raw_data', payload)
        # query = {"devAddr": payload["devAddr"]}
        # update = {"$push": {"frames": payload}}
        # db.update('device_raw_data', query, update)
    except Exception:
        raise Exception

    appKeyC = "01" if application['appKey'] else "00"
    send_join_accept(device['devAddr'], appKeyC, application['appKey'])


def update_last_seen(devAddr, date):
    query = {"devAddr": devAddr}
    update = {"$set": {"lastSeen": date}}
    db.update('devices', query, update)

def send_join_accept(devAddr, appKeyC, appKey):
    msg = "2B2B02"
    tmstmp = "00000000"
    msg = msg + pad2Hex(devAddr) + appKeyC + appKey + tmstmp + "0C"
    decryptedMsg = bytearray.fromhex(msg)
    encryptedMsg = xor(decryptedMsg, len(decryptedMsg), key, len(key))
    encryptedMsg = toHexArrayStr(toHexArrayInt(encryptedMsg))
    dl = encryptedMsg + "/" + devAddr + "&"

    mqttc.publish('atlas/down', dl)
    print("publiced: ", msg)


def join_accept(payload, data):
    print("Join Accept: ", data)


def confirmed_data(payload, data):
    print("Confirmed Data: ", data)


def unconfirmed_data(payload, data):
    print("Unconfirmed Data: ", data)
    payload['devAddr'] = str(int(data[6:8], 16))
    payload['len'] = str(int(data[62:64], 16))
    payload['numSensors'] = int(data[8:10], 16)
    payload['SensorsValue'] = []
    for i in range(payload['numSensors']):
        payload['SensorsValue'].append(sensorRead(data, i*10+10))
    last_seen_date = datetime.now()
    update_last_seen(payload["devAddr"], last_seen_date)
    payload["date"] = last_seen_date

    payload["wcfi"] = calculate_wcfi(payload["SensorsValue"])
    db.insert('device_raw_data', payload)
    check_downlink_queue(payload['devAddr'])
    # query = {"devAddr": payload["devAddr"]}
    # update = {"$push": {"frames": payload}}
    # db.update('device_raw_data', query, update)


def check_downlink_queue(devAddr):
    macCommand = db.find('downlink_mac', {'devAddr': devAddr})
    if len(macCommand):
        macInterval = macCommand[0]['interval']
        if macInterval['status'] == "pending":
            send_mac_command(devAddr, 1, macInterval['value'])


def send_mac_command(devAddr, commandId, value):
    msg = "2B2B" + commandId + "5"
    tmstmp = "00000000"
    NU = "00"
    msg = msg + pad2Hex(devAddr) + value + tmstmp + NU + "0E"
    decryptedMsg = bytearray.fromhex(msg)
    encryptedMsg = xor(decryptedMsg, len(decryptedMsg), key, len(key))
    encryptedMsg = toHexArrayStr(toHexArrayInt(encryptedMsg))
    dl = encryptedMsg + "/" + devAddr + "&"

    mqttc.publish('atlas/down', dl)
    print("publiced: ", msg)


def calculate_wcfi(sensorsValue):
    # todo: complete this
    return 2


def sensorRead(data, idx):
    sensorData = {}
    sensorData['sensorId'] = int(data[idx:idx+2], 16)
    if sensorData['sensorId'] == 1:
        sensorData['sensorType'] = "Temperature"
    elif sensorData['sensorId'] == 2:
        sensorData['sensorType'] = "PH"
    elif sensorData['sensorId'] == 3:
        sensorData['sensorType'] = "Dissolved Oxygen"
    elif sensorData['sensorId'] == 4:
        sensorData['sensorType'] = "Conductivity"
    sensorData['value'] = struct.unpack('f', bytearray.fromhex(data[idx+2:idx+10]))[0]
    return sensorData

def mac_command(payload, data):
    print("Mac Command: ", data)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("atlas/down")
    client.subscribe("atlas/keep_alive")


def initClients(config_default, config_amqp, config_mongoDB):
    mqttc_init = mqtt.Client()
    mqttc_init.on_connect = on_connect
    mqttc_init.connect(config_default['mqtt_ip'], 1883, 60)
    consumer_init = Consumer(config_amqp)
    db_init = MongoDB(config_mongoDB)
    return mqttc_init, consumer_init, db_init


def mqttc_keep_alive(mqttc):
    while 1:
        mqttc.publish('atlas/keep_alive', "heartbeat")
        time.sleep(30)


if __name__ == "__main__":
    try:
        print(__name__)
        print("[processFrame]: start")
        config = configparser.ConfigParser()
        config.read('../config.ini')
        config_amqp = config['AMQP']
        config_mongoDB = config['MONGODB']
        config_default = config.defaults()
        key = bytearray.fromhex(config_default["nw_key"])
        mqttc, consumer, db = initClients(config_default, config_amqp, config_mongoDB)

    except Exception as e:
        print(e)
        raise e
    try:
        x = threading.Thread(target=mqttc_keep_alive, args=(mqttc,)).start()
        consumer.consume(callback)
    except KeyboardInterrupt:
        consumer.stop()
        print("[processFrame]: EXIT")
