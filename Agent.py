import time

from Message import *
from constants import *
from pathfind import astar


class Agent:

    def __init__(self, color, receive_queue, send_queue, H, W, holes_depth,
                 holes_col, tiles_no, tiles_col, obstacles, position,
                 color_index, agents):
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
        self.agents = agents
        self.steps = 0
        self.crt_action = 'move_to_tile'
        self.refuse = set()
        self.goto_path = []
        self.last_success = True

        self.cache_best = {
            'tile_path': [],
            'hole_path': []
        }
        self.timeout = RESEND_TIMEOUT
        self.msg_sent = 0
        self.last_negotiation_id = -1
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
        self.last_success = False
        if msg_type is not None:
            if msg_type == 'pick':
                self.pick(color=self.color)
            elif msg_type == 'move':
                self.move(direction=direction)
            elif msg_type == 'use_tile':
                self.use_tile(direction=direction)

        # If there's no msg_type, just random it
        # chance = np.random.rand()
        # if chance < 0.4:
        #     self.pick()
        # elif chance > 0.6:
        #     self.move()
        # else:
        #     self.use_tile()

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
            direction = np.random.choice(possible_directions)

        msg = "move %s" % direction

        dest = "environment"
        send_msg = Message(
            self.color, dest, msg, Message.REQUEST, "move-%s" % self.color)

        self.sent.put(send_msg)
        # TODO: increment steps after receiving message.content == 'success'
        self.refuse = set()
        self.steps += 1

    def pick(self, color):
        """
        The function that sends a 'pick' message to the environment.

        :return: nothing
        """
        dest = "environment"
        send_msg = Message(
            self.color, dest, "pick", Message.REQUEST, "pick-%s" % self.color)

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
            self.color, dest, msg, Message.REQUEST, "use-tile-%s" % self.color)

        self.sent.put(send_msg)

    def receive_message(self):
        """
        The function that handles incoming messages. If the content of a
        message is 'failed', it will send the last known message again
        to the environment

        :return: nothing
        """
        msg_queue = []
        try:
            while(True):
                data = self.received.get(False)
                msg_queue.append(data)
        except:
            pass

        for data in msg_queue:
            if data.sender == 'environment':
                if data.content == 'stop':
                    while True:
                        time.sleep(10000)
                if data.content == 'success':
                    self.last_success = True
                    self.position = self.goto_path[0]
                    del self.goto_path[0]
            elif data.conv_id == self.last_negotiation_id:
                if data.msg_type == Message.ACCEPT:
                    self.goto_path = self.cache_best['tile_path']
            elif data.msg_type == Message.REQUEST:
                msg = Message(self.color, data.sender, data.content, Message.ACCEPT, data.conv_id)
                print(msg)
                self.sent.put(msg)


    def closest_target(self, target, color, start_position=None):
        """
        Get the closest target ('tile' or 'hole') that is the same color as
        the agent to direct the agent towards it.

        :return: nothing
        """

        positions = []
        if target == 'tile':
            positions = np.argwhere(self.tiles_col == color)
        elif target == 'hole':
            positions = np.argwhere(self.holes_col == color)
        min_dist = self.W * self.H
        goto_position = None
        goto_path = None
        maze = self.obstacles + self.holes_depth
        for position in positions:
            if target == 'tile':
                if self.tiles_no[tuple(position)] == 0:
                    continue
            if target == 'hole':
                maze[tuple(position)] = 0

            if start_position is None:
                start_position = self.position

            path = astar(
                maze=maze,
                start=tuple(start_position),
                end=tuple(position)
            )

            if target == 'hole':
                maze[tuple(position)] = 1
            # we are already in start position (don't need to go there)
            path = path[1:]

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

        return goto_position, goto_path

    def send_agent_message(self, dest, content, msg_type):
        conv_id = self.color + '_' + str(self.msg_sent)
        self.last_negotiation_id = conv_id
        msg = Message(
            sender=self.color, dest=dest, content=content, msg_type=msg_type, conv_id=conv_id)
        # print(msg)
        self.sent.put(msg)

    def best_path(self):
        all_colors = set(self.tiles_col[self.tiles_col > -1]) - self.refuse
        min_dist = 1000
        min_color = -1
        for color in all_colors:
            goto_position_tile, goto_path_tile = self.closest_target('tile', color)
            goto_position_hole, goto_path_hole = self.closest_target('hole', color, goto_position_tile)

            l = np.sum([len(goto_path_tile), len(goto_path_hole)])
            if l < min_dist:
                min_dist = l
                min_color = color
                self.cache_best['tile_path'] = goto_path_tile
                self.cache_best['hole_path'] = goto_path_hole

        self.send_agent_message(dest=self.agents[min_color], content='move_tile-9', msg_type=Message.REQUEST)

    def move_to_target(self, target):
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
        try:
            if len(self.goto_path) == 0:
                self.best_path()
                # self.closest_target(target)
                if len(self.goto_path) == 0:
                    return

        except ValueError as ve:
            self.crt_action = 'none'
            self.loop()
        next_position = self.goto_path[0]

        goto_direction = None
        for next_move, direction in INVERTED_DIRECTIONS.items():
            if (self.position + np.array(next_move) == next_position).all():
                goto_direction = direction

        self.send_message('move', goto_direction)

        time.sleep(SLEEP_TIME)

        self.loop()

    def loop(self):
        """
        The base function of the agent.

        :return: nothing.
        """

        self.receive_message()
        if not self.last_success:
            time.sleep(SLEEP_TIME)
            self.loop()

        if self.crt_action == 'move_to_tile':
            self.move_to_target(
                target='tile')
            if len(self.goto_path) == 0:
                self.crt_action = 'pick_up_tile'

        elif self.crt_action == 'pick_up_tile':
            # send a 'pick' message to envirionment
            self.send_message('pick')

            # decrement existing tiles
            self.tiles_no[self.position[0]][self.position[1]] -= 1

            # make sure that the next action will be to cover up a hole
            self.crt_action = 'move_to_hole'

        elif self.crt_action == 'move_to_hole':
            self.move_to_target(
                target='hole',
            )
            if len(self.goto_path) == 0:
                self.crt_action = 'use_tile'

        elif self.crt_action == 'use_tile':
            use_direction = None
            for next_move, direction in INVERTED_DIRECTIONS.items():
                possible_hole = self.position + np.array(next_move)
                try:
                    if self.holes_depth[possible_hole[0]][possible_hole[1]] > 0:
                        use_direction = direction
                        break
                except:
                    pass

            # send a 'use_tile' message to environment
            self.send_message(msg_type='use_tile', direction=use_direction)

            # decrement hole depth
            self.holes_depth[possible_hole[0]][possible_hole[1]] -= 1

            # make sure that the next action will be to get another tile
            self.crt_action = 'move_to_tile'
        time.sleep(SLEEP_TIME)
        self.loop()
