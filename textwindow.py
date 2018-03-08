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
        self.last_selected_indexes = self.get_selected_indexes()

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
            self.check_selection_written_over()
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
        self.set_last_selected_indexes()
        self.recv()

    def check_selection_written_over(self):
        '''
        Check if previously selected text has been written over.
        Run this when new text is written, as then it's possible to write over.
        '''
        current_indexes = self.get_selected_indexes()
        changes_in_indexes = current_indexes != self.last_selected_indexes
        if changes_in_indexes:
            # selected text has been written over!
            _from, _to = self.last_selected_indexes
            self.output(
                source='selection_written_over',
                message=None,
                _from=_from,
                _to=_to,
                _type='delete',
                )

    def get_selected_indexes(self):
        try:
            _from = self.index('sel.first')
            _to = self.index('sel.last')
            selected_indexes = (_from, _to)
        except tk.TclError:
            selected_indexes = None
        return selected_indexes

    def set_last_selected_indexes(self):
        self.last_selected_indexes = self.get_selected_indexes()

    def recv(self):
        try:
            while True:
                message = self.parent.recv_queue.get_nowait()
                _from = message.get('_from')
                _to = message.get('_to')
                message_text = message.get('message')
                _type = message.get('_type')
                self.log('recv', message_text, _from=_from, _to=_to, _type=_type)
                if _type == 'insert':
                    self.insert(_from, message_text)
                elif _type == 'delete':
                    self.delete(_from, _to)
                else:
                    self.log('recv', 'Could not handle message type.', _type=_type)
        except queue.Empty:
            pass

    def text_deleted(self, *args):
        selected_indexes = self.get_selected_indexes()
        if selected_indexes is not None:
            _from, _to = selected_indexes
        else:
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
        selected_indexes = self.get_selected_indexes()
        if selected_indexes is not None:
            _from, _to = selected_indexes
        else:
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
