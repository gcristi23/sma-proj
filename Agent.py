import time
import numpy as np
from copy import deepcopy

from constants import *
from Message import *
from pathfind import astar
from pprint import pprint

class Agent:

    def __init__(self, color, receive_queue, send_queue, H, W, holes_depth,
                 holes_col, tiles_no, tiles_col, obstacles, position,
                 color_index):
        """
        :param color: str
            The color of the agent ('blue', 'green', etc.)

        :param receive_queue: multiprocessing.Queue
            The receive queue

        :param send_queue: multiprocessing.Queue
            The send queue

        :param H: int
            The height of the grid

        :param W: int
            The width of the grid

        :param holes_depth: np.array
            A matrix of shape (H, W) that has as positive integers the depth
            of the holes (0 if there isn't a hole)
            E.g.:
            array(
            [
                [2, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 2, 0, 0],
                [0, 0, 0, 0]
            ])

        :param holes_col: np.array
            A matrix of shape (H, W) that contains the hole colors as integer
            (0 - blue, 1 - green, etc.) and -1 for the rest of the tiles
            E.g.:
            array(
            [
                [ 1, -1, -1, -1],
                [-1, -1, -1, -1],
                [-1,  0, -1, -1],
                [-1, -1, -1, -1]
            ])

        :param tiles_no: np.array
            A matrix of shape (H, W) that contains the number of available
            tiles as integer (0 if there isn't a tile available on that
            position)
            E.g.:
            array(
            [
                [0, 0, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 1, 2, 0]
            ])

        :param tiles_col: np. array
            A matrix of shape (H, W) that contains the tile colors as integer
            (0 - blue, 1 - green, etc.) and -1 for the rest of the tiles
            E.g.:
            array(
            [
                [-1, -1,  1, -1],
                [-1, -1, -1, -1],
                [-1, -1, -1, -1],
                [-1,  1,  0, -1]
            ])

        :param obstacles: np.array
            A matrix of shape (H, W) that contains the obstacles coded with the
            integer value 1
            E.g.:
            array(
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 0]
            ])

        :param position: np.array
            The agent's position on the grid.
            E.g.: [3 0]

        :param color_index: int
            The agent's color index (0, 1, etc.)
        """
        self.color = color
        self.color_index = color_index
        self.received = receive_queue
        self.sent = send_queue
        self.H = H
        self.W = W
        self.holes_depth = holes_depth
        self.holes_col = holes_col
        self.tiles_no = tiles_no
        self.tiles_col = tiles_col
        self.obstacles = obstacles
        self.position = position
        self.steps = 0
        self.crt_action = 'move_to_tile'
        self.last_msg = None
        self.timeout = RESEND_TIMEOUT
        self.loop()

    def send_message(self, msg_type, direction=None):
        """
        :param msg_type: str
            The type of the message ('pick', 'move' or 'use_tile')
        :param direction: None or str
            The direction where we want the agent to move, if it's a 'move'
            message or the direction where the tile should be used if it's
            a 'use_tile' message. Possible values are 'North', 'South', 'East'
            and 'West'.
        :return: nothing
        """
        accepted_messages = ['pick', 'move', 'use_tile', None]
        if msg_type not in accepted_messages:
            raise ValueError(f'Cannot send message with message type {str(msg_type)}. '
                             f'Accepted values are {accepted_messages}!')
        if msg_type is not None:
            if msg_type == 'pick':
                self.pick()
            elif msg_type == 'move':
                self.move(direction=direction)
            elif msg_type == 'use_tile':
                self.use_tile(direction=direction)

        # If there's no msg_type, just random it
        chance = np.random.rand()
        if chance < 0.4:
            self.pick()
        elif chance > 0.6:
            self.move()
        else:
            self.use_tile()

    def move(self, direction=None):
        """
        The function that sends a 'move' message to the environment along with
        the direction of the agent's movement.

        :param direction: None or str
            The direction where we want the agent to move,. Possible values
            are 'North', 'South', 'East' and 'West'.
        :return: nothing
        """
        possible_directions = ["North", "West", "East", "South"]
        if direction is None or direction not in possible_directions:
            direction = np.random.choice(possible_directions )

        msg = "move %s" % direction

        dest = "environment"
        send_msg = Message(
            self.color, dest, msg, Message.INFORM, "test-%s" % self.color)
        self.last_msg = deepcopy(send_msg)
        self.sent.put(send_msg)
        self.steps += 1

    def pick(self):
        """
        The function that sends a 'pick' message to the environment.

        :return: nothing
        """
        dest = "environment"
        send_msg = Message(
            self.color, dest, "pick", Message.INFORM, "test-%s" % self.color)
        self.last_msg = deepcopy(send_msg)
        self.sent.put(send_msg)

    def use_tile(self, direction=None):
        """
        The function that sends a 'use-tile' message to the environment along with
        the direction of the place where the tile should be used.

        :param direction: None or str
            The direction where the tile should be used. Possible values are
            'North', 'South', 'East' and 'West'.
        :return: nothing
        """
        possible_directions = ["North", "West", "East", "South"]
        if direction is None or direction not in possible_directions:
            direction = np.random.choice(possible_directions)

        dest = "environment"

        msg = "use-tile %s" % direction
        send_msg = Message(
            self.color, dest, msg, Message.INFORM, "test-%s" % self.color)
        self.last_msg = deepcopy(send_msg)
        self.sent.put(send_msg)

    def receive_message(self):
        """
        The function that handles incoming messages. If the content of a
        message is 'failed', it will send the last known message again
        to the environment

        :return: nothing
        """
        try:
            while True:
                data = self.received.get(False)
                # print("This is: ", self.color)
                # print(data)
                if data.content == 'success' or self.timeout == 0:
                    break

                print(f'Will resend last message from {self.color} with content {self.last_msg.content}')
                self.sent.put(self.last_msg)
                self.timeout -= 1
                time.sleep(SLEEP_TIME)

            self.timeout = RESEND_TIMEOUT
        except:
            pass

    def closest_target(self, target):
        """
        Get the closest target ('tile' or 'hole') that is the same color as
        the agent to direct the agent towards it.

        :return: (np.array, list of tuples)
            A tuple consisting of the closest target (position wise) and a
            computed path towards it
        """
        positions = []
        if target == 'tile':
            positions = np.argwhere(self.tiles_col == self.color_index)
        elif target == 'hole':
            positions = np.argwhere(self.holes_col == self.color_index)

        min_dist = self.W * self.H
        goto_position = None
        goto_path = None
        for position in positions:
            path = astar(
                maze=self.obstacles+self.holes_depth,
                start=tuple(self.position),
                end=tuple(position)
            )

            crt_dist = len(path)
            if crt_dist < min_dist:
                min_dist = crt_dist
                goto_position = position
                goto_path = path

        if goto_position is None:
            raise ValueError("There are no more tiles to get!")

        # if we targeted a hole, we must stop before reaching it
        if target == 'hole':
            goto_path = goto_path[:-1]
            goto_position = goto_path[-1]

        return goto_position, goto_path


    def move_to_target(self, target, next_action):
        """
        Given a target ('tile' or 'hole') move towards it and afterwards set
        the next action.

        :param target: str
            The agent's target that can be either 'tile' either 'hole'
        :param next_action: str
            After managing to get to the target, what should be the agent's
            next action. Valid actions are 'move_to_tile', 'pick_up_tile',
            'move_to_hole', 'use_tile' or 'none' (in case of error)
        :return: nothing
        """
        path_to_closest_target = []
        try:
            closest_target, path_to_closest_target = self.closest_target(target)
        except ValueError as ve:
            self.crt_action = 'none'
            self.loop()

        for next_position in path_to_closest_target:
            goto_direction = None
            for next_move, direction in INVERTED_DIRECTIONS.items():
                if (self.position + np.array(next_move) == next_position).all():
                    goto_direction = direction

            self.send_message('move', goto_direction)
            self.receive_message()
            time.sleep(SLEEP_TIME)
            self.position = np.array(next_position)

        self.crt_action = next_action
        self.loop()

    def loop(self):
        """
        The base function of the agent.

        :return: nothing.
        """
        if self.crt_action == 'move_to_tile':
            print(f'{self.color} will move to tile')
            self.move_to_target(
                target='tile',
                next_action='pick_up_tile')

        elif self.crt_action == 'pick_up_tile':
            print(f'{self.color} will pick up tile')

            # send a 'pick' message to envirionment
            self.send_message('pick')

            self.receive_message()
            time.sleep(SLEEP_TIME)

            # decrement existing tiles
            self.tiles_no[self.position[0]][self.position[1]] -= 1

            # make sure that the next action will be to cover up a hole
            self.crt_action = 'move_to_hole'

            self.loop()

        elif self.crt_action == 'move_to_hole':
            print(f'{self.color} will move to hole')
            self.move_to_target(
                target='hole',
                next_action='use_tile')

        elif self.crt_action == 'use_tile':
            use_direction = None
            for next_move, direction in INVERTED_DIRECTIONS.items():
                possible_hole = self.position + np.array(next_move)
                if self.holes_depth[possible_hole[0]][possible_hole[1]] > 0:
                    use_direction = direction

            print(f'{self.color} will use tile with direction {use_direction}')

            # send a 'use_tile' message to environment
            self.send_message(msg_type='use_tile', direction=use_direction)

            self.receive_message()
            time.sleep(SLEEP_TIME)

            # decrement hole depth
            self.holes_depth[self.position[0]][self.position[1]] -= 1

            # make sure that the next action will be to get another tile
            self.crt_action = 'move_to_tile'

            self.loop()
