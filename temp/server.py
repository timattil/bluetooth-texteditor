from bluetooth import *
import threading as th

def connect(clients):
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
        while True:
            data = client_sock.recv(size)
            if data:
                print(data)
                client_sock.send(data)
    except:
        print("Closing socket")
        client_sock.close()
        server_sock.close()

if __name__ == '__main__':
    clients = []
    connect(clients)
    #t_connect = th.Thread(target=connect, args = (clients,))
    #t_listen = th.Thread()
