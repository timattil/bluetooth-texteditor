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
        self.recv()

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
        #self.insert(args[0], args[1])

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
        #self.delete(args[0])
    
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
        self.log(**out)
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
                self.log('recv', message_text, _from=_from, _to=_to, _type=_type, _order=_order)
                if _type == 'insert':
                    self.insert(_from, message_text)
                elif _type == 'delete':
                    self.delete(_from, _to)
                else:
                    self.log('recv', 'Could not handle message type.', _type=_type)
        except queue.Empty:
            pass
        self.parent.after(10, self.recv)
