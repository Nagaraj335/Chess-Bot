"""
Lightweight Chess Engine with proper rule validation
Fallback implementation while the heavy Hugging Face model loads
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class LightweightChessEngine:
    def __init__(self):
        self.games = {}
        logger.info("🚀 Lightweight Chess Engine initialized!")
    
    def create_game(self, game_id, human_color='white', difficulty_elo=1400):
        """Create a new chess game with proper validation"""
        board = chess.Board()
        
        self.games[game_id] = {
            'board': board,
            'human_color': human_color,
            'difficulty_elo': difficulty_elo,
            'move_count': 0,
            'game_over': False,
            'result': None
        }
        
        logger.info(f"Created game {game_id}: Human={human_color}, Difficulty={difficulty_elo} ELO")
        return {
            'success': True,
            'board_fen': board.fen(),
            'legal_moves': [move.uci() for move in board.legal_moves],
            'game_over': False,
            'result': None
        }
    
    def make_move(self, game_id, move_uci):
        """Make a move with comprehensive validation"""
        if game_id not in self.games:
            return {'success': False, 'error': 'Game not found'}
        
        game = self.games[game_id]
        board = game['board']
        
        if game['game_over']:
            return {'success': False, 'error': 'Game is already over'}
        
        try:
            move = chess.Move.from_uci(move_uci)
            
            # Comprehensive move validation
            if move not in board.legal_moves:
                return {'success': False, 'error': 'Illegal move'}
            
            # Execute the move
            board.push(move)
            game['move_count'] += 1
            
            # Check game state
            result = self.check_game_result(board)
            game['game_over'] = result is not None
            game['result'] = result
            
            logger.info(f"Move made in game {game_id}: {move_uci}")
            
            return {
                'success': True,
                'board_fen': board.fen(),
                'legal_moves': [m.uci() for m in board.legal_moves],
                'game_over': game['game_over'],
                'result': game['result']
            }
            
        except Exception as e:
            logger.error(f"Error making move {move_uci}: {e}")
            return {'success': False, 'error': f'Invalid move: {str(e)}'}
    
    def get_ai_move(self, game_id):
        """Get AI move with ELO-based difficulty"""
        if game_id not in self.games:
            return {'success': False, 'error': 'Game not found'}
        
        game = self.games[game_id]
        board = game['board']
        
        if game['game_over']:
            return {'success': False, 'error': 'Game is already over'}
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return {'success': False, 'error': 'No legal moves available'}
        
        try:
            # Get move based on ELO rating
            ai_move = self.get_move_by_elo(board, legal_moves, game['difficulty_elo'])
            
            # Double-check move is legal (should always be true)
            if ai_move not in board.legal_moves:
                logger.warning(f"Generated illegal move {ai_move}, selecting random legal move")
                ai_move = random.choice(legal_moves)
            
            # Execute AI move
            board.push(ai_move)
            game['move_count'] += 1
            
            # Check game state
            result = self.check_game_result(board)
            game['game_over'] = result is not None
            game['result'] = result
            
            logger.info(f"AI move in game {game_id}: {ai_move.uci()} (ELO: {game['difficulty_elo']})")
            
            return {
                'success': True,
                'move': ai_move.uci(),
                'board_fen': board.fen(),
                'legal_moves': [m.uci() for m in board.legal_moves],
                'game_over': game['game_over'],
                'result': game['result']
            }
            
        except Exception as e:
            logger.error(f"Error getting AI move: {e}")
            return {'success': False, 'error': f'AI move failed: {str(e)}'}
    
    def get_move_by_elo(self, board, legal_moves, elo):
        """Get move based on ELO rating with proper chess strategy"""
        
        if elo >= 2500:
            return self.get_expert_move(board, legal_moves)
        elif elo >= 2000:
            return self.get_strong_move(board, legal_moves)
        elif elo >= 1500:
            return self.get_intermediate_move(board, legal_moves)
        elif elo >= 1000:
            return self.get_beginner_move(board, legal_moves)
        else:
            return self.get_random_move(legal_moves)
    
    def get_expert_move(self, board, legal_moves):
        """Expert level: Check for mate, tactical moves, strong positional play"""
        # 1. Check for checkmate in 1
        for move in legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return move
            board.pop()
        
        # 2. Check for checks that lead to material gain
        good_checks = []
        for move in legal_moves:
            if board.gives_check(move):
                board.push(move)
                # If opponent has limited responses, this could be good
                if len(list(board.legal_moves)) <= 3:
                    good_checks.append(move)
                board.pop()
        
        if good_checks:
            return random.choice(good_checks)
        
        # 3. Captures that win material
        winning_captures = []
        for move in legal_moves:
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    # Simple material evaluation
                    piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
                    captured_value = piece_values.get(captured_piece.symbol().lower(), 0)
                    moving_piece = board.piece_at(move.from_square)
                    moving_value = piece_values.get(moving_piece.symbol().lower(), 0)
                    
                    # If we're capturing a more valuable piece, it's likely good
                    if captured_value >= moving_value:
                        winning_captures.append(move)
        
        if winning_captures:
            return random.choice(winning_captures)
        
        # 4. Development moves (knights and bishops)
        development_moves = []
        for move in legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.symbol().lower() in ['n', 'b']:
                # Check if piece is moving from starting square
                if (piece.color == chess.WHITE and move.from_square in [1, 2, 5, 6, 57, 58, 61, 62]) or \
                   (piece.color == chess.BLACK and move.from_square in [1, 2, 5, 6, 57, 58, 61, 62]):
                    development_moves.append(move)
        
        if development_moves:
            return random.choice(development_moves)
        
        # 5. Central pawn moves
        central_moves = []
        for move in legal_moves:
            if move.to_square in [27, 28, 35, 36]:  # e4, d4, e5, d5 squares
                central_moves.append(move)
        
        if central_moves:
            return random.choice(central_moves)
        
        return random.choice(legal_moves)
    
    def get_strong_move(self, board, legal_moves):
        """Strong level: Good tactics, avoid blunders"""
        # Check for mate in 1
        for move in legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return move
            board.pop()
        
        # Prefer captures
        captures = [move for move in legal_moves if board.is_capture(move)]
        if captures:
            return random.choice(captures)
        
        # Prefer checks
        checks = [move for move in legal_moves if board.gives_check(move)]
        if checks:
            return random.choice(checks)
        
        # Avoid moves that put own king in check (this should not happen with legal moves)
        safe_moves = []
        for move in legal_moves:
            board.push(move)
            if not board.is_check():
                safe_moves.append(move)
            board.pop()
        
        if safe_moves:
            return random.choice(safe_moves)
        
        return random.choice(legal_moves)
    
    def get_intermediate_move(self, board, legal_moves):
        """Intermediate level: Basic tactics, some strategy"""
        # Look for captures
        captures = [move for move in legal_moves if board.is_capture(move)]
        if captures and random.random() < 0.7:
            return random.choice(captures)
        
        # Sometimes play checks
        checks = [move for move in legal_moves if board.gives_check(move)]
        if checks and random.random() < 0.3:
            return random.choice(checks)
        
        return random.choice(legal_moves)
    
    def get_beginner_move(self, board, legal_moves):
        """Beginner level: Mix of random and basic moves"""
        # 50% chance of random move
        if random.random() < 0.5:
            return random.choice(legal_moves)
        
        # 50% chance of slightly better move (captures if available)
        captures = [move for move in legal_moves if board.is_capture(move)]
        if captures:
            return random.choice(captures)
        
        return random.choice(legal_moves)
    
    def get_random_move(self, legal_moves):
        """Random move for lowest difficulty"""
        return random.choice(legal_moves)
    
    def check_game_result(self, board):
        """Check if the game is over and return result"""
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return "Black wins by checkmate"
            else:
                return "White wins by checkmate"
        elif board.is_stalemate():
            return "Draw by stalemate"
        elif board.is_insufficient_material():
            return "Draw by insufficient material"
        elif board.is_seventyfive_moves():
            return "Draw by 75-move rule"
        elif board.is_fivefold_repetition():
            return "Draw by repetition"
        return None
    
    def set_difficulty(self, game_id, difficulty_elo):
        """Set AI difficulty (ELO rating)"""
        if game_id not in self.games:
            return {'success': False, 'error': 'Game not found'}
        
        # Clamp ELO to reasonable range
        difficulty_elo = max(400, min(3000, difficulty_elo))
        self.games[game_id]['difficulty_elo'] = difficulty_elo
        
        logger.info(f"Set difficulty for game {game_id} to {difficulty_elo} ELO")
        
        return {
            'success': True,
            'difficulty_elo': difficulty_elo
        }

# Global engine instance
engine = LightweightChessEngine()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'engine': 'lightweight-rules-engine'})

@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Create a new chess game"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    human_color = data.get('human_color', 'white')
    difficulty_elo = data.get('rating', 1400)
    
    result = engine.create_game(game_id, human_color, difficulty_elo)
    return jsonify(result)

@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Make a human move"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    move_uci = data.get('move')
    
    if not move_uci:
        return jsonify({'success': False, 'error': 'Move is required'})
    
    result = engine.make_move(game_id, move_uci)
    return jsonify(result)

@app.route('/api/get_ai_move', methods=['POST'])
def get_ai_move():
    """Get AI move"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    
    result = engine.get_ai_move(game_id)
    return jsonify(result)

