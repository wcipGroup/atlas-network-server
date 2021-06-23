import requests
from datetime import datetime, timedelta
from utils.utils import normalize, fetch_data


if __name__=="__main__":
    startDate = datetime.today() - timedelta(hours=24)
    endDate = datetime.today()
    data = fetch_data(1, startDate, endDate)  # data from the last 24 hours
    normalized_values = normalize(data)
    model = tf.load_model("path/to/save/" + "_1_1") # analoga to onoma sto save apo to train
    predicted_values = model.predict(normalized_values, 12)  # next 12 values
    mongoDB.save(predicted_values)