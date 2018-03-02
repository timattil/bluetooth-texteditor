# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

from bluetooth import *
import _thread

def listen(sock, data, should_close):
    try:
        while True:
            data = sock.recv(1024)
            if len(data) == 0:
                should_close = True
                break
            print("Received [%s]" % data)
    except IOError:
        pass

def send(sock, should_close):
    while True:
        data = input()
        if len(data) == 0:
            should_close = True
            break
        sock.send(data)

def close():
    print("Disconnected")
    client_sock.close()
    server_sock.close()
    print("All done")

if __name__ == '__main__':
    server_sock=BluetoothSocket( RFCOMM )
    server_sock.bind(("",PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]

    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

    advertise_service( server_sock, "SampleServer",
                       service_id = uuid,
                       service_classes = [ uuid, SERIAL_PORT_CLASS ],
                       profiles = [ SERIAL_PORT_PROFILE ],
    #                   protocols = [ OBEX_UUID ]
                        )

    print("Waiting for connection on RFCOMM channel %d" % port)

    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)

    should_close = False
    client_data = ''
    listen_thread = _thread.start_new_thread(listen, (client_sock, client_data, should_close,))
    talk_thread = _thread.start_new_thread(send, (client_sock, should_close,))
    '''
    try:
        while True:
            data = client_sock.recv(1024)
            if len(data) == 0: break
            print("Received [%s]" % data)
    except IOError:
        pass
    '''
    while True:
        if should_close == True:
            close()
            break
