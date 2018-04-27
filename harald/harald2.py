from bluetooth import *
import threading
import json
from utils import format_message
import queue
import datetime
from dateutil import parser

class Harald():
    def __init__(self, send_queue, recv_queue):
        self.group = None
        self.password = None
        self.supportLongMessages = True
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.socket_recv_queue = queue.Queue()
        self.socket_send_queue = queue.Queue()
        self.client_socks = []
        self.host_sock = None # If sock here, then we in Client mode!
        self.order_counter = 0
        self.next_order = 0
        self.synchronizing = True
        self.own_datetime = None
        self.should_stop_hosting = False
        self.start_update_loop()

    def set_group(self, _group):
        self.group = _group

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
        '''
        This does quite a few things.
        '''
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
                        msg_to_send = self.header_formation(formatted_msg)

                        for client in self.client_socks:
                            try:
                                client.send(msg_to_send)
                            except OSError:
                                print('Lost connection to a Client. Removing Client from list.')
                                client.close()
                                self.client_socks.remove(client)
        except queue.Empty:
            pass

    def handle_socket_send(self):
        '''
        Clients send data from TextEditor to Host.
        Host sends data from TextEditor to its own socket_recv_queue, as if it was another message.
        This way Host handles (puts in order) all messages equally, even its own messages.
        '''
        try:
            while True:
                msg = self.send_queue.get(True, 0.01)
                formatted_msg = json.dumps(msg)
                if self.host_sock:
                    self.socket_send_msg(formatted_msg)
                else:
                    self.socket_recv_queue.put(msg)
        except queue.Empty:
            pass
        except OSError:
            print('Lost connection to Host.')
            self.lost_host()
    
    def socket_send_msg(self, formatted_msg):
        '''
        This handles >1024 byte messages use always and only with receive
        '''
        msg_to_send = self.header_formation(format_message)
        self.host_sock.send(msg_to_send)
    
    def header_formation(self, formatted_msg):
        header = ""
        length_of_message = len(formatted_msg) + len("HARALD")
        if self.supportLongMessages and length_of_message > 1024:
            header = "HAR" + length_of_message + "ALD"        
        
        msg_to_send = header + formatted_msg
    
    def start_host(self):
        self.host_sock = None
        self.should_stop_hosting = False

        self.advertise_thread = threading.Thread(
            target=self.advertise,
            args=[self.client_socks],
            )
        self.advertise_thread.setDaemon(True)
        self.advertise_thread.start()

        #self.check_others_thread = threading.Thread(
        #    target=self.check_others,
        #    )
        #self.check_others_thread.setDaemon(True)
        #self.check_others_thread.start()

    def start_client(self):
        self.synchronizing = True
        self.should_stop_hosting = True

        self.client_thread = threading.Thread(
            target=self.client_connect
            )
        self.client_thread.setDaemon(True)
        self.client_thread.start()

    def stop(self):
        print('Sorry. If you wish to stop, you must implement it. :)')

    def client_connect(self):
        '''
        Client searches and connects to Host using this.
        '''
        print('Searching all nearby bluetooth devices for the Host')

        uuid = 'c125a726-4370-4745-9787-b486c687c3a4'
        addr = None
        service_matches = find_service( uuid = uuid, address = addr )

        if len(service_matches) == 0:
            print('Couldn\'t find the Host =(')
            sys.exit(0)

        perfect_match = None
        earliest = None
        for match in service_matches:
            match_name = match['name'].decode('utf-8').split(' ')
            match_group = ' '.join(match_name[:-2])
            match_date = match_name[-2:-1][0]
            match_time = match_name[-1:][0]
            parsed = match_date + ' ' + match_time
            datetime = parser.parse(parsed)
            if match_group == self.group:
                if earliest == None or earliest > datetime:
                    perfect_match = match

        if perfect_match is None:
            print('Couldn\'t find the Host of ' + self.group)
            sys.exit(0)

        port = perfect_match['port']
        name = perfect_match['name'].decode('utf-8')
        host = perfect_match['host']

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
        '''
        This continuously advertises Host's service and takes in new clients.
        '''
        server_sock = BluetoothSocket(RFCOMM)
        server_sock.bind(('', PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        uuid = 'c125a726-4370-4745-9787-b486c687c3a4'

        self.own_datetime = datetime.datetime.utcnow()
        name = self.group + ' ' + str(self.own_datetime)

        advertise_service(server_sock,
                          name,
                          service_id = uuid,
                          service_classes = [ uuid, SERIAL_PORT_CLASS ],
                          profiles = [ SERIAL_PORT_PROFILE ])

        print('Advertising service on RFCOMM port %d' % port)

        while True:
            if self.should_stop_hosting:
                return
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
                self.send_sync_command()
            else:
                client_sock.close()
                print('Denied connection from ', client_info)

    def receive(self, sock):
        '''
        This listens to receiving socket all the time.
        Large messages > 1024 bytes come in multiple messages, so those are handled aswell.
        '''
        msg = ""
        remaining = -1 # -1 for unknown
        while True:
            try:
                data = sock.recv(1024)
                # The problem occurs if header is found from the end of previous message due latency.
                if data:
                    string_data = data.decode('utf-8')
                    if (remaining <= 0):
                    # pass data to msg - start buffer if needed
                        if self.supportLongMessages:
                            try:
                                header_end_index = string_data.find('ALD', 0, 15)
                                json_started = string_data.find('{', 0, 15)
                                if header_end_index == -1 or json_started > -1: 
                                    #Header not found
                                    msg = string_data
                                else:
                                    header_end = header_end_index + len("ALD")
                                    header = string_data[:header_end-1]
                                    msg = string_data[header_end:]
                                    msg_length = int(header[len("HAR"):-(len("ALD")-1)])
                                    remaining = msg_length - 1024
                            except ValueError as e:
                                print(e)
                                print("ValueError on parsing header")
                                pass
                        else:
                            msg = string_data  
                    
                    else:
                    # buffer has been started
                        msg += string_data
                        remaining = remaining - 1024
                        
                    if remaining <= 0:
                    # message is ready to parse
                        try:
                            formatted_data = format_message(msg)
                            self.socket_recv_queue.put(formatted_data)
                        except ValueError as e:
                            print(e)
                            print("Message lost..")
                            pass
                    #print("Harald received:", string_data)

            except OSError:
                if self.host_sock:
                    print('Lost connection to Host. Closing this receive thread.')
                else:
                    print('Lost connection to a Client. Closing this receive thread.')
                sock.close()
                return

    def check_others(self):
        while True:
            print('Checking if there are other Hosts')

            uuid = 'c125a726-4370-4745-9787-b486c687c3a4'
            addr = None
            service_matches = find_service( uuid = uuid, address = addr )

            if len(service_matches) == 0:
                print('No other Hosts found')

            else:
                for match in service_matches:
                    match_name = match['name'].decode('utf-8').split(' ')
                    match_group = ' '.join(match_name[:-2])
                    match_date = match_name[-2:-1][0]
                    match_time = match_name[-1:][0]
                    parsed = match_date + ' ' + match_time
                    datetime = parser.parse(parsed)
                    if match_group == self.group:
                        if self.own_datetime > datetime:
                            print('Found earlier Host: ' + match['host'])
                            self.should_stop_hosting = True
                            self.start_client()
                        else:
                            print('Found later Host ' + match['host'])

    def lost_host(self):
        print('Host lost. Starting as new Host.')
        self.host_sock = None
        self.start_host()

    def ask_access(self, sock):
        '''
        Client sends access request to Host and waits for response.
        Client notifies TextEditor if access is denied.
        '''
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
        '''
        Host responds to client request IF passwords match.
        '''
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
        '''
        Client sends Host a sync request.
        This is used when Client realizes it is confused.
        '''
        sync_request = {
            'source': 'send_sync_request',
            'message': 'SYNCHRONIZE WITH ME',
            '_from': None,
            '_to': None,
            '_type': 'sync_request',
            '_order': None,
        }

        formatted_sync_request = json.dumps(sync_request)
        self.socket_send_msg(formatted_sync_request)
        #self.host_sock.send(formatted_sync_request)

    def send_sync_command(self):
        '''
        Host sends itself a sync request to force clients to sync.
        This is used when a new client joins the group.
        '''
        sync_command = {
            'source': 'send_sync_command',
            'message': 'SYNCHRONIZE WITH ME',
            '_from': None,
            '_to': None,
            '_type': 'sync_request',
            '_order': None,
        }

        self.recv_queue.put(sync_command)
