import time
from constants import SLEEP_TIME


class Dispatch:
    def __init__(self, receive_queues, send_queues):
        self.receive_queues = receive_queues
        self.send_queues = send_queues
        self.route()

    def route(self):
        for agent, queue in self.send_queues.items():
            try:
                message = queue.get(False)
                self.receive_queues[message.dest].put(message)
            except:
                pass
        time.sleep(SLEEP_TIME*0.1)
        self.route()
