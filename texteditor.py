import hashlib
import tkinter as tk
from time import gmtime, strftime


def now():
    return strftime('%H:%M:%S', gmtime())


class Text_editor_program(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.set_text_window()

    def set_text_window(self):
        self.text_window = Text_window(self)
        self.text_window.grid()
        self.text_window.start()


class Text_window(tk.Text):
    def __init__(self, parent):
        tk.Text.__init__(self, parent)
        self.parent = parent
        self.last_hash = self.get_hash()

    def start(self):
        self.set_last()
        self.last_written()
        self.bind('<BackSpace>', self.text_deleted)
        self.bind('<Control-x>', self.cut_text)

    def set_last(self):
        self.mark_set('last', 'insert')
        self.mark_gravity('last', 'left')

    def print_out(func):
        def wrapped_function(self, *args, **kwargs):
            text = func(self, *args, **kwargs)
            if text:
                print('{}: {}'.format(now(), text))
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
        if last_text and self.has_changed():
            out = last_text
            self.last_hash = self.get_hash()
        else:
            out = None
        self.parent.after(10, self.last_written)
        self.set_last()
        return out

    def text_deleted(self, *args):
        try:
            _from = self.index('sel.first')
            _to = self.index('sel.last')
        except tk.TclError:
            _from = 'insert -1 chars'
            _to = 'insert'
        deleted_char = self.get(_from, _to)
        print(now(), "DELETED:", deleted_char, self.index(_from), self.index(_to))
        self.delete(_from, _to)
        return 'break'

    def cut_text(self, *args):
        try:
            _from = self.index('sel.first')
            _to = self.index('sel.last')
        except tk.TclError:
            print(now(), 'CUT: no selection.')
            return 'break'
        deleted_char = self.get(_from, _to)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(deleted_char)
        print(now(), "CUT:", deleted_char, self.index(_from), self.index(_to))
        self.delete(_from, _to)
        return 'break'


if __name__ == '__main__':
    program = Text_editor_program()
    program.mainloop()