@app.route('/api/set_difficulty', methods=['POST'])
def set_difficulty():
    """Set AI difficulty"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    difficulty_elo = data.get('rating', 1400)
    
    result = engine.set_difficulty(game_id, difficulty_elo)
    return jsonify(result)

@app.route('/api/reset_game', methods=['POST'])
def reset_game():
    """Reset the current game"""
    data = request.get_json()
    game_id = data.get('game_id', 'default')
    
    if game_id in engine.games:
        game = engine.games[game_id]
        result = engine.create_game(game_id, game['human_color'], game['difficulty_elo'])
        return jsonify(result)
    else:
        result = engine.create_game(game_id)
        return jsonify(result)

@app.route('/')
def serve_chess_game():
    """Serve the chess game HTML file"""
    import os
    chess_html_path = os.path.join(os.path.dirname(__file__), '..', 'chess.html')
    try:
        with open(chess_html_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Chess game HTML file not found", 404

if __name__ == '__main__':
    print("🚀 Starting Lightweight Chess API Server...")
    print("📍 Backend running on: http://localhost:5001")
    print("🏥 Health check: http://localhost:5001/api/health")
    print("🎯 API endpoints available at /api/*")
    print("⚡ Fast, rule-compliant chess engine")
    print("🎮 Chess game available at: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
