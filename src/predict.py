import requests
import tensorflow as tf
import numpy as np
from tensorflow import keras
from datetime import datetime, timedelta
from utils.utils import makeAverage, jsonToMatrix

def makePrediction(data_matrix, indexOfSensorId, trained_model_path):
    #This function retuns a 12-hour (12 samples) prediction of the selected parameter (indexOfSensorId)
    #The last 48 available hours (48 samples) are used to make the prediction

    #First, we average the recieved data to an hour-interval (or in general timeFrame - interval)
    TIME_FRAME = 3600
    data_hour = makeAverage(data_matrix, TIME_FRAME, indexOfSensorId)

    x_test = np.ndarray(shape=(48,1))
    #x_test will take the last 48 samples from data_hour. That is, the last 48 hours of measurements
    for i in range(len(data_hour) - 48,len(data_hour)):
	    k = i - len(data_hour) + 48
	    x_test[k] = data_hour[i]


    x_test_temp = x_test  #save the original x_test, it will be used later for de-normalization

    #normalize the input data (x_test) for the naural network
    x_test = (x_test- np.min(x_test))/(np.max(x_test)-np.min(x_test))

    #reshape x_test in the suitable form for the neural network input
    x_test = np.array(x_test)
    x_test = np.reshape(x_test, (1, x_test.shape[0], 1))

    #load the trained model
    model = keras.models.load_model(trained_model_path)

    #make the prediction
    prediction = model.predict(x_test)

    #de-normalization. This is necessary, since the normalized data lie into the range [0,1]
    prediction = (np.max(x_test_temp)-np.min(x_test_temp))*prediction + np.min(x_test_temp)
    return prediction

if __name__=="__main__":
    startDate = datetime.today() - timedelta(hours=48)
    endDate = datetime.today()
    data = fetch_data(1, startDate, endDate)  # data from the last 48 hours
    data_matrix = jsonToMatrix(data)
    predicted_values = makePrediction(data_matrix, indexOfSensorId,trained_model_path)
    mongoDB.save(predicted_values)
