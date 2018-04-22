import hashlib
import queue
import tkinter as tk
from time import gmtime, strftime
from idlelib.WidgetRedirector import WidgetRedirector

def now():
    return strftime('%H:%M:%S', gmtime())

class TextWindow(tk.Text):
    def __init__(self, parent):
        tk.Text.__init__(self, parent)
        self.redirector = WidgetRedirector(self)
        self.insert = self.redirector.register("insert", self.myinsert)
        self.delete = self.redirector.register("delete", self.mydelete)
        self.parent = parent
        self.config(undo=False)
        self.load_cache()
        self.recv()
        self.save_cache()

    def myinsert(self, *args):
        _from = self.index('insert')
        _to = self.index('last')
        self.output(
            source='myinsert',
            message=args[1],
            _from=_from,
            _to=_to,
            _type=args[0],
            _order=None,
        )

    def mydelete(self, *args):
        _from = self.index('insert-1c')
        _to = self.index('insert')
        self.output(
            source='mydelete',
            message=None,
            _from=_from,
            _to=_to,
            _type='delete',
            _order=None,
        )
    
    def log(self, source=None, message=None, *args, **kwargs):
        '''Unified logging for all methods.'''
        log_message = '{} @ {}: "{}"'.format(now(), source, message)
        if args:
            log_message = '{} args:{}'.format(log_message, args)
        if kwargs:
            log_message = '{} kwargs:{}'.format(log_message, kwargs)
        print(log_message)
    
    def output(self, source, message, _from=None, _to=None, _type=None, _order=None):
        '''Stub for the unified output method.'''
        out = {
            'source': source,
            'message': message,
            '_from': _from,
            '_to': _to,
            '_type': _type,
            '_order': _order,
        }
        #self.log(**out)
        self.parent.send_queue.put(out)

    def recv(self):
        try:
            while True:
                message = self.parent.recv_queue.get_nowait()
                _from = message.get('_from')
                _to = message.get('_to')
                message_text = message.get('message')
                _type = message.get('_type')
                _order = message.get('_order')
                self.log('recv', repr(message_text), _from=_from, _to=_to, _type=_type, _order=_order)
                if _type == 'insert':
                    self.insert(_from, message_text)
                elif _type == 'delete':
                    self.delete(_from, _to)
                elif _type == 'sync_request':
                    self.send_all_text()
                elif _type == 'sync_response':
                    self.receive_all_text(message_text)
                elif _type == 'authentication' and message_text == 'denied':
                    self.parent.enable_buttons()
                else:
                    self.log('recv', 'Could not handle message type.', _type=_type)
        except queue.Empty:
            pass
        self.parent.after(10, self.recv)

    def send_all_text(self):
        all_text = self.get('1.0', 'end-1c')
        self.output(
            source='send_whole_text',
            message=all_text,
            _from=None,
            _to=None,
            _type='sync_response',
            _order=None,
        )

    def receive_all_text(self, all_text):
        self.delete('1.0', 'end-1c')
        self.insert('1.0', all_text)

    def save_cache(self):
        all_text = self.get('1.0', 'end-1c')
        with open('cache.txt', 'w') as text_file:
            print(all_text, file=text_file)
        self.parent.after(1000, self.save_cache)

    def load_cache(self):
        with open('cache.txt', 'r') as text_file:
            cached_text = text_file.read()
            cached_text = cached_text.rstrip('\n') # save_cache() adds a newline to the cached text
            self.insert('1.0', cached_text)