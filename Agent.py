import time
import numpy as np
from Message import *


class Agent:

    def __init__(self, color, receive_queue, send_queue):
        self.color = color
        self.received = receive_queue
        self.sent = send_queue
        self.steps = 0
        self.loop()

    def send_message(self):
        direc = ["North", "West", "East", "South"]
        msg = "move %s" % np.random.choice(direc)

        dest = "environment"
        self.sent.put(Message(self.color, dest, msg, Message.INFORM, "test-%s" % self.color))
        self.steps += 1

    def receive_message(self):
        try:
            data = self.received.get(False)
            print("This is: ", self.color)
            print(data)
        except:
            pass

    def loop(self):
        self.send_message()
        self.receive_message()
        time.sleep(1)
        self.loop()
