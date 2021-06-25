import requests
from utils.utils import makeAverage, fetch_data
import pandas as pd
import numpy as np
import json
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import ReLU
import math
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional


def train(data_matrix, indexOfSensorId, path):
	#trains a model for the selected parameter (indexOfSensorId)
        #indexOfSensorId:  0:tmp, 1:pH, 2:DO,  3:cnd
	#take the data matrix and make the hour average for the indexOfSensorId
	data_temp = makeAverage(data_matrix,indexOfSensorId)         #temp stands for temporary and not temperature
	
	#create a 1D array of the parameter and then fill the data (this shape is required. Actually is an array with parameter values only)
	data = np.ndarray(shape=(len(data_temp),1))
	for i in range(0,len(data_temp)):
		data[i] = data_temp[i]
	
	#data normalization 
	data = (data - np.min(data))/(np.max(data)-np.min(data))

	training_set = data

	x_train = []
	y_train = []
	n_future = 12 #future samples prediction
	n_past = 48 #Past known samples

	#create the timeseries 
	for i in range(0, len(training_set) - n_past - n_future + 1):
		x_train.append(training_set[i : i + n_past, 0])
		y_train.append(training_set[i + n_past : i + n_past + n_future, 0])

	#reshape the data for feeding the neural ntwork
	x_train , y_train = np.array(x_train), np.array(y_train)
	x_train = np.reshape(x_train, (x_train.shape[0] , x_train.shape[1], 1))

	#building the LSTM model
	model = keras.Sequential()
	model.add(Bidirectional(LSTM(units=100, return_sequences=True, input_shape = (x_train.shape[1], 1))))
	model.add(Dropout(0.2))
	#model.add(LSTM(units= 100, return_sequences=True))
	#model.add(Dropout(0.2))
	#model.add(LSTM(units= 30, return_sequences=True))
	#model.add(Dropout(0.2))
	model.add(LSTM(units= 100))
	model.add(Dropout(0.2))
	model.add(Dense(units = n_future, activation="relu"))

	#train the model
	model.compile(optimizer="adam", loss="mean_squared_error")
	model.fit(x_train, y_train, epochs=200, batch_size = 32)

	#save the model
	trained_model = model.save(path)
	return trained_model

if __name__=="__main__":
    print("start")
    data = fetch_data(1, False, False)  # 1 for the 1st device, False and False for the Dates.
    # because we want data from all the dates.
    for i in range(4):  #4 sensors
        train(data, i, "path/to/save")
    print("end")

