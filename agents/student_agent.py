"""Student agent: edit ONLY this file."""
from agents.agent import Agent
from store import register_agent
from helpers import (Move, get_valid_moves, execute_move, check_winner,
                     check_endgame, random_move, copy_state, top_view)
from constants import *
import numpy as np
import time

@register_agent("student_agent")          # do not change this string

class StudentAgent(Agent):
    def __init__(self):
        """Set up your agent. This runs once per game, before the first move, and must finish
        within INIT_TIME_LIMIT seconds."""
        super().__init__()
        self.name = "StudentAgent"
    def important_lines(self, board):
        owners, sizes = top_view(board)
        lines = []
        for r in range(BOARD_SIZE):
            lines.append([(r, c,owners[r][c], sizes[r][c]) for c in range(BOARD_SIZE)])
        for c in range(BOARD_SIZE):
            lines.append([(r, c,owners[r][c], sizes[r][c])for r in range(BOARD_SIZE)])
        lines.append([(i, i,owners[i][i], sizes[i][i]) for i in range(BOARD_SIZE)])
        lines.append([(i, BOARD_SIZE-1-i,owners[i][BOARD_SIZE-1-i], sizes[i][BOARD_SIZE-1-i]) for i in range(BOARD_SIZE)])
        
    def available_pieces(self, board, reserves, player, line):
        owners, sizes = top_view(board)
        available = []
        #pieces in reserves
        for size in range(NUM_SIZES):
            for _ in range(int(reserves[player, size])):
                available.append(size)
        moves = get_valid_moves(board, reserves, player)
        #pieces on the board that we can move without losing
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if owners[r][c] == player:
                    # not counting pieces of our current line
                    if (r, c, owners[r][c], sizes[r][c]) in line:
                        continue
                    # not making a piece move that its moving causes a loss
                    for move in moves:
                        if move.src == (r,c):
                            test_board, test_reserves= copy_state(board, reserves)
                            execute_move(test_board, test_reserves, player, move)
                            if check_winner(test_board, player) != 3 - player:
                                available.append(sizes[r][c])
        return available
    def can_fork(self, board, reserves, player):
        moves = get_valid_moves(board, reserves, player)
        for move in moves:
            test_board, test_reserves = copy_state(board, reserves)
            execute_move(test_board, test_reserves, player, move)
            winner = check_winner(test_board, player)
            if winner!=0:
                continue
            next_moves = get_valid_moves(test_board, test_reserves, player)
            winning_moves = []
            for next_move in next_moves:
                next_board, next_reserves = copy_state(test_board, test_reserves)
                execute_move(next_board, next_reserves, next_moves)
                if check_winner(next_board, player) == player:
                    if (next_moves.src, next_moves.dest, next_moves.size) not in winning_moves:
                        winning_moves.append((next_moves.src, next_moves.dest, next_moves.size))
            if len(winning_moves) >= 2:
                return True
        return False
    def can_cover(self, board, reserves, player, row, col, opp_size):
        owners, sizes = top_view(board)
        # check if we can cover the piece by our reserves
        for size in range(opp_size + 1, NUM_SIZES):
            if reserves[player, size] > 0:
                return True
        # check if we can cover the piece by one of the pieces of the board without defeating the game
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if r == row and c == col:
                    continue
                if owners[r][c] == player and sizes[r][c] > opp_size:
                    return True
        return False
    def evaluate(self, board, reserves, player):

        dist_w = {1: 1000, 2:200, 3:30, 4:0}
        size_w = {SMALL: 1, MEDIUM: 2, LARGE:4}
        score_us = 0
        score_ops = 0

        opp = 3 - player
        dist_from_winning = WIN_LENGTH
        winner = check_winner(board)
        if winner == player:
            return float('+inf')
        if winner == opp:
            return float('-inf')
        

        lines = self.important_lines(board)
        for line in lines:
            for current_player in (player, opp):
                strength = 0
                reqs = []
                #calculate current strength and missing piece we need
                for r, c, owner, size in line:
                    if owner == current_player:
                        strength += size_w[size]
                    elif owner == OBSTACLE:
                        reqs = None
                        break
                    elif owner == EMPTY:
                        reqs.append(SMALL)
                    else:
                        # need bigger size ot fill the place if not possible then not a good state
                        need_size = size + 1
                        if need_size >= NUM_SIZES:
                            reqs = None
                            break
                        reqs.append(need_size)
                #line cannot get compeleted
                if reqs is None:
                    continue
                missing = len(reqs)
                if missing == 0:
                    continue
                if missing >= WIN_LENGTH:
                    continue
                # getting pieces that we can move either from reserves or from the board
                available = self.available_pieces(board, reserves, player, line)
                #matching larger reqs with larger available pieces
                reqs.sort(reserves = True)
                available.sort(reverse=True)
                matched = 0
                for required in reqs:
                    for i in range(len(available)):
                        if available[i] >= required:
                            matched +=1
                            available.pop(i)
                            break
                ratio = matched/missing
                score = dist_w[missing] * strength * ratio
                if current_player == player:
                    score_us += score
                else:
                    score_ops+=score
        fork_score = 1000
        if self.can_fork(board, reserves, player):
            score_us+=fork_score
        if self.can_fork(board, reserves, opp):
            score_ops+=fork_score
        return score_us - score_ops
        # diagonals and horizontals and verticals to check how much away we are from winning
        
            
    def search_evaluate(self, board, reserves, player):
        """Temporary lightweight evaluation for testing the search."""
        owners, sizes = top_view(board)
        opponent = 3 - player
        score = 0

        weights = [0, 1, 10, 100, 10000]

        # Evaluate all possible winning lines
        lines = []

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    cells = [
                        (r + i * dr, c + i * dc)
                        for i in range(WIN_LENGTH)
                    ]

                    if all(0 <= rr < BOARD_SIZE and
                           0 <= cc < BOARD_SIZE
                           for rr, cc in cells):
                        lines.append(cells)

        for line in lines:
            values = [owners[r, c] for r, c in line]

            if OBSTACLE in values:
                continue

            ours = values.count(player)
            theirs = values.count(opponent)

            if theirs == 0:
                score += weights[ours]

            if ours == 0:
                score -= weights[theirs]

        return score

    def alpha_beta(self, board, reserves, depth,
                   alpha, beta, current_player,
                   root_player, deadline, distance):

        if time.perf_counter() >= deadline:
            raise TimeoutError

        # Check terminal positions using the previous mover
        winner = check_winner(board, 3 - current_player)

        if winner == root_player:
            return 1000000 - distance

        if winner == 3 - root_player:
            return -1000000 + distance

        moves = get_valid_moves(
            board, reserves, current_player
        )

        # Handle positions with no legal moves
        if not moves:
            if ALLOW_MOVES:
                if current_player == root_player:
                    return -1000000 + distance
                return 1000000 - distance

            # Placement-only variant: draw or forced pass
            if not get_valid_moves(
                board, reserves, 3 - current_player
            ):
                return 0

            if depth == 0:
                return self.search_evaluate(
                    board, reserves, root_player
                )

            return self.alpha_beta(
                board, reserves, depth - 1,
                alpha, beta, 3 - current_player,
                root_player, deadline, distance + 1
            )

        # Evaluate nonterminal positions at the depth limit
        if depth == 0:
            return self.search_evaluate(
                board, reserves, root_player
            )

        # MAX node: our turn
        if current_player == root_player:
            best = float("-inf")

            for move in moves:
                if time.perf_counter() >= deadline:
                    raise TimeoutError

                b, r = copy_state(board, reserves)
                execute_move(b, r, current_player, move)

                value = self.alpha_beta(
                    b, r, depth - 1,
                    alpha, beta, 3 - current_player,
                    root_player, deadline, distance + 1
                )

                best = max(best, value)
                alpha = max(alpha, best)

                if alpha >= beta:
                    break

            return best

        # MIN node: opponent's turn
        else:
            best = float("inf")

            for move in moves:
                if time.perf_counter() >= deadline:
                    raise TimeoutError

                b, r = copy_state(board, reserves)
                execute_move(b, r, current_player, move)

                value = self.alpha_beta(
                    b, r, depth - 1,
                    alpha, beta, 3 - current_player,
                    root_player, deadline, distance + 1
                )

                best = min(best, value)
                beta = min(beta, best)

                if alpha >= beta:
                    break

            return best


    def search_root(self, board, reserves, player,
                    depth, deadline, preferred_move):

        moves = get_valid_moves(board, reserves, player)

        # Search the previous iteration's best move first
        if preferred_move in moves:
            moves.remove(preferred_move)
            moves.insert(0, preferred_move)

        best_move = moves[0]
        best_score = float("-inf")

        alpha = float("-inf")
        beta = float("inf")

        for move in moves:
            if time.perf_counter() >= deadline:
                raise TimeoutError

            b, r = copy_state(board, reserves)
            execute_move(b, r, player, move)

            score = self.alpha_beta(
                b, r, depth - 1,
                alpha, beta, 3 - player,
                player, deadline, 1
            )

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

        return best_move, best_score

    def step(self, board, reserves, player, opponent):
        """Choose a move using iterative deepening alpha-beta."""

        start = time.perf_counter()
        deadline = start + STEP_TIME_LIMIT - 0.25

        moves = get_valid_moves(board, reserves, player)

        if not moves:
            return None

        # Always keep a legal fallback move
        best_move = moves[0]
        depth = 1

        while time.perf_counter() < deadline:
            try:
                candidate, score = self.search_root(
                    board, reserves, player,
                    depth, deadline, best_move
                )

                # Update only after a completed search
                best_move = candidate

                # Stop early if a forced win was found
                if score >= 900000:
                    break

                depth += 1

            except TimeoutError:
                break

        return best_move
