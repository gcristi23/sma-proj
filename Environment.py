import tkinter as tk


class Environment:
    scale = 50

    def __init__(self, h, w, holes_depth, holes_col,
                 tiles_no, tiles_col, agents, agent_pos, obstacles, queue):
        self.H = h
        self.W = w
        self.holes_depth = holes_depth
        self.holes_col = holes_col
        self.tiles_no = tiles_no
        self.tiles_col = tiles_col

        self.queue = queue
        self.agents = agents
        self.agent_pos = agent_pos
        self.obstacles = obstacles
        self.main_window = tk.Tk()
        self.canvas = tk.Canvas(self.main_window, width=w * Environment.scale, height=h * Environment.scale)
        self.canvas.pack()
        self.create_grid()
        self.print_obstacles()
        self.print_holes()
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
        for i in range(self.H):
            for j in range(self.W):
                if self.agent_pos[i, j] != -1:
                    self.canvas.create_oval(Environment.scale * j + offset, Environment.scale * i + offset,
                                            Environment.scale * j + offset + agent_size,
                                            Environment.scale * i + offset + agent_size,
                                            fill=self.agents[self.agent_pos[i, j]])


    def print_holes(self):
        for i in range(self.H):
            for j in range(self.W):
                if self.holes_depth[i, j] != 0:
                    self.canvas.create_rectangle(Environment.scale * j, Environment.scale * i,
                                                 Environment.scale * (j + 1), Environment.scale * (i + 1),
                                                 fill=self.agents[self.holes_col[i, j]])

    def print_tiles(self):
        offset = Environment.scale / 10
        agent_size = Environment.scale / 5
        for i in range(self.H):
            for j in range(self.W):
                if self.tiles_no[i, j] != 0:
                    self.canvas.create_rectangle(Environment.scale * j + offset, Environment.scale * (i + 1) - offset,
                                                 Environment.scale * j + offset + agent_size,
                                                 Environment.scale * (i+1) - (offset + agent_size),
                                                 fill=self.agents[self.tiles_col[i, j]])
                    self.canvas.create_text(Environment.scale * j + offset*2,
                                            Environment.scale * (i+1) - (offset + agent_size)*0.7,
                                            text=str(self.tiles_no[i, j]),
                                            fill="white")

    def loop(self):
        try:
            data = self.queue.get(False)
            print(data)
        except:
            pass
        self.print_tiles()
        self.print_agents()
        self.main_window.after(500, self.loop)


if __name__ == '__main__':
    env = Environment(10, 20)
