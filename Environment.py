import tkinter as tk

import numpy as np


class Environment:
    scale = 70

    def __init__(self, h, w, holes_depth, holes_col,
                 tiles_no, tiles_col, agents, agent_pos, obstacles, receive_queue, send_queue):
        self.H = h
        self.W = w
        self.holes_depth = holes_depth
        self.holes_col = holes_col
        self.tiles_no = tiles_no
        self.tiles_col = tiles_col

        self.directions = {"North": np.array([0, -1]), "West": np.array([-1, 0]), "East": np.array([1, 0]),
                           "South": np.array([0, 1])}
        self.agent_obj = {}
        self.received = receive_queue
        self.sent = send_queue
        self.agents = agents
        self.agent_pos = agent_pos
        self.obstacles = obstacles
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
            j = pos[0]
            i = pos[1]
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
                    self.canvas.create_text(Environment.scale * (j + 1) - offset, Environment.scale * i + offset,
                                            text=str(self.holes_depth[i, j]), fill="white")

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
                    self.canvas.create_text(Environment.scale * j + offset * 2,
                                            Environment.scale * (i + 1) - (offset + agent_size) * 0.7,
                                            text=str(self.tiles_no[i, j]),
                                            fill="white")

    def get_messages(self):
        try:
            data = self.received.get(False)
            print(data)
            if "move" in data.content:
                direction = data.content.split()[1]
                new_pos = self.agent_pos[data.sender] + self.directions[direction]
                if (0 <= new_pos[0] < self.W) and (0 <= new_pos[1] < self.H) and \
                        self.obstacles[new_pos[1], new_pos[0]] == 0 and self.holes_depth[new_pos[1], new_pos[0]] == 0:
                    self.agent_pos[data.sender] = new_pos
                    self.canvas.move(self.agent_obj[data.sender], self.directions[direction][0] * Environment.scale,
                                     self.directions[direction][1] * Environment.scale
                                     )
                else:
                    print("%s can't move %s" % (data.sender, direction))

        except:
            pass

    def loop(self):
        self.get_messages()
        self.main_window.after(500, self.loop)


if __name__ == '__main__':
    env = Environment(10, 20)
