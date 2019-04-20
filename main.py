import sys
from multiprocessing import Process, Queue

import numpy as np

from Agent import *
from Dispatch import *
from Environment import *


def parse_and_start(file):
    with open(file, "r") as f:
        lines = f.read().split('\n')
    lines = ' '.join(lines).split()
    data = list(filter(lambda x: len(x) != 0, lines))
    print(data)
    N = int(data[0])
    t = int(data[1])
    T = int(data[2])
    W = int(data[3])
    H = int(data[4])
    agents = data[5:5 + N]
    last = 5 + N

    agent_pos = np.zeros((H, W), dtype=np.int) - 1
    agent_no = 0
    for i in range(last, last + 2 * N, 2):
        agent_pos[int(data[i + 1]), int(data[i])] = agent_no
        agent_no += 1
    last = last + N * 2 + 1

    obstacles = np.zeros((H, W), dtype=np.int)
    while data[last] != "TILES":
        obstacles[int(data[last + 1]), int(data[last])] = 1
        last += 2
    last += 1

    tiles_no = np.zeros((H, W), dtype=np.int)
    tiles_col = np.zeros((H, W), dtype=np.int) - 1
    while data[last] != "HOLES":
        tiles_no[int(data[last + 3]), int(data[last + 2])] = int(data[last])
        tiles_col[int(data[last + 3]), int(data[last + 2])] = agents.index(data[last + 1])
        last += 4
    last += 1

    holes_depth = np.zeros((H, W), dtype=np.int)
    holes_col = np.zeros((H, W), dtype=np.int) - 1
    while last < len(data):
        holes_depth[int(data[last + 3]), int(data[last + 2])] = int(data[last])
        holes_col[int(data[last + 3]), int(data[last + 2])] = agents.index(data[last + 1])
        last += 4
    print(obstacles)
    env_q = Queue()
    env = Process(target=Environment, args=(H, W, holes_depth, holes_col,
                                            tiles_no, tiles_col, agents, agent_pos, obstacles, env_q))
    env.start()
    queues = {"environment": env_q}
    agent_processes = []
    for agent in agents:
        queues[agent] = Queue()
        agent_processes.append(Process(target=Agent, args=(agent, queues[agent])))
        agent_processes[-1].start()
    dispatch = Process(target=Dispatch, args=(queues,))
    dispatch.start()
    env.join()
    dispatch.join()
    for agent in agent_processes:
        agent.join()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        file = "system.txt"
    else:
        file = sys.argv[1]
    parse_and_start(file)
