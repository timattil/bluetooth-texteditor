import tkinter as tk
from bluetooth import *
import threading as th
import hashlib
import queue
from time import gmtime, strftime, sleep

def now():
    return strftime('%H:%M:%S', gmtime())

class Text_editor(tk.Tk):
    def __init__(self, send_queue, recv_queue):
        tk.Tk.__init__(self)
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.set_text_window()
        self.recv()

    def set_text_window(self):
        self.text_window = Text_window(self)
        self.text_window.grid()
        self.text_window.start()

    def recv(self):
        try:
            data = self.recv_queue.get_nowait()
            self.text_window.insert('last', data)
            self.recv_queue.task_done()
        except queue.Empty:
            pass
        self.after(1, self.recv)

class Text_window(tk.Text):
    def __init__(self, parent):
        tk.Text.__init__(self, parent)
        self.parent = parent
        self.last_hash = self.get_hash()

    def start(self):
        self.bindings()
        self.set_last()
        self.last_written()

    def bindings(self):
        self.bind('<BackSpace>', self.text_deleted)
        self.bind('<Control-x>', self.text_cut)

    def set_last(self):
        self.mark_set('last', 'insert')
        self.mark_gravity('last', 'left')

    def print_out(func):
        def wrapped_function(self, *args, **kwargs):
            text = func(self, *args, **kwargs)
            if text:
                print('{}: {} @ {}'.format(now(), text[0], text[1]))
        return wrapped_function

    def get_hash(self):
        return hashlib.md5(self.get('1.0', 'end').encode('utf-8')).digest()

    def has_changed(self):
        if self.last_hash != self.get_hash():
            return True
        else:
            return False

    @print_out
    def last_written(self):
        last_text = self.get('last', 'insert')
        last_index = self.index('last')
        if last_text and self.has_changed():
            out = (last_text, last_index)
            self.last_hash = self.get_hash()
            send_queue.put(out)
        else:
            out = None
        self.parent.after(10, self.last_written)
        self.set_last()
        return out

    def text_deleted(self, *args):
        try:
            _from = self.index('sel.first')
            _to = self.index('self.last')
        except tk.TclError:
            _from = 'insert -1 chars'
            _to = 'insert'
        deleted_char = self.get(_from, _to)
        print(now(), 'DELETED: {} @ {} {}'.format(deleted_char, self.index(_from), self.index(_to)))
        self.delete(_from, _to)
        return 'break'

    def text_cut(self, *args):
        try:
            _from = self.index('sel.first')
            _to = self.index('self.last')
        except tk.TclError:
            print(now(), 'Cut: no selection')
            return 'break'
        deleted_char = self.get(_from, _to)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(deleted_char)
        print(now(), "CUT: {} @ {} {}".format(deleted_char, self.index(_from), self.index(_to)))
        self.delete(_from. _to)
        return 'break'

class Bluetooth_comms(th.Thread):
    def __init__(self, sock, send_queue, recv_queue):
        th.Thread.__init__(self)
        self.sock = sock
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self._stop_event = th.Event()
        self.start()

    def run(self):
        try:
            while not self._stop_event.is_set():
                self.send()
                self.receive()
        except IOError:
            pass

    def stop(self):
        self._stop_event.set()

    def send(self):
        try:
            data = self.send_queue.get_nowait()
            if data != None:
                self.sock.send(data[0])
                self.send_queue.task_done()
        except queue.Empty:
            pass

    def receive(self):
        try:
            data = self.recv_queue.get_nowait()
            print(data)
            self.recv_queue.task_done()
        except queue.Empty:
            pass

def start_bluetooth():
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

    return sock

if __name__ == '__main__':
    sock = start_bluetooth()

    send_queue = queue.Queue()
    recv_queue = queue.Queue()

    bl_comms = Bluetooth_comms(sock, send_queue, recv_queue)

    text_editor = Text_editor(send_queue, recv_queue)
    text_editor.mainloop()

    bl_comms.stop()
    bl_comms.join()

    print('allsgood')
