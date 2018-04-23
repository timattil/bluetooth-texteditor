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
        self.order_counter = 0
        self.next_order = 0
        self.synchronizing = False
        self.start_update_loop()

    def set_password(self, _password):
        self.password = _password

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
                # IF CLIENT
                if self.host_sock:
                    if self.synchronizing:
                        if rcv_msg['_type'] == 'sync_response':
                            print('Synchronized!')
                            self.next_order = rcv_msg['_order'] + 1
                            self.recv_queue.put(rcv_msg)
                            self.synchronizing = False
                        else:
                            continue
                    else:
                        if rcv_msg['_order'] == self.next_order:
                            self.next_order += 1
                            self.recv_queue.put(rcv_msg)
                        else:
                            print("Order messed up. Synchronizing with Host.")
                            self.synchronizing = True
                            self.send_sync_request()
                # IF HOST
                else:
                    if rcv_msg['_type'] == 'sync_request':
                        self.recv_queue.put(rcv_msg)
                    else:
                        rcv_msg['_order'] = self.order_counter
                        self.order_counter += 1
                        self.recv_queue.put(rcv_msg)
                        formatted_msg = json.dumps(rcv_msg)
                        for client in self.client_socks:
                            try:
                                client.send(formatted_msg)
                            except OSError:
                                print('Lost connection to a Client. Removing Client from list.')
                                client.close()
                                self.client_socks.remove(client)
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
                else:
                    self.socket_recv_queue.put(msg)
        except queue.Empty:
            pass
        except OSError:
            print('Lost connection to Host.')

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
        print('Authenticating')
        if self.ask_access(sock):
            # Start receiving data from host in this thread!
            print('Access granted, connected to Host')
            self.host_sock = sock
            self.receive(sock)
        else:
            print('Host denied access')
            sock.close()

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
            if self.give_access(client_sock):
                print('Accepted connection from ', client_info)
                client_socks.append(client_sock)
                client_thread = threading.Thread(
                    target=self.receive,
                    args=[client_sock],
                )
                client_thread.setDaemon(True)
                client_thread.start()
            else:
                client_sock.close()
                print('Denied connection from ', client_info)

    def receive(self, sock):
        while True:
            try:
                data = sock.recv(1024)
                if data:
                    string_data = data.decode('utf-8')
                    #print("Harald received:", string_data)
                    formatted_data = format_message(string_data)
                    self.socket_recv_queue.put(formatted_data)
            except OSError:
                if self.host_sock:
                    print('Lost connection to Host. Closing this receive thread.')
                else:
                    print('Lost connection to a Client. Closing this receive thread.')
                sock.close()
                return

    def ask_access(self, sock):
        msg = {
            'source': "ask_access",
            'message': self.password,
            '_from': None,
            '_to': None,
            '_type': "authentication",
            '_order': None,
        }

        formatted_msg = json.dumps(msg)
        sock.send(formatted_msg)

        for ticks in range(0, 1000):
            data = sock.recv(1024)
            if data:
                string_data = data.decode('utf-8')
                formatted_data = format_message(string_data)
                if formatted_data.get("_type") == "authentication" and formatted_data.get("message") == "granted":
                    return True
                else:
                    break

        failed_msg = {
            'source': "ask_access",
            'message': "denied",
            '_from': None,
            '_to': None,
            '_type': "authentication",
            '_order': None,
        }
        self.recv_queue.put(failed_msg)
        return False

    def give_access(self, sock):
        msg = {
            'source': "give_access",
            'message': None,
            '_from': None,
            '_to': None,
            '_type': "authentication",
            '_order': None,
        }

        while True:
            data = sock.recv(1024)
            if data:
                string_data = data.decode('utf-8')
                formatted_data = format_message(string_data)
                if formatted_data.get("_type") == "authentication" and formatted_data.get("message") == self.password:
                    msg["message"] = "granted"
                    formatted_msg = json.dumps(msg)
                    sock.send(formatted_msg)
                    return True
                else:
                    return False

    def send_sync_request(self):
        sync_request = {
            'source': 'send_sync_request',
            'message': 'SYNCHRONIZE WITH ME',
            '_from': None,
            '_to': None,
            '_type': 'sync_request',
            '_order': None,
        }

        formatted_sync_request = json.dumps(sync_request)
        self.host_sock.send(formatted_sync_request)
