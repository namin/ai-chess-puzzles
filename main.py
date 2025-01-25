import chess
import random
from typing import Optional, List, Dict, Tuple

class BaseBoardEvaluator:
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }

    def __init__(self, name: str):
        self.name = name

    @staticmethod
    def opponent(color) -> bool:
        return chess.BLACK if color == chess.WHITE else chess.WHITE

    def sum_pieces(self, board: chess.Board, color: bool, piece_weights: Optional[Dict] = None) -> int:
        weights = piece_weights or self.PIECE_VALUES
        return sum(
            weights[piece_type] * len(board.pieces(piece_type, color))
            for piece_type in weights
        )

    def evaluate(self, board: chess.Board, init_board: chess.Board, player: int) -> float:
        raise NotImplementedError

class MaterialBalanceEvaluator(BaseBoardEvaluator):
    def evaluate(self, board: chess.Board, init_board: chess.Board, player: int) -> float:
        if board.is_checkmate():
            return -player

        color = board.turn
        return player * (
            self.sum_pieces(board, color) - 
            self.sum_pieces(board, self.opponent(color))
        )

class MaterialDiffEvaluator(BaseBoardEvaluator):
    def evaluate(self, board: chess.Board, init_board: chess.Board, player: int) -> float:
        if board.is_checkmate():
            return -player

        color = board.turn
        return player * (
            (self.sum_pieces(board, color) - self.sum_pieces(init_board, color)) -
            (self.sum_pieces(board, self.opponent(color)) - self.sum_pieces(init_board, self.opponent(color)))
        )

class ChessStrategy:
    def __init__(self, name: str):
        self.name = name
        self.stats = {'wins': 0, 'total': 0}

    def get_move(self, board: chess.Board) -> str:
        raise NotImplementedError

    def update_stats(self, won: bool):
        self.stats['total'] += 1
        if won:
            self.stats['wins'] += 1

class MinMaxStrategy(ChessStrategy):
    def __init__(self, name: str = "minmax", depth: int = 3, evaluator: Optional[BaseBoardEvaluator] = None):
        super().__init__(name)
        self.depth = depth
        self.evaluator = evaluator or MaterialBalanceEvaluator("default")

    @staticmethod
    def apply_move(board: chess.Board, move: chess.Move) -> chess.Board:
        new_board = board.copy()
        new_board.push(move)
        return new_board

    def evaluate_move(self, move: chess.Move, player: int, board: chess.Board, init_board: chess.Board, depth: int) -> Tuple[float, chess.Move]:
        new_board = self.apply_move(board, move)
        score, _ = self.minmax(new_board, player=player, init_board=init_board, depth=depth)
        return score, move

    def minmax(self, board: chess.Board, player: int = 1, init_board: Optional[chess.Board] = None, depth: int = 0) -> Tuple[float, Optional[chess.Move]]:
        init_board = init_board or board
        if self.depth <= depth:
            return self.evaluator.evaluate(board, init_board, player), None

        moves = list(board.legal_moves)
        if not moves:
            return self.evaluator.evaluate(board, init_board, player), None

        evaluations = [
            self.evaluate_move(move, player, board, init_board, depth+1)
            for move in moves
        ]
        evaluations.sort(key=lambda x: x[0])
        return evaluations[0]

    def get_move(self, board: chess.Board) -> str:
        _, move = self.minmax(board)
        return move.uci() if move else None

class RandomStrategy(ChessStrategy):
    def __init__(self):
        super().__init__("random")
        
    def get_move(self, board: chess.Board) -> str:
        return random.choice(list(board.legal_moves)).uci()

class PuzzleExtractor:
    HEADERS = ['PuzzleId', 'FEN', 'Moves', 'Rating', 'RatingDeviation', 'Popularity', 'NbPlays', 'Themes', 'GameUrl', 'OpeningTags']
    
    def __init__(self):
        self.header_idx = dict([(self.HEADERS[i], i) for i in range(len(self.HEADERS))])

    def extract_puzzle(self, line: str) -> Tuple[chess.Board, List[str]]:
        xs = line.split(',')
        fen = xs[self.header_idx['FEN']]
        board = chess.Board(fen)
        solution_moves = xs[self.header_idx['Moves']].split(' ')
        return board, solution_moves

class StrategyEvaluator:
    def __init__(self, puzzle_file: str):
        self.puzzle_file = puzzle_file
        self.strategies: List[ChessStrategy] = []
        self.extractor = PuzzleExtractor()

    def add_strategy(self, strategy: ChessStrategy):
        self.strategies.append(strategy)

    def print_stats(self):
        stats_strs = []
        for strategy in self.strategies:
            stats = strategy.stats
            if stats['total'] > 0:
                win_rate = (stats['wins'] / stats['total']) * 100
                stats_strs.append(f"{strategy.name}: {stats['wins']}/{stats['total']} ({win_rate:.1f}%)")
        print(" | ".join(stats_strs))

    def evaluate_puzzle(self, board: chess.Board, expected: str) -> bool:
        some_success = False
        for strategy in self.strategies:
            actual = strategy.get_move(board)
            if actual == expected:
                some_success = True
            strategy.update_stats(actual == expected)
        return some_success

    def evaluate_all(self):
        with open(self.puzzle_file) as f:
            next(f)
            for line in f:
                board, solution_moves = self.extractor.extract_puzzle(line.strip())
                if self.evaluate_puzzle(board, solution_moves[0]):
                    self.print_stats()
        self.print_stats()  # Final stats

import argparse
import os

# Set base directory
DB_DIR = "db"
DB_PREFIX = "lichess_db_puzzle"

def check_db_exists(db_file):
    """Check if the dataset file exists, otherwise suggest downloading."""
    if not os.path.exists(db_file):
        print(f"Error: The dataset file '{db_file}' is missing.")
        print("Please run `./download_db.sh` to download the required dataset.")
        exit(1)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Process Lichess puzzle dataset.")
    parser.add_argument(
        "-n", "--num", type=int, choices=[50, 500], 
        help="Specify the number of puzzles to use (50 or 500). Defaults to full dataset."
    )
    return parser.parse_args()

def main():
    """Main function to determine dataset and process it."""
    args = parse_arguments()

    # Determine dataset file
    db_file = DB_PREFIX
    if args.num == 50 or args.num == 500:
        db_file += "_" + str(args.num)
    db_file += ".csv"
    db_file = os.path.join(DB_DIR, db_file)

    # Check if the database file exists
    check_db_exists(db_file)

    # Set random seed for consistency
    random.seed(42)

    evaluator = StrategyEvaluator(db_file)
    
    evaluator.add_strategy(RandomStrategy())
    evaluator.add_strategy(MinMaxStrategy("minmax_balance", evaluator=MaterialBalanceEvaluator("balance")))
    evaluator.add_strategy(MinMaxStrategy("minmax_diff", evaluator=MaterialDiffEvaluator("diff")))
    
    evaluator.evaluate_all()

if __name__ == '__main__':
    main()
