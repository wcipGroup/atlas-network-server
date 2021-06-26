import logging
from socketserver import TCPServer
from collections import defaultdict

from umodbus import conf
from umodbus.server.tcp import RequestHandler, get_server
from umodbus.utils import log_to_stream

# Add stream handler to logger 'uModbus'.
log_to_stream(level=logging.DEBUG)

# A very simple data store which maps address against their values.
data_store = defaultdict(int)

# Enable values to be signed (default is False).
conf.SIGNED_VALUES = True

TCPServer.allow_reuse_address = True
app = get_server(TCPServer, ('0.0.0.0', 2459), RequestHandler)


@app.route(slave_ids=[1], function_codes=[3, 4], addresses=list(range(0, 21)))
def read_data_store(slave_id, function_code, address):
    return data_store[address]


@app.route(slave_ids=[1], function_codes=[16], addresses=list(range(0, 21)))
def write_data_store(slave_id, function_code, address, value):
    data_store[address] = value


def initState():
    data_store[1] = 1
    data_store[4] = 1

if __name__ == '__main__':
    try:
        initState()
        app.serve_forever()
    finally:
        app.shutdown()
        app.server_close()