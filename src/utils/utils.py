import requests
import numpy as np

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
        ret = ret + pad2Hex(input[i].split("0x")[1])
    return ret

def pad2Hex(symbol):
    if len(symbol) == 1:
        return "0" + symbol
    return symbol
#
# def fetch_data(devAddr, startDate, endDate):
#     url = "localhost/user-data/data/" + devAddr
#     params = {"startDate": startDate, "endDate": endDate}
#     r = requests.get(url, params)
#     return r.json()

def jsonToMatrix(data):
 	#transforms the json data to a matrix form
 	data_matrix = np.ndarray(shape=(len(data),5))
 	for i in range(0,len(data)):
 		data_matrix[i,0] = data[i]["SensorsValue"][0]["value"]
 		data_matrix[i,1] = data[i]["SensorsValue"][1]["value"]
 		data_matrix[i,2] = data[i]["SensorsValue"][2]["value"]
 		data_matrix[i,3] = data[i]["SensorsValue"][3]["value"]
 		data_matrix[i,4] = data[i]["tmstmp"]
 	return data_matrix

def makeAverage(data, timeFrame, indexOfSensorID):
	#This function returns a list, whose samples are averaged over an hour interval
	#data should be a 2D matrix with row: [parameter value, timestamp]
    #data_hour is the 
    #timeFrame is the averaging time interval (seconds)
    data_hour = []
    data = data[:, [indexOfSensorID, 4]]
	#initialization
    time_counter = 0             #the time since we start taking the average   
    time_sample = data[len(data)-1,1]      #the timestamp of the sample when time_counter = 0
    summation = data[len(data)-1,0]        #sum of the samples (the values) to be averaged
    number_of_samples = 1        #number of samples to be averaged

    for i in range(len(data)-2, -1, -1):
        time_counter = data[i,1] - time_sample

		#the if loop checks whether the time of samples till the current i, exceeds 3600 seconds.
		# In this case, the samples utill i should be averaged
        if time_counter < timeFrame:
            summation = summation + data[i,0]
            number_of_samples = number_of_samples + 1
        else:
            data_hour.append(summation/number_of_samples)
            time_counter = 0
            time_sample = data[i,1]
            summation = data[i,0]
            number_of_samples = 1
    return data_hour
