# atlas-network-server
A simple network server following the rules of the ATLAS wireless network protocol

### TODO
* create new thread that reads messages from the uplink queue and determine the message type, prepare the response and finally put the response back into another queue
* create new thread that reads the downlink queue and route the messages to the gateway through the mqtt broker
* build the functions that handle the downlink messages into the network devices
