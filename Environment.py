import tkinter as tk
import time
from Message import *
from constants import *


class Environment:
    scale = 70

    def __init__(self, h, w, holes_depth, holes_col,
                 tiles_no, tiles_col, agents, agent_pos, obstacles, receive_queue, send_queue, t, T, done):
        self.H = h
        self.W = w
        self.done = done
        self.t = t
        self.T = T
        self.holes_depth = holes_depth
        self.holes_col = holes_col
        self.tiles_no = tiles_no
        self.tiles_col = tiles_col
        self.current_time = 0
        self.step = 1
        self.agent_obj = {}
        self.tiles_obj = {}
        self.holes_obj = {}
        self.received = receive_queue
        self.sent = send_queue
        self.agents = agents
        self.holding = {x: None for x in self.agents}
        self.agent_pos = agent_pos
        self.obstacles = obstacles
        self.messages = {x: [] for x in self.agents}
        self.main_window = tk.Tk()
        self.canvas = tk.Canvas(self.main_window, width=w * Environment.scale, height=h * Environment.scale)
        self.canvas.pack()
        self.create_grid()
        self.print_obstacles()
        self.print_tiles()
        self.print_holes()
        self.print_agents()
        self.loop()
        tk.mainloop()

    def create_grid(self):
        for i in range(self.H):
            self.canvas.create_line(0, Environment.scale * i, Environment.scale * self.W, Environment.scale * i)
        for j in range(self.W):
            self.canvas.create_line(Environment.scale * j, 0, Environment.scale * j, Environment.scale * self.H)

    def print_obstacles(self):
        for i in range(self.H):
            for j in range(self.W):
                if self.obstacles[i, j] != 0:
                    self.canvas.create_rectangle(Environment.scale * j, Environment.scale * i,
                                                 Environment.scale * (j + 1), Environment.scale * (i + 1), fill="black")

    def print_agents(self):
        offset = Environment.scale / 10
        agent_size = Environment.scale / 5
        for agent, pos in self.agent_pos.items():
            multi_agent_offset = offset * self.agents.index(agent)
            i = pos[0]
            j = pos[1]
            self.agent_obj[agent] = self.canvas.create_oval(Environment.scale * j + offset + multi_agent_offset,
                                                            Environment.scale * i + offset,
                                                            Environment.scale * j + offset + agent_size + multi_agent_offset,
                                                            Environment.scale * i + offset + agent_size,
                                                            fill=agent)

    def print_holes(self):
        offset = Environment.scale / 5
        for i in range(self.H):
            for j in range(self.W):
                if self.holes_depth[i, j] != 0:
                    self.canvas.create_rectangle(Environment.scale * j, Environment.scale * i,
                                                 Environment.scale * (j + 1), Environment.scale * (i + 1),
                                                 fill=self.agents[self.holes_col[i, j]])
                    self.holes_obj[(i, j)] = self.canvas.create_text(Environment.scale * (j + 1) - offset,
                                                                     Environment.scale * i + offset,
                                                                     text=str(self.holes_depth[i, j]), fill="gray")

    def print_tiles(self):
        offset = Environment.scale / 10
        agent_size = Environment.scale / 5
        for i in range(self.H):
            for j in range(self.W):
                if self.tiles_no[i, j] != 0:
                    self.canvas.create_rectangle(Environment.scale * j + offset, Environment.scale * (i + 1) - offset,
                                                 Environment.scale * j + offset + agent_size,
                                                 Environment.scale * (i + 1) - (offset + agent_size),
                                                 fill=self.agents[self.tiles_col[i, j]])
                    self.tiles_obj[(i, j)] = self.canvas.create_text(Environment.scale * j + offset * 2,
                                                                     Environment.scale * (i + 1) - (
                                                                             offset + agent_size) * 0.7,
                                                                     text=str(self.tiles_no[i, j]),
                                                                     fill="gray")

    def get_messages(self):
        try:
            msg_recv = self.received.get(False)
            print(f'[{round(self.current_time, 2)}][ENV][{msg_recv.sender}] {msg_recv.content}')
            self.messages[msg_recv.sender].append((msg_recv, self.current_time))
        except:
            pass

    def do_actions(self):
        for agent in self.agents:
            if len(self.messages[agent]) == 0:
                continue
            if self.current_time - self.messages[agent][0][1] == self.t:
                msg_recv = self.messages[agent].pop(0)[0]
            else:
                continue
            content = None
            if "move" in msg_recv.content:
                direction = msg_recv.content.split()[1]
                new_pos = self.agent_pos[msg_recv.sender] + DIRECTIONS[direction]
                if (0 <= new_pos[1] < self.W) and (0 <= new_pos[0] < self.H) and \
                        self.obstacles[new_pos[0], new_pos[1]] == 0 and self.holes_depth[new_pos[0], new_pos[1]] == 0:
                    self.agent_pos[msg_recv.sender] = new_pos
                    self.canvas.move(self.agent_obj[msg_recv.sender], DIRECTIONS[direction][1] * Environment.scale,
                                     DIRECTIONS[direction][0] * Environment.scale
                                     )
                    content = "success"

                else:
                    content = "failed"

            if "pick" in msg_recv.content:
                pos = self.agent_pos[msg_recv.sender]
                if self.tiles_no[pos[0], pos[1]] != 0 and self.holding[msg_recv.sender] is None:
                    self.tiles_no[pos[0], pos[1]] -= 1
                    self.holding[msg_recv.sender] = self.agents[self.tiles_col[pos[0], pos[1]]]
                    self.canvas.itemconfig(self.tiles_obj[(pos[0], pos[1])], text=str(self.tiles_no[pos[0], pos[1]]))
                    content = "success"
                else:
                    content = "failed"

            if "use-tile" in msg_recv.content:
                direction = msg_recv.content.split()[1]
                pos = self.agent_pos[msg_recv.sender]
                h_pos = pos + DIRECTIONS[direction]

                if self.holes_depth[h_pos[0], h_pos[1]] != 0 and self.holding[msg_recv.sender] is not None:
                    self.holes_depth[h_pos[0], h_pos[1]] -= 1
                    self.holding[msg_recv.sender] = None
                    self.canvas.itemconfig(self.holes_obj[(h_pos[0], h_pos[1])],
                                           text=str(self.holes_depth[h_pos[0], h_pos[1]]))
                    content = "success"
                else:
                    content = "failed"
            if content == "success":
                print(f'[{round(self.current_time, 2)}][ENV][{msg_recv.sender}] Operation Done')
            msg = Message('environment', msg_recv.sender, content, Message.INFORM, msg_recv.conv_id)
            self.sent.put(msg)

    def stop(self):
        for agent in self.agents:
            msg = Message('environment', 'agent', 'stop', Message.INFORM, f'stop-{agent}')
            self.sent.put(msg)
        print("[ENV] Stopped")
        self.done.value = 1
        while True:
            time.sleep(10000)

    def loop(self):
        if self.current_time == self.T:
            self.stop()
        self.get_messages()
        self.do_actions()
        self.current_time += self.step
        self.main_window.after(int(SLEEP_TIME * 100), self.loop)


if __name__ == '__main__':
    env = Environment(10, 20)
