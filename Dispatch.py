from Message import *
import time

class Dispatch:
    def __init__(self, queues):
        self.queues = queues
        self.route()

    def route(self):
        for agent, queue in self.queues.items():
            try:
                message = queue.get(False)
                self.queues[message.dest].put(message)
            except:
                pass
        time.sleep(5)
        self.route()
