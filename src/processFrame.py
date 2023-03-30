from amqp.consumer import Consumer
import configparser
import json
from persist.mongodb import MongoDB
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from utils.utils import xor, toHexArrayStr, toHexArrayInt, pad2Hex, makeAverage, jsonToMatrix
from predict import makePrediction
import numpy as np
import tensorflow as tf
from tensorflow import keras
import threading
import time
import struct
import subprocess
import os

consumer = None
db = None
mqttc = None
key = None


# TODO: exclude duplicated messages


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    payload = prepare_payload(json.loads(body))


def prepare_payload(frame):
    data = frame['DATA']
    payload = {'crc': data[0:4],
               'msgType': data[4:6],
               'gwId': frame['GW_ID'],
               'snrUl': frame['SNR'],
               'rssiUl': frame['RSSI'],
               'tmstmp': frame['TMSTMP']}
    try:
        update_gw_last_seen(frame['GW_ID'], datetime.now())
    except Exception:
        pass
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
    # application: {'appId': '', appName: '', 'ownerId': '', 'appKey': '', 'hasAppKey': Boolean, 'dateCreated': Date,
    # 'devices': []}
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
    send_join_accept(device['devAddr'], appKeyC, application['appKey'], payload['gwId'])


# Add the gw_id to last seen as well.
def update_last_seen(devAddr, date):
    query = {"devAddr": devAddr}
    update = {"$set": {"lastSeen": date}}
    db.update('devices', query, update)


def update_gw_last_seen(gwId, date):
    query = {"gwId": gwId}
    update = {"$set": {"lastSeen": date}}
    db.update('gateways', query, update)


def send_join_accept(devAddr, appKeyC, appKey, gwId):
    msg = "2B2B02"
    tmstmp = "00000000"
    msg = msg + pad2Hex(devAddr) + appKeyC + appKey + tmstmp + "0C"
    decryptedMsg = bytearray.fromhex(msg)
    encryptedMsg = xor(decryptedMsg, len(decryptedMsg), key, len(key))
    encryptedMsg = toHexArrayStr(toHexArrayInt(encryptedMsg))
    dl = encryptedMsg + "/" + devAddr + "&"
    mqttc.publish("atlas/%s/down" % gwId, dl)
    db.update('devices', {'devAddr': devAddr},
              {"$set": {"interval": "5", "txPower": 0}})
    print("published: ", msg)


def join_accept(payload, data):
    print("Join Accept: ", data)


def confirmed_data(payload, data):
    print("Confirmed Data: ", data)

def savePrediction():

    #collection
    #collection = db["device_raw_data"]

    #number of documents to find
    n_docs = 864

    #find the first n_docs documents in descending order of 'tmstmp'
    #data = db.find("device_raw_data", {"msgType": "04"}).sort("tmstmp", -1).limit(n_docs)
    data = db.find_limit_ordered("device_raw_data", {"msgType": "04"}, n_docs)
    #data = list(data)

    #transform json to numpy
    matrix = jsonToMatrix(data)

    path_Tmp = "trainedModels/waterQualityTmpModel.h5"
    indexOfSensorId = 0
    prediction_Tmp = makePrediction(matrix, indexOfSensorId, path_Tmp)
    
    #pH
    path_pH = "trainedModels/waterQualitypHModel.h5"
    prediction_pH = makePrediction(matrix, indexOfSensorId+1, path_pH)

    #col = db["predictions"]

    for i in range(12):
        db.update_one("predictions", {"predNo": i+1, "SensorsValue.sensorId": indexOfSensorId+1},{"$set": {f"SensorsValue.{indexOfSensorId}.value": float(prediction_Tmp[0,i])}})
        #update time by adding i+1 hours to the current one
        delta = timedelta(hours=i+1)
        new_date = datetime.now() + delta
        db.update_one("predictions", {"predNo": i+1},{"$set": {"date": new_date}})
        #pH
        db.update_one("predictions", {"predNo": i+1, "SensorsValue.sensorId": indexOfSensorId+2},{"$set": {f"SensorsValue.{indexOfSensorId+1}.value": float(prediction_pH[0,i])}})
     

