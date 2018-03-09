import queue
import threading
import tkinter as tk
from textwindow import TextWindow
#from temp import client, server
from harald import harald

class TextEditorProgram(tk.Tk):
    def __init__(self, send_queue, recv_queue):
        tk.Tk.__init__(self)
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.set_harald(send_queue, recv_queue)
        self.set_buttons()
        self.set_TextWindow()

    def set_harald(self, send_queue, recv_queue):
        self.harald = harald.Harald(send_queue, recv_queue)

    def set_buttons(self):
        self.client_button = tk.Button(
            self,
            text='CLIENT',
            command=self.client_button_command,
        )
        self.host_button = tk.Button(
            self,
            text='HOST',
            command=self.host_button_command,
        )
        self.client_button.grid(row=0, column=0)
        self.host_button.grid(row=0, column=1)

    def client_button_command(self):
        print('CLIENT SELECTED')
        self.harald.start_client()
        self.disable_buttons()

    def host_button_command(self):
        print('HOST SELECTED')
        self.harald.start_host()
        self.disable_buttons()

    def disable_buttons(self):
        for button in (self.client_button, self.host_button):
            button.config(state='disabled')

    def set_TextWindow(self):
        self.textWindow = TextWindow(self)
        self.textWindow.grid(row=1, column=0, columnspan=2)
        self.textWindow.start()


if __name__ == '__main__':
    send_queue = queue.Queue()
    recv_queue = queue.Queue()
    program = TextEditorProgram(send_queue, recv_queue)
    program.mainloop()
