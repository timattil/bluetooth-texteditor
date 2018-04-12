import queue
import threading
import tkinter as tk
from textwindow2 import TextWindow
from harald import harald2

class TextEditorProgram(tk.Tk):
    def __init__(self, send_queue, recv_queue):
        tk.Tk.__init__(self)
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.set_harald(send_queue, recv_queue)
        self.set_buttons()
        self.password_field = self.set_password_field()
        self.set_TextWindow()

    def set_harald(self, send_queue, recv_queue):
        self.harald = harald2.Harald(send_queue, recv_queue)

    def set_buttons(self):
        self.client_button = tk.Button(
            self,
            text='Client',
            command=self.client_button_command,
        )
        self.host_button = tk.Button(
            self,
            text='Host',
            command=self.host_button_command,
        )
        self.client_button.grid(row=0, column=8)
        self.host_button.grid(row=0, column=12)

    def set_password_field(self):
        self.password_label = tk.Label(self, text='Password:')
        self.password_field = tk.Entry(self)
        self.password_label.grid(row=0, column=0)
        self.password_field.grid(row=0, column=1)
        self.password_field.config(show="*")
        return self.password_field

    def client_button_command(self):
        print('Client selected')
        password = self.password_field.get()
        self.harald.set_password(password)
        self.harald.start_client()
        self.disable_buttons()

    def host_button_command(self):
        print('Host selected')
        password = self.password_field.get()
        self.harald.set_password(password)
        self.harald.start_host()
        self.disable_buttons()

    def disable_buttons(self):
        for button in (self.client_button, self.host_button):
            button.config(state='disabled')

    def set_TextWindow(self):
        self.textWindow = TextWindow(self)
        self.textWindow.grid(row=1, column=0, columnspan=16)

if __name__ == '__main__':
    send_queue = queue.Queue()
    recv_queue = queue.Queue()
    program = TextEditorProgram(send_queue, recv_queue)
    program.mainloop()