def unconfirmed_data(payload, data):
    print("Unconfirmed Data: ", data)
    payload['devAddr'] = str(int(data[6:8], 16))
    payload['len'] = str(int(data[62:64], 16))
    payload['numSensors'] = int(data[8:10], 16)
    payload['SensorsValue'] = []
    for i in range(payload['numSensors']):
        payload['SensorsValue'].append(sensorRead(data, i * 10 + 10))
    last_seen_date = datetime.now()
    update_last_seen(payload["devAddr"], last_seen_date)
    payload["date"] = last_seen_date
    
    payload["wcfi"] = fwqi(payload["SensorsValue"], payload['devAddr'])
    alert(payload["SensorsValue"], payload['devAddr'])
    db.insert('device_raw_data', payload)
    # mac_optimizations(payload['devAddr'])
    check_downlink_queue(payload['devAddr'], payload["gwId"])
    savePrediction()


def alert(data,devAddr):
    # this function sends email notification if a parameter is out of the desired bounds
    # tmp_val = data[0]["value"]
    # send_email("temperature",tmp_val)
    # temperature
    tmp_val = data[0]["value"]
    if tmp_val < 10:
        send_email("temperature",tmp_val)
    elif tmp_val >= 30:
        send_email("temperature",tmp_val)

    # pH
    ph_value = data[1]["value"]
    if ph_value <= 6:
        send_email("pH",ph_value)
    elif ph_value >= 9:
        send_email("pH",ph_value)

    # DO
    #do_value = data[2]["value"]
    #if do_value <= 3:
    #    send_email("disolved oxygen",do_value)

    # cnd
    cnd_value = data[3]["value"]
    if cnd_value >= 1000:
        send_email("conductivity",cnd_value)
    elif cnd_value < 0:
        send_email("conductivity",cnd_value)



def send_email(VARIABLE_NAME,VARIABLE_VALUE):
    f = open("/usr/local/alarms/send_email.php","w+")
    f.write("<?php\r\n")
    f.write("$to_email = 'tyrovolas@auth.gr';\r\n")
    f.write("$subject = 'ATLAS Warning';\r\n")
    f.write("$message = 'Warning! The value of %s is %d.'; \r\n" % (VARIABLE_NAME, VARIABLE_VALUE))
    f.write("$headers = 'From: info@atlas.com';\r\n")
    f.write("mail($to_email,$subject,$message,$headers);\r\n")
    f.write("?>\r\n")
    f.close()
    # db.insert_one('notifications', payload)


def mac_optimizations(devAddr):
    device = db.find('devices', {'devAddr': devAddr})[0]
    preference = device["optimizations"] if "optimizations" in device.keys() else False
    if not preference:
        return
    numOfPackets = 5
    """"List of packets: [pkt1, pkt2, ...]"""
    last_packets = db.find_limit_ordered('device_raw_data', {'devAddr': devAddr, 'msgType': "04"}, numOfPackets)
    if len(last_packets) < numOfPackets:
        return
    """"Packet: {snrUl: int, rssiUl: int, date: date, ...}"""
    update_txPower(devAddr=devAddr, value=0)
    """Value
        0->Low Power
        1->Medium Power
        2->High Power
    """
    update_interval(devAddr=devAddr, value=34)
    """Value in seconds"""
    return


def update_txPower(devAddr, value):
    """Value
    0->Low Power
    1->Medium Power
    2->High Power
     """
    if value not in [0, 1, 2]:
        return
    db.update('downlink_mac', {"devAddr": devAddr},
              {"$set": {"txPower": {"commandType": "txPower", "commandId": 4,
                                              "value": value, "dateCreated": datetime.now(),
                                              "status": "pending"}}})


