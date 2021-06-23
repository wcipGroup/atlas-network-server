import requests
from utils.utils import normalize, fetch_data


def train(data, indexOfSensorId, path, devAddr):
    # indexOfSensorId = 0: temperature, 1:ph, 2:do, 3:conductivity
    #  data = array of snapshots
    #  snapshot = object of measurement with tmstmp and sensorsValue


    # for snapshot in data:
    #     tmstmp = data["tmstmp"]
    #     value = data["sensorValue"][indexOfSensorId]
    # normalized_values = normalize(temperature_values)
    # model = tf.model()
    # model.train(normalized_values)
    # model.save(path+ "/model_devAddr_"+ indexOfSensorId)
    return 0

if __name__=="__main__":
    print("start")
    data = fetch_data(1, False, False)  # 1 for the 1st device, False and False for the Dates.
    # because we want data from all the dates.
    for i in range(4):  #4 sensors
        train(data, i, "path/to/save", 1)
    print("end")

