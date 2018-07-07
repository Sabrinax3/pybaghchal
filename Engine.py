from collections import namedtuple
from enum import Enum

from Point import Point
from Board import Board


class Engine(object):
    """
    Takes a board position and returns the best move
    """

    INF = 100000

    class MoveType(Enum):
        P = 1  # Place
        M = 2  # Move
        C = 3  # Capture

        def __repr__(self):
            if self.name == "P":
                return "Place"
            elif self.name == "M":
                return "Move"
            else:
                return "Capture"

        def __str__(self):
            return self.__repr__()

    # f = from, t = to, mt = MoveType
    Move = namedtuple('Move', ['f', 't', 'mt'])

    def __init__(self, position=None, depth=5):
        super(Engine, self).__init__()
        self.board = Board(position)
        self.depth = depth

    def _placements(self):
        return [
            Engine.Move(point.index, point.index, Engine.MoveType.P)
            for point in self.board.points
            if point.get_state() == Point.State.E
        ]

    def _movements(self):
        """
        Returns the possible movements (excluding captures)
        for the board and the turn
        """

        # since we don't have goat positions, we just loop to find the goats
        if self.board.turn == Board.Player.G:
            pieces = [p.index for p in self.board.points if p.get_state() == Point.State.G]
        else:
            pieces = self.board.tigerPos

        return [
            Engine.Move(p, p + d, Engine.MoveType.M)
            for p in pieces
            for d in Board.directions
            if self.board.is_movable(p, p + d)
        ]

    def _captures(self):
        return [
            Engine.Move(t, t + 2 * d, Engine.MoveType.C)
            for t in self.board.tigerPos
            for d in Board.directions
            if self.board.can_capture(t, t + 2 * d)
        ]

    def _movable(self, t_pos):
        """
        Returns whether a particular tiger is movable
        """

        return any(
            self.board.is_movable(t_pos, t_pos + d) or self.board.can_capture(t_pos, t_pos + 2 * d)
            for d in Board.directions
        )

    def _make_move(self, move):
        """
        Makes the given move on the board
        """

        # placement
        if move.mt == Engine.MoveType.P:
            self.board.points[move.t].set_state("G")
            self.board.turn = Board.Player.T
            self.board.goatsToBePlaced -= 1

        # movement
        elif move.mt == Engine.MoveType.M:
            if self.board.turn == Board.Player.G:
                self.board.points[move.t].set_state("G")
                self.board.points[move.f].set_state("E")
                self.board.turn = Board.Player.T
            else:
                self.board.points[move.t].set_state("T")
                self.board.points[move.f].set_state("E")
                self.board.turn = Board.Player.G
                self.board._set_tiger_positions()

        # capture
        elif move.mt == Engine.MoveType.C:
            self.board.points[move.f].set_state("E")
            self.board.points[(move.t + move.f) // 2].set_state("E")
            self.board.points[move.t].set_state("T")
            self.board.turn = Board.Player.G
            self.board.deadGoats += 1
            self.board._set_tiger_positions()

    def _revert_move(self, move):
        """
        Reverts the given move on the board
        """

        # placement
        if move.mt == Engine.MoveType.P:
            self.board.points[move.t].set_state("E")
            self.board.turn = Board.Player.G
            self.board.goatsToBePlaced += 1

        # movement
        elif move.mt == Engine.MoveType.M:
            if self.board.turn == Board.Player.G:
                self.board.points[move.f].set_state("T")
                self.board.points[move.t].set_state("E")
                self.board.turn = Board.Player.T
                self.board._set_tiger_positions()
            else:
                self.board.points[move.f].set_state("G")
                self.board.points[move.t].set_state("E")
                self.board.turn = Board.Player.G

        # capture
        elif move.mt == Engine.MoveType.C:
            self.board.points[move.f].set_state("T")
            self.board.points[(move.t + move.f) // 2].set_state("G")
            self.board.points[move.t].set_state("E")
            self.board.turn = Board.Player.T
            self.board.deadGoats -= 1
            self.board._set_tiger_positions()

    def movable_tigers(self):
        """
        Returns the number of movable tigers on the board
        """

        return sum(int(self._movable(t)) for t in self.board.tigerPos)

    def generate_move_list(self):
        """
        Generate a list of all moves for the board and turn
        """

        move_list = []

        # turn = Goat
        if self.board.turn == Board.Player.G:
            # placement phase
            if self.board.goatsToBePlaced > 0:
                move_list.extend(self._placements())
            # movement phase
            else:
                move_list.extend(self._movements())

        # turn = Tiger
        else:
            # moves
            move_list.extend(self._movements())
            # captures
            move_list.extend(self._captures())

        return move_list

    def evaluate(self, depth=0):
        """
        Returns a numeric evaluation of the position
        Written from the perspective of Tiger
        """
        if self.board.winner == Board.Player.G:
            return -Engine.INF
        elif self.board.winner == Board.Player.T:
            return Engine.INF

        return 30 * self.movable_tigers() + 50 * self.board.deadGoats - depth

    def minmax(self, depth=0, alpha=0, beta=0):
        score = self.evaluate(depth)

        # if a leaf node is reached, return the score
        if depth == self.depth or abs(score) == Engine.INF:
            return score

        # find the minimum attainable value for the Goat
        if self.board.turn == Board.Player.G:
            best_val = Engine.INF

            for move in self.generate_move_list():
                # first make the move
                self._make_move(move)
                # evaluate the resulting position
                value = self.minmax(depth + 1)

                # if value < beta:
                #     beta = value

                best_val = min(best_val, value)
                # then revert the move
                self._revert_move(move)

                return best_val

                # if alpha >= beta:
                #     return beta

        # find the maximum attainable value for the maximizer
        else:
            best_val = -Engine.INF

            for move in self.generate_move_list():
                # first make the move
                self._make_move(move)
                # evaluate the resulting position
                value = self.minmax(depth + 1)

                # if value < beta:
                #     beta = value

                best_val = max(best_val, value)
                # then revert the move
                self._revert_move(move)

            return best_val

        # return alpha if self.board.turn == Board.Player.G else beta

    def find_best_move(self):
        score = 0
        best_move = None

        for move in self.generate_move_list():
            # make the move
            self._make_move(move)

            # is it the best move we've found so far?
            if self.minmax() > score:
                best_move = move

            # revert the move
            self._revert_move(move)

        return best_move

    def make_random_move(self):
        import random
        move_list = self.generate_move_list()
        # pick a random move
        move = random.choice(move_list)
        # make the move
        self._make_move(move)
        return move

    def make_best_move(self):
        move = self.find_best_move()
        self._make_move(move)