def update_interval(devAddr, value):
    """Value in seconds"""
    if not isinstance(value, int):
        return
    db.update('downlink_mac', {"devAddr": devAddr},
              {"$set": {"interval": {"commandType": "interval", "commandId": 2,
                                     "value": value, "dateCreated": datetime.now(),
                                     "status": "pending"}}})


def check_downlink_queue(devAddr, gwId):
    macCommand = db.find('downlink_mac', {'devAddr': devAddr})
    if len(macCommand):
        if 'interval' in macCommand[0].keys():
            macInterval = macCommand[0]['interval']
            if macInterval['status'] == "pending":
                if send_mac_command(devAddr, 2, macInterval['value'], gwId):
                    db.update('downlink_mac', {'devAddr': devAddr},
                              {"$set": {"interval": {"commandType": "interval", "commandId": 2,
                                                     "dateUpdated": datetime.now(), "status": "sent"}}})
                    db.update('devices', {'devAddr': devAddr},
                              {"$set": {"interval": macInterval['value']}})
                    return
        if 'txPower' in macCommand[0].keys():
            macTxPower = macCommand[0]['txPower']
            if macTxPower['status'] == "pending":
                if send_mac_command(devAddr, 4, macTxPower['value'], gwId):
                    db.update('downlink_mac', {'devAddr': devAddr},
                              {"$set": {"txPower": {"commandType": "txPower", "commandId": 4,
                                                     "dateUpdated": datetime.now(), "status": "sent"}}})
                    db.update('devices', {'devAddr': devAddr},
                              {"$set": {"txPower": macTxPower['value']}})
                    return


def send_mac_command(devAddr, commandId, value, gwId):
    try:
        msg = "2B2B" + str(commandId) + "5"
        tmstmp = "00000000"
        NU = "00"
        msg = msg + pad2Hex(devAddr) + pad2Hex("%x" % int(value)) + tmstmp + NU + "0E"
        decryptedMsg = bytearray.fromhex(msg)
        encryptedMsg = xor(decryptedMsg, len(decryptedMsg), key, len(key))
        encryptedMsg = toHexArrayStr(toHexArrayInt(encryptedMsg))
        dl = encryptedMsg + "/" + devAddr + "&"
        mqttc.publish('atlas/%s/down' % gwId, dl)
        return True
    except Exception as e:
        return False


