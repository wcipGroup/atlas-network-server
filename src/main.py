import threading
from check_auth import maincheckauth
# import processFrame

if __name__ == '__main__':
    print("[atlas-network-server] start")
    try:
        maincheckauth()
        # check_auth()
        # processFrame()
    except Exception as e:
        print(e)
