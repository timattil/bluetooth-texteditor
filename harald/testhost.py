import harald
import queue
import time
import threading

def receive(recv_queue):
    while True:
        try:
            data = recv_queue.get()
            print(data)
            recv_queue.task_done()
        except queue.Empty:
            pass

def send(send_queue):
    data = 'hello from host'
    while True:
        time.sleep(2)
        send_queue.put(data)

if __name__ == '__main__':
    send_queue = queue.Queue()
    recv_queue = queue.Queue()
    host = harald.Host(send_queue, recv_queue)
    #client = harald.Client(send_queue, recv_queue)

    recv_thread = threading.Thread(
        target=receive,
        args=[recv_queue]
    )
    recv_thread.setDaemon(True)
    recv_thread.start()

    send_thread = threading.Thread(
        target=send,
        args=[send_queue]
    )
    send_thread.setDaemon(True)
    send_thread.start()

    while True:
        time.sleep(2)
        print('Main thread running')