def fwqi(data, devAddr, weights=[0.5, 0.333, 0.166]):
    #def fwqi(data, devAddr, weights=[0.5, 0.75, 0.9167, 0.25]):
    # this function calculates the water quality index
    # data should be a single point in time
    # weights are the weighting factors for calculating fwqi

    system_alerts = []
    # at the end of this function, this array will hold all the alerts that the system should handle as feedback
    # either as pushed notification or as system automation
    potentially_alerts = []
    # all the alerts that related with individual indexes of 3

    # temperature
    tmp_val = data[0]["value"]
    if 23 <= tmp_val < 28:
        Tmp = 1
    elif (20 <= tmp_val < 23) or (28 <= tmp_val < 29):
        Tmp = 2
    elif 10 <= tmp_val < 20:
        Tmp = 3
        potentially_alerts.append({"actuator": "hotWater", "actionTime": 20})
    elif 29 <= tmp_val < 30:
        Tmp = 3
        potentially_alerts.append({"actuator": "coldWater", "actionTime": 20})
    elif 5 <= tmp_val < 10:
        Tmp = 4
        system_alerts.append({"actuator": "hotWater", "actionTime": 30})
    elif 30 <= tmp_val < 34:
        Tmp = 4
        system_alerts.append({"actuator": "coldWater", "actionTime": 30})
    elif tmp_val < 5:
        Tmp = 5
        system_alerts.append({"actuator": "hotWater", "actionTime": 40})
    elif tmp_val >= 34:
        Tmp = 5
        system_alerts.append({"actuator": "coldWater", "actionTime": 40})

    # pH
    ph_value = data[1]["value"]
    if 6.6 <= ph_value < 8:
        pH = 1
    elif (6.4 <= ph_value < 6.6) or (8 <= ph_value < 8.6):
        pH = 2
    elif 6 <= ph_value < 6.4:
        pH = 3
        potentially_alerts.append({"actuator": "acid", "actionTime": 20})
    elif 8.6 <= ph_value < 9:
        pH = 3
        potentially_alerts.append({"actuator": "base", "actionTime": 20})
    elif 4.8 <= ph_value < 6:
        pH = 4
        system_alerts.append({"actuator": "acid", "actionTime": 30})
    elif 9 <= ph_value < 9.2:
        pH = 4
        system_alerts.append({"actuator": "base", "actionTime": 30})
    elif ph_value < 4.8:
        pH = 5
        system_alerts.append({"actuator": "acid", "actionTime": 40})
    elif ph_value >= 9.2:
        pH = 5
        system_alerts.append({"actuator": "base", "actionTime": 40})

    # DO
    do_value = data[2]["value"]
    if do_value >= 8:
        DO = 1
    elif 4 <= do_value < 8:
        DO = 2
    elif 3 <= do_value < 4:
        DO = 3
        potentially_alerts.append({"actuator": "oxygen", "actionTime": 20})
    elif 2 <= do_value < 3:
        DO = 4
        system_alerts.append({"actuator": "oxygen", "actionTime": 30})
    else:
        DO = 5
        system_alerts.append({"actuator": "oxygen", "actionTime": 40})

    # cnd
    cnd_value = data[3]["value"]
    if 150 < cnd_value < 500:
        cnd = 1
    elif (100 < cnd_value <= 150) or (500 <= cnd_value < 700):
        cnd = 2
    elif (0 < cnd_value <= 100) or (700 <= cnd_value < 1000):
        cnd = 3
    elif 1000 <= cnd_value < 2000:
        cnd = 4
    else:
        cnd = 5

    # FWQI = round((Tmp ** weights[0]) * (pH ** weights[1]) * (DO ** weights[2]) * (cnd ** weights[3]))
    FWQI = (Tmp * weights[1]) + (pH * weights[0]) + (cnd * weights[2])
    #if FWQI > 5:
    #    FWQI = 5
    # FWQI = 28

    # for fwqi over 2, we may include all the potentially alerts.
    if FWQI > 2:
        for alert in potentially_alerts:
            system_alerts.append(alert)

    if len(system_alerts):
        handle_alerts(system_alerts, devAddr)
    return (FWQI)



def handle_alerts(alerts, devAddr):
    automations_flag = notification_policy(devAddr)
    if automations_flag:
        # TODO: add mbus client
        print("saving for mbus server")
    else:
        # TODO: find a notification method and implement it
        print("notifications only")


def notification_policy(devAddr):
    # this function should check for the notification policy of the proper user in his profile.
    # the flow should be: devAddr -> ownerId -> profile -> return(autoActions)
    return False


def sensorRead(data, idx):
    sensorData = {}
    sensorData['sensorId'] = int(data[idx:idx + 2], 16)
    if sensorData['sensorId'] == 1:
        sensorData['sensorType'] = "Temperature"
    elif sensorData['sensorId'] == 2:
        sensorData['sensorType'] = "PH"
    elif sensorData['sensorId'] == 3:
        sensorData['sensorType'] = "Dissolved Oxygen"
    elif sensorData['sensorId'] == 4:
        sensorData['sensorType'] = "Conductivity"
    sensorData['value'] = struct.unpack('f', bytearray.fromhex(data[idx + 2:idx + 10]))[0]
    return sensorData


def mac_command(payload, data):
    print("Mac Command: ", data)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("atlas/+/down")
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
