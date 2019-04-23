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
        chance = np.random.rand()
        if chance < 0.4:
            self.pick()
        elif chance > 0.6:
            self.move()
        else:
            self.use_tile()

    def move(self):
        direc = ["North", "West", "East", "South"]
        msg = "move %s" % np.random.choice(direc)

        dest = "environment"
        self.sent.put(Message(self.color, dest, msg, Message.INFORM, "test-%s" % self.color))
        self.steps += 1

    def pick(self):
        dest = "environment"
        self.sent.put(Message(self.color, dest, "pick", Message.INFORM, "test-%s" % self.color))

    def use_tile(self):
        dest = "environment"
        direc = ["North", "West", "East", "South"]
        msg = "use-tile %s" % np.random.choice(direc)
        self.sent.put(Message(self.color, dest, msg, Message.INFORM, "test-%s" % self.color))

    def receive_message(self):
        try:
            data = self.received.get(False)
            # print("This is: ", self.color)
            # print(data)
        except:
            pass

    def loop(self):
        self.send_message()
        self.receive_message()
        time.sleep(0.1)
        self.loop()
