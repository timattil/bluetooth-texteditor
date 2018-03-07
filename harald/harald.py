from bluetooth import *
import threading

class Host():
    def __init__(self, send_queue, recv_queue):
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.client_socks = []
        self.connect_thread = threading.Thread(
            target=self.connect,
            args=[self.client_socks]
        )
        self.connect_thread.setDaemon(True)
        self.connect_thread.start()
        self.send_thread = threading.Thread(
            target=self.send,
            args=[self.client_socks],
        )
        self.send_thread.setDaemon(True)
        self.send_thread.start()

    def connect(self, client_socks):
        server_sock = BluetoothSocket(RFCOMM)
        server_sock.bind(('', PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        uuid = '94f39d29-7d6d-437d-973b-fba39e49d4ee'
        name = 'BLT Host'

        advertise_service(server_sock,
                          name,
                          service_id = uuid,
                          service_classes = [ uuid, SERIAL_PORT_CLASS ],
                          profiles = [ SERIAL_PORT_PROFILE ])

        print('Advertising service on RFCOMM channel %d' % port)

        while True:
            client_sock, client_info = server_sock.accept()
            print('Accepted connection from ', client_info)
            client_socks.append(client_sock)
            client_thread = threading.Thread(
                target=self.receive,
                args=[client_sock],
            )
            client_thread.setDaemon(True)
            client_thread.start()

    def send(self, client_socks):
        while True:
            data = self.send_queue.get()
            for client_sock in client_socks:
                client_sock.send(data)
            self.send_queue.task_done()

    def receive(self, sock):
        while True:
            print('received data')
            data = sock.recv(1024)
            if data:
                self.recv_queue.put(data)


class Client():
    def __init__(self, send_queue, recv_queue):
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.sock = self.connect()
        self.send_thread = threading.Thread(
            target=self.send
        )
        self.send_thread.setDaemon(True)
        self.send_thread.start()
        self.recv_thread = threading.Thread(
            target=self.receive
        )
        self.recv_thread.setDaemon(True)
        self.recv_thread.start()

    def connect(self):
        print("Searching all nearby bluetooth devices for the BLT Host.")

        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        addr = None
        service_matches = find_service( uuid = uuid, address = addr )

        if len(service_matches) == 0:
            print("Couldn't find the BLT Host =(")
            sys.exit(0)

        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"]

        print("Connecting to \"%s\" on %s" % (name, host))

        sock = BluetoothSocket( RFCOMM )
        sock.connect((host, port))
        print("Connected")
        return sock

    def send(self):
        while True:
            data = self.send_queue.get()
            self.sock.send(data)
            self.send_queue.task_done()

    def receive(self):
        while True:
            data = self.sock.recv(1024)
            if data:
                self.recv_queue.put(data)
