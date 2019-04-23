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

    agent_pos = {}
    agent_no = 0
    for i in range(last, last + 2 * N, 2):
        agent_pos[agents[agent_no]] = np.array([int(data[i + 1]), int(data[i])])
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

    env_rcv_q = Queue()
    env_snd_q = Queue()
    env = Process(target=Environment, args=(H, W, holes_depth, holes_col,
                                            tiles_no, tiles_col, agents, agent_pos, obstacles, env_rcv_q, env_snd_q))
    env.start()
    recv_queues = {"environment": env_rcv_q}
    send_queues = {"environment": env_snd_q}
    agent_processes = []
    for agent in agents:
        recv_queues[agent] = Queue()
        send_queues[agent] = Queue()
        agent_processes.append(Process(target=Agent, args=(agent, recv_queues[agent], send_queues[agent])))
        agent_processes[-1].start()
    dispatch = Process(target=Dispatch, args=(recv_queues, send_queues))
    dispatch.start()

    dispatch.join()
    for agent in agent_processes:
        agent.join()
    env.join()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        file = "system.txt"
    else:
        file = sys.argv[1]
    parse_and_start(file)