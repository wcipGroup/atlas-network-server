import requests

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

def fetch_data(devAddr, startDate, endDate):
    url = "localhost/user-data/data/" + devAddr
    params = {"startDate": startDate, "endDate": endDate}
    r = requests.get(url, params)
    return r.json()

def normalize(values):
    # normalize the values to 5 min and after to 1 hour
    return []