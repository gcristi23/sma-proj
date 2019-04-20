import time

from Message import *


class Agent:

    def __init__(self, color, queue):
        self.color = color
        self.queue = queue
        self.loop()

    def send_message(self):
        if self.color == "blue":
            dest = "green"
        else:
            dest = "environment"
        self.queue.put(Message(self.color, dest, self.color, Message.INFORM, "test-%s" % self.color))

    def receive_message(self):
        try:
            data = self.queue.get(False)
            print(data)
        except:
            pass

    def loop(self):
        self.send_message()
        self.receive_message()
        time.sleep(5)
        self.loop()
