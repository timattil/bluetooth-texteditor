from bluetooth import *
import threading
import sys
import time
import texteditor

class Receiver(threading.Thread):
    def __init__(self, sock, program):
        threading.Thread.__init__(self)
        self.text_editor = program
        self._stop_event = threading.Event()
        self.start()

    def run(self):
        try:
            while not self._stop_event.is_set():
                data = sock.recv(1024)
                if len(data) != 0:
                    self.text_editor.text_window.insert('last', data)
                    print('Received {}'.format(data))
        except IOError:
            pass

    def stop(self):
        self._stop_event.set()

class Sender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.start()

    def run(self):
        try:
            while not self._stop_event.is_set():
                data = sock.send(1024)
                if len(data) != 0:
                    self.text_editor.text_window.insert('last', data)
                    print('Received {}'.format(data))
        except IOError:
            pass

    def stop(self):
        self._stop_event.set()

if __name__ == '__main__':
    if sys.version < '3':
        input = raw_input

    addr = None

    if len(sys.argv) < 2:
        print("No device specified.  Searching all nearby bluetooth devices for the SampleServer service.")
    else:
        addr = sys.argv[1]
        print("Searching for SampleServer on %s" % addr)

    # search for the SampleServer service
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    service_matches = find_service( uuid = uuid, address = addr )

    if len(service_matches) == 0:
        print("Couldn't find the SampleServer service =(")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    print("Connecting to \"%s\" on %s" % (name, host))

    # Create the client socket
    sock=BluetoothSocket( RFCOMM )
    sock.connect((host, port))

    text_editor = texteditor.Text_editor_program()

    receiver = Receiver(sock, text_editor)
    sender = Sender()

    text_editor.mainloop()

    receiver.stop()
    sender.stop()
    receiver.join()
    sender.join()

    sock.close()

'''
def listen(sock, should_close):
    try:
        while True:
            data = sock.recv(1024)
            if len(data) == 0:
                print('listen should close')
                should_close = True
                break
            print('Received {}'.format(data))
    except IOError:
        pass

def send(sock, should_close):
    while True:
        data = input()
        if len(data) == 0:
            print('send should close')
            should_close = True
            break
        sock.send(data)

if __name__ == '__main__':
    if sys.version < '3':
        input = raw_input

    addr = None

    if len(sys.argv) < 2:
        print("No device specified.  Searching all nearby bluetooth devices for the SampleServer service.")
    else:
        addr = sys.argv[1]
        print("Searching for SampleServer on %s" % addr)

    # search for the SampleServer service
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    service_matches = find_service( uuid = uuid, address = addr )

    if len(service_matches) == 0:
        print("Couldn't find the SampleServer service =(")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    print("Connecting to \"%s\" on %s" % (name, host))

    # Create the client socket
    sock=BluetoothSocket( RFCOMM )
    sock.connect((host, port))

    should_close = False
    t1 = threading.Thread(target=listen, args=(sock, should_close,))
    t2 = threading.Thread(target=send, args=(sock, should_close,))
    t1.start()
    t2.start()

    print("Connected.  Type stuff:")
    while True:
        if should_close == True:
            t1.join()
            t2.join()
            sock.close()
            break
'''
