from bluetooth import *

def connect():
    addr = None

    print("Searching all nearby bluetooth devices for the BLT Host.")

    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    service_matches = find_service( uuid = uuid, address = addr )

    if len(service_matches) == 0:
        print("Couldn't find the BLT Host =(")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    print("Connecting to \"%s\" on %s" % (name, host))

    # Create the client socket
    sock = BluetoothSocket( RFCOMM )
    sock.connect((host, port))
    print("Connected")
    return sock
    
if __name__ == '__main__':
    s = connect()
    while True:
        text = input()
        if text == "quit":
            break
        s.send(bytes(text, 'UTF-8'))
    s.close()