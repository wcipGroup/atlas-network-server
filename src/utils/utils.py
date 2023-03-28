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

# def makeAverage(data_matrix, indexOfSensorId):
# 	#This function returns a list, whose samples are averaged over an hour interval (corresponding to indexOfSensorId)
# 	#data_matrix should be a matrix with rows at the form: [temp, pH, DO, cnd, timestamp]
# 	#We assume that data_matrix has already red the json file. Thus, it presents a matrix form
#
# 	#data_hour is the output, the data averaged over an hour which corresponds to the indexOfSensorId
# 	data_hour = []
#
# 	data = np.ndarray(shape=(len(data_matrix),2))      #a 2D matrix with row [Sensorvalue, timestamp]
# 	for i in range (0,len(data_matrix)):
# 		data[i,0] = data_matrix[i,indexOfSensorId]     #the Sensorvalue corresponding to indexOfSensorId
# 		data[i,1] = data_matrix[i,4]                   #the timestamp
#
# 	#initialization
# 	time_counter = 0             #the time since we start taking the average
# 	time_sample = data[0,1]      #the timestamp of the sample when time_counter = 0
# 	summation = data[0,0]        #sum of the samples (the values) to be averaged
# 	number_of_samples = 1        #number of samples to be averaged
#
# 	for i in range(1,len(data)):
# 		time_counter = data[i,1] - time_sample
#
# 		#the if loop checks whether the time of samples till the current i, exceeds 3600 seconds.
# 		# In this case, the samples until i should be averaged
# 		if time_counter < 3600:
# 			summation = summation + data[i,0]
# 			number_of_samples = number_of_samples + 1
# 		else:
# 			data_hour.append(summation/number_of_samples)
# 			#The following if loop refers to the extreme scenario, where two adjacent samples present
# 			#>3600s time difference. In this case we fill the missing data between those two samples
# 			if data[i,0] - data[i-1,0] > 3600:
# 				n = round((data[i,0] - data[i-1,0])/3600)
# 				for j in range(0,n):
# 					data_hour.append(data[i,0])
# 				i = i + 1
# 				a = 1
# 			time_counter = 0
# 			time_sample = data[i,1]
# 			summation = data[i,0]
# 			number_of_samples = 1
# 	return data_hour
