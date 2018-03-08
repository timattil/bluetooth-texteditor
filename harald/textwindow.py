import hashlib
import queue
import tkinter as tk
from time import gmtime, strftime


def now():
    return strftime('%H:%M:%S', gmtime())


class TextWindow(tk.Text):
    def __init__(self, parent):
        tk.Text.__init__(self, parent)
        self.parent = parent
        self.last_hash = self.get_hash()
        self.config(undo=False)

    def start(self):
        self.set_last()
        self.last_written()
        self.bind('<BackSpace>', self.text_deleted)
        self.bind('<Control-x>', self.cut_text)

    def set_last(self):
        self.mark_set('last', 'insert')
        self.mark_gravity('last', 'left')

    def log(self, source=None, message=None, *args, **kwargs):
        '''Unified logging for all methods.'''
        log_message = '{} @ {}: "{}"'.format(now(), source, message)
        if args:
            log_message = '{} args:{}'.format(log_message, args)
        if kwargs:
            log_message = '{} kwargs:{}'.format(log_message, kwargs)
        print(log_message)

    def output(self, source, message, _from=None, _to=None, _type=None):
        '''Stub for the unified output method.'''
        out = {
            'source': source,
            'message': message,
            '_from': _from,
            '_to': _to,
            '_type': _type,
        }
        self.log(**out)
        self.parent.send_queue.put(out)

    def get_hash(self):
        return hashlib.md5(self.get('1.0', 'end').encode('utf-8')).digest()

    def has_changed(self):
        if self.last_hash != self.get_hash():
            return True
        else:
            return False

    def last_written(self):
        last_text = self.get('last', 'insert')
        if last_text and self.has_changed():
            out = last_text
            self.last_hash = self.get_hash()
        else:
            out = None
        if out is not None:
            self.output(
                source='last_written',
                message=out,
                _type='insert',
                _from=self.index('last'),
            )
        self.parent.after(10, self.last_written)
        self.set_last()
        self.recv()

    def recv(self):
        try:
            message = self.parent.recv_queue.get_nowait()
            _from = message.get('_from')
            _to = message.get('_to')
            message_text = message.get('message')
            if message.get('_type') == 'insert':
                self.log('recv', message_text, _from=_from, _to=_to)
                self.insert(_from, message_text)
        except queue.Empty:
            pass

    def text_deleted(self, *args):
        try:
            _from = self.index('sel.first')
            _to = self.index('sel.last')
        except tk.TclError:
            _from = 'insert -1 chars'
            _to = 'insert'
        deleted_text = self.get(_from, _to)
        self.output(
            source='text_deleted',
            message=deleted_text,
            _from=self.index(_from),
            _to=self.index(_to),
            _type='delete',
        )
        self.delete(_from, _to)
        self.last_hash = self.get_hash()
        return 'break'

    def cut_text(self, *args):
        try:
            _from = self.index('sel.first')
            _to = self.index('sel.last')
        except tk.TclError:
            self.log('cut_text', 'no selection')
            return 'break'
        deleted_text = self.get(_from, _to)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(deleted_text)
        self.output(
            source="cut_text",
            message=deleted_text,
            _from=self.index(_from),
            _to=self.index(_to),
            _type='delete',
        )
        self.delete(_from, _to)
        self.last_hash = self.get_hash()
        return 'break'
