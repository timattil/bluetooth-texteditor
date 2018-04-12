from bluetooth import *
import threading
import json
from utils import format_message
import queue

class Harald():
    def __init__(self, send_queue, recv_queue):
        self.password = None
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.socket_recv_queue = queue.Queue()
        self.socket_send_queue = queue.Queue()
        self.client_socks = []
        self.host_sock = None # If sock here, then we in Client mode!
        self.start_update_loop()

    def set_password(self, _password):
        self.password = _password
        print('Password: %s' % self.password)

    def start_update_loop(self):
        self.update_loop_thread = threading.Thread(
            target=self.update_loop,
            )
        self.update_loop_thread.setDaemon(True)
        self.update_loop_thread.start()

    def update_loop(self):
        while True:
            self.handle_socket_receive()
            self.handle_socket_send()

    def handle_socket_receive(self):
        try:
            while True:
                rcv_msg = self.socket_recv_queue.get(True, 0.01)
                # HERE CAN BE LOGIC FOR HANDLING RECEIVED MESSGES
                # 1: Ordering of messages
                # 2: Listen thread in case of crash?
                self.recv_queue.put(rcv_msg)
        except queue.Empty:
            pass

    def handle_socket_send(self):
        try:
            while True:
                msg = self.send_queue.get(True, 0.01)
                formatted_msg = json.dumps(msg)
                if self.host_sock:
                    self.host_sock.send(formatted_msg)
                    continue # In theory, this is probably useless
                for client in self.client_socks:
                    client.send(formatted_msg)
        except queue.Empty:
            pass

    def start_host(self):
        self.advertise_thread = threading.Thread(
            target=self.advertise,
            args=[self.client_socks],
            )
        self.advertise_thread.setDaemon(True)
        self.advertise_thread.start()

    def start_client(self):
        self.client_thread = threading.Thread(
            target=self.client_connect
            )
        self.client_thread.setDaemon(True)
        self.client_thread.start()

    def client_connect(self):
        print('Searching all nearby bluetooth devices for the Host')

        uuid = '94f39d29-7d6d-437d-973b-fba39e49d4ee'
        addr = None
        service_matches = find_service( uuid = uuid, address = addr )

        if len(service_matches) == 0:
            print('Couldn\'t find the Host =(')
            sys.exit(0)

        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"]

        print('Connecting to \'%s\' on %s' % (name, host))

        sock = BluetoothSocket( RFCOMM )
        sock.connect((host, port))
        print('Connected')
        self.host_sock = sock
        # Start receiving data from host in this thread!
        self.receive(sock)

    def advertise(self, client_socks):
        server_sock = BluetoothSocket(RFCOMM)
        server_sock.bind(('', PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        uuid = '94f39d29-7d6d-437d-973b-fba39e49d4ee'
        name = 'Host'

        advertise_service(server_sock,
                          name,
                          service_id = uuid,
                          service_classes = [ uuid, SERIAL_PORT_CLASS ],
                          profiles = [ SERIAL_PORT_PROFILE ])

        print('Advertising service on RFCOMM port %d' % port)

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

    def receive(self, sock):
        while True:
            data = sock.recv(1024)
            if data:
                string_data = data.decode('utf-8')
                print("Harald received:", string_data)
                formatted_data = format_message(string_data)
                self.socket_recv_queue.put(formatted_data)
