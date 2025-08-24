#!/usr/bin/env python3
"""
Flask Backend API for React Chess Game
Provides chess logic, AI moves, and game state management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine
import random
import time
import threading
from typing import Optional, Dict, List

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

class ChessEngine:
    """Chess AI engine with adjustable difficulty"""
    
    def __init__(self, rating: int = 1500):
        self.rating = max(400, min(rating, 3000))
    
    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move using minimax with alpha-beta pruning"""
        if board.is_game_over():
            return None
        
        depth = self._get_depth_from_rating()
        _, best_move = self._minimax(board, depth, -float('inf'), float('inf'), True)
        
        # Add some randomness for lower ratings
        if self.rating < 2000 and random.random() < (2000 - self.rating) / 2000:
            legal_moves = list(board.legal_moves)
            return random.choice(legal_moves)
        
        return best_move
    
    def _get_depth_from_rating(self) -> int:
        """Convert rating to search depth"""
        if self.rating < 800:
            return 1
        elif self.rating < 1200:
            return 2
        elif self.rating < 1600:
            return 3
        elif self.rating < 2000:
            return 4
        elif self.rating < 2400:
            return 5
        else:
            return 6
    
    def _minimax(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool):
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0 or board.is_game_over():
            return self._evaluate_position(board), None
        
        best_move = None
        legal_moves = list(board.legal_moves)
        
        # Order moves for better pruning
        legal_moves.sort(key=lambda move: self._move_priority(board, move), reverse=True)
        
        if maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    def _evaluate_position(self, board: chess.Board) -> float:
        """Evaluate the current position"""
        if board.is_checkmate():
            return -1000 if board.turn else 1000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Piece values
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                score += value if piece.color == chess.WHITE else -value
        
        # Add positional bonuses
        score += self._positional_evaluation(board)
        
        return score
    
    def _positional_evaluation(self, board: chess.Board) -> float:
        """Basic positional evaluation"""
        score = 0
        
        # Center control
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        for square in center_squares:
            piece = board.piece_at(square)
            if piece:
                score += 0.3 if piece.color == chess.WHITE else -0.3
        
        # King safety (simplified)
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        
        if white_king_square:
            # Prefer castled king
            if white_king_square in [chess.G1, chess.C1]:
                score += 0.5
        
        if black_king_square:
            if black_king_square in [chess.G8, chess.C8]:
                score -= 0.5
        
        return score
    
    def _move_priority(self, board: chess.Board, move: chess.Move) -> int:
        """Assign priority to moves for better move ordering"""
        priority = 0
        
        # Captures
        if board.is_capture(move):
            priority += 10
        
        # Checks
        board.push(move)
        if board.is_check():
            priority += 5
        board.pop()
        
        # Central moves
        if move.to_square in [chess.E4, chess.E5, chess.D4, chess.D5]:
            priority += 2
        
        return priority

# Global game state
games: Dict[str, Dict] = {}
engines: Dict[str, ChessEngine] = {}

@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Start a new chess game"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    rating = data.get('rating', 1500)
    human_color = data.get('human_color', 'white')
    
    # Create new game
    board = chess.Board()
    games[game_id] = {
        'board': board,
        'human_color': human_color,
        'game_over': False,
        'result': None,
        'move_history': []
    }
    
    # Create AI engine
    engines[game_id] = ChessEngine(rating)
    
    return jsonify({
        'success': True,
        'game_id': game_id,
        'board_fen': board.fen(),
        'human_color': human_color,
        'legal_moves': [move.uci() for move in board.legal_moves],
        'game_over': False
    })

@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Make a human move"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    move_uci = data.get('move')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            board.push(move)
            game['move_history'].append(move_uci)
            
            # Check if game is over
            if board.is_game_over():
                game['game_over'] = True
                if board.is_checkmate():
                    winner = 'white' if board.turn == chess.BLACK else 'black'
                    game['result'] = f'{winner}_wins'
                else:
                    game['result'] = 'draw'
            
            return jsonify({
                'success': True,
                'board_fen': board.fen(),
                'legal_moves': [move.uci() for move in board.legal_moves],
                'game_over': game['game_over'],
                'result': game.get('result'),
                'last_move': move_uci
            })
        else:
            return jsonify({'error': 'Illegal move'}), 400
    
    except ValueError:
        return jsonify({'error': 'Invalid move format'}), 400

@app.route('/api/get_ai_move', methods=['POST'])
def get_ai_move():
    """Get AI move"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    
    if game_id not in games or game_id not in engines:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    engine = engines[game_id]
    
    if board.is_game_over():
        return jsonify({'error': 'Game is over'}), 400
    
    # Get AI move
    ai_move = engine.get_best_move(board)
    
    if ai_move:
        board.push(ai_move)
        game['move_history'].append(ai_move.uci())
        
        # Check if game is over
        if board.is_game_over():
            game['game_over'] = True
            if board.is_checkmate():
                winner = 'white' if board.turn == chess.BLACK else 'black'
                game['result'] = f'{winner}_wins'
            else:
                game['result'] = 'draw'
        
        return jsonify({
            'success': True,
            'ai_move': ai_move.uci(),
            'board_fen': board.fen(),
            'legal_moves': [move.uci() for move in board.legal_moves],
            'game_over': game['game_over'],
            'result': game.get('result')
        })
    
    return jsonify({'error': 'No legal moves available'}), 400

@app.route('/api/get_game_state', methods=['GET'])
def get_game_state():
    """Get current game state"""
    game_id = request.args.get('game_id', 'default')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    board = game['board']
    
    return jsonify({
        'board_fen': board.fen(),
        'legal_moves': [move.uci() for move in board.legal_moves],
        'game_over': game['game_over'],
        'result': game.get('result'),
        'human_color': game['human_color'],
        'move_history': game['move_history']
    })

@app.route('/api/set_difficulty', methods=['POST'])
def set_difficulty():
    """Change AI difficulty"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    rating = data.get('rating', 1500)
    
    if game_id not in engines:
        return jsonify({'error': 'Game not found'}), 404
    
    engines[game_id].rating = max(400, min(rating, 3000))
    
    return jsonify({
        'success': True,
        'new_rating': engines[game_id].rating
    })

@app.route('/api/reset_game', methods=['POST'])
def reset_game():
    """Reset the current game"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    
    if game_id in games:
        board = chess.Board()
        games[game_id] = {
            'board': board,
            'human_color': games[game_id]['human_color'],
            'game_over': False,
            'result': None,
            'move_history': []
        }
        
        return jsonify({
            'success': True,
            'board_fen': board.fen(),
            'legal_moves': [move.uci() for move in board.legal_moves],
            'game_over': False
        })
    
    return jsonify({'error': 'Game not found'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Chess API is running'})

if __name__ == '__main__':
    print("🚀 Starting Chess API Server...")
    print("📍 Backend running on: http://localhost:5000")
    print("🏥 Health check: http://localhost:5000/health")
    print("🎯 API endpoints available at /api/*")
    app.run(debug=True, host='0.0.0.0', port=5000)
