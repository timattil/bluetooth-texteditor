import queue
import tkinter as tk
from textwindow import TextWindow


class TextEditorProgram(tk.Tk):
    def __init__(self, send_queue, recv_queue):
        tk.Tk.__init__(self)
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.set_TextWindow()

    def set_TextWindow(self):
        self.textWindow = TextWindow(self)
        self.textWindow.grid()
        self.textWindow.start()


if __name__ == '__main__':
    send_queue = queue.Queue()
    recv_queue = queue.Queue()
    program = TextEditorProgram(send_queue, recv_queue)
    program.mainloop()
