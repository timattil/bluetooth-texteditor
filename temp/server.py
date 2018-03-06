from bluetooth import *
import threading as th
import json
from utils import format_message

def server(send_queue, recv_queue):
    clients = []
    connect_thread = threading.Thread(
            target=connect,
            args=[clients, recv_queue],
        )
    connect_thread.setDaemon(True)
    connect_thread.start()
       
    
def connect(clients, recv_queue):
    size = 1024
    server_sock=BluetoothSocket( RFCOMM )
    server_sock.bind(("",PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]

    uuid = '94f39d29-7d6d-437d-973b-fba39e49d4ee'

    advertise_service( server_sock, 'BLT Host',
                       service_id = uuid,
                       service_classes = [ uuid, SERIAL_PORT_CLASS ],
                       profiles = [ SERIAL_PORT_PROFILE ],
    #                   protocols = [ OBEX_UUID ]
                        )

    print("Waiting for connection on RFCOMM channel %d" % port)

    try:
        client_sock, client_info = server_sock.accept()
        print("Accepted connection from ", client_info)
        clients.append(client_sock)
        client_thread = threading.Thread(
            target=receive,
            args=[client_sock, recv_queue],
        )
        client_thread.setDaemon(True)
        client_thread.start()
        
    except:
        print("Closing socket")
        client_sock.close()
        server_sock.close()

def receive(client_sock, recv_queue):
    while True:
        data = client_sock.recv(size)
        if data:
            print(data)
            received = format_message(data)
            recv_queue.put(received)
        
if __name__ == '__main__':
    clients = []
    send_queue = queue.Queue()
    recv_queue = queue.Queue()
    self.client_thread = threading.Thread(
            target=connect,
            args=[clients],
        )
