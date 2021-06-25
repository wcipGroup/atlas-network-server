import requests
from datetime import datetime, timedelta
from utils.utils import makeAverage, fetch_data, jsonToMatrix


if __name__=="__main__":
    startDate = datetime.today() - timedelta(hours=48)
    endDate = datetime.today()
    data = fetch_data(1, startDate, endDate)  # data from the last 48 hours
    data_matrix = jsonToMatrix(data)
    data_hour = makeAverage(data_matrix, indexOfSensorId)
    model = tf.load_model("path/to/save/" + "_1_1") # analoga to onoma sto save apo to train
    predicted_values = model.predict(normalized_values, 12)  # next 12 values
    mongoDB.save(predicted_values)
