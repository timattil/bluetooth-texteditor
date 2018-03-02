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
        self.text_bouncer = Text_bouncer(self, send_queue, recv_queue)
        self.set_text_window()

    def set_text_window(self):
        self.text_window = Text_window(self)
        self.text_window.grid()
        self.text_window.start()

    def quit(self):
        self.text_bouncer.stop()
        self.text_bouncer.join()

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

class Text_bouncer(th.Thread):
    def __init__(self, parent, send_queue, recv_queue):
        th.Thread.__init__(self)
        self.parent = parent
        self._stop_event = th.Event()
        self.start()

    def run(self):
        while not self._stop_event.is_set():
            try:
                data = recv_queue.get_nowait()
                self.parent.text_window.insert('last', data)
                recv_queue.task_done()
            except queue.Empty:
                pass

    def stop(self):
        self._stop_event.set()

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
            data = send_queue.get_nowait()
            print(data)
            send_queue.task_done()
        except queue.Empty:
            pass

    def receive(self):
        data = self.sock.recv(1024)
        if len(data) == 0:
            return
        recv_queue.put(data)

def start_bluetooth():
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

    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)

    return client_sock

if __name__ == '__main__':
    client_sock = start_bluetooth()

    send_queue = queue.Queue()
    recv_queue = queue.Queue()

    bl_comms = Bluetooth_comms(client_sock, send_queue, recv_queue)

    text_editor = Text_editor(send_queue, recv_queue)
    text_editor.mainloop()
    text_editor.quit()

    bl_comms.stop()
    bl_comms.join()

    print('allsgood')
