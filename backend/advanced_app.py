"""
Advanced Chess Engine using Hugging Face chess-llama model
Fixes all chess rule violations and implements proper ELO-based difficulty
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import random
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class ChessLlamaEngine:
    def __init__(self):
        self.model_name = "lazy-guy12/chess-llama"
        self.tokenizer = None
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Load the chess-llama model from Hugging Face"""
        try:
            logger.info("Loading chess-llama model from Hugging Face...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map="auto" if torch.cuda.is_available() else "cpu"
            )
            logger.info("Chess-llama model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.tokenizer = None
    
    def get_move(self, board, difficulty_elo=1400):
        """Get move from chess-llama model with ELO-based difficulty adjustment"""
        if not self.model or not self.tokenizer:
            logger.warning("Model not loaded, using fallback")
            return self.get_fallback_move(board, difficulty_elo)
        
        try:
            # Convert board to game notation for the model
            game_moves = []
            temp_board = chess.Board()
            
            # Replay moves to get the current position
            for move in board.move_stack:
                game_moves.append(temp_board.san(move))
                temp_board.push(move)
            
            # Create input for the model
            game_str = " ".join(game_moves)
            if game_str:
                input_text = f"[RESULT] {game_str}"
            else:
                input_text = "[RESULT]"
            
            # Tokenize and generate
            inputs = self.tokenizer.encode(input_text, return_tensors="pt")
            
            # Adjust temperature based on ELO (higher ELO = lower temperature = better play)
            # ELO 400 -> temp 1.5 (very random)
            # ELO 1400 -> temp 0.3 (model's natural strength)  
            # ELO 3000 -> temp 0.1 (very focused)
            temperature = max(0.1, 1.6 - (difficulty_elo / 1000.0))
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=10,
                    temperature=temperature,
                    do_sample=True,
                    top_k=50,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the output
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the next move
            new_moves = generated_text[len(input_text):].strip()
            
            # Parse the move
            if new_moves:
                # Try to extract a valid move from the generated text
                move_pattern = r'\b[a-h][1-8][a-h][1-8][qrnb]?\b'
                matches = re.findall(move_pattern, new_moves.lower())
                
                for move_str in matches:
                    try:
                        move = chess.Move.from_uci(move_str)
                        if move in board.legal_moves:
                            return move
                    except:
                        continue
            
            # Fallback if no valid move found
            return self.get_fallback_move(board, difficulty_elo)
            
        except Exception as e:
            logger.error(f"Error generating move: {e}")
            return self.get_fallback_move(board, difficulty_elo)
    
    def get_fallback_move(self, board, difficulty_elo):
        """Fallback move selection with ELO-based difficulty"""
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            return None
        
        # ELO-based move selection
        if difficulty_elo >= 2500:
            # Expert level: prioritize captures, checks, and tactical moves
            return self.get_tactical_move(board, legal_moves)
        elif difficulty_elo >= 1800:
            # Advanced level: good moves with some tactics
            return self.get_good_move(board, legal_moves)
        elif difficulty_elo >= 1200:
            # Intermediate level: decent moves, avoid blunders
            return self.get_decent_move(board, legal_moves)
        else:
            # Beginner level: mix of random and basic moves
            if random.random() < 0.3:
                return random.choice(legal_moves)
            return self.get_basic_move(board, legal_moves)
    
    def get_tactical_move(self, board, legal_moves):
        """Get tactical move for high ELO"""
        # Prioritize: checkmate, checks, captures, promotions
        for move in legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return move
            board.pop()
        
        # Check for checks
        checking_moves = [move for move in legal_moves if board.gives_check(move)]
        if checking_moves:
            return random.choice(checking_moves)
        
        # Captures
        captures = [move for move in legal_moves if board.is_capture(move)]
        if captures:
            return random.choice(captures)
        
        return random.choice(legal_moves)
    
    def get_good_move(self, board, legal_moves):
        """Get good move for medium-high ELO"""
        # Avoid moves that lead to check for own king
        safe_moves = []
        for move in legal_moves:
            board.push(move)
            if not board.is_check():
                safe_moves.append(move)
            board.pop()
        
        if safe_moves:
            # Prefer captures and checks among safe moves
            captures = [move for move in safe_moves if board.is_capture(move)]
            if captures:
                return random.choice(captures)
            
            checking_moves = [move for move in safe_moves if board.gives_check(move)]
            if checking_moves:
                return random.choice(checking_moves)
            
            return random.choice(safe_moves)
        
        return random.choice(legal_moves)
    
    def get_decent_move(self, board, legal_moves):
        """Get decent move for medium ELO"""
        # Basic move selection avoiding obvious blunders
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # Avoid moves that immediately lose material
        good_moves = []
        for move in legal_moves:
            board.push(move)
            # Simple check: if opponent can capture our piece, it might be bad
            opponent_captures = [m for m in board.legal_moves if board.is_capture(m)]
            if len(opponent_captures) <= 2:  # Allow some risk
                good_moves.append(move)
            board.pop()
        
        if good_moves:
            return random.choice(good_moves)
        return random.choice(legal_moves)
    
    def get_basic_move(self, board, legal_moves):
        """Get basic move for low ELO"""
        # Very simple move selection
        return random.choice(legal_moves)

class AdvancedChessEngine:
    def __init__(self):
        self.games = {}
        self.llama_engine = ChessLlamaEngine()
        logger.info("🚀 Advanced Chess Engine initialized with chess-llama!")
    
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
        """Get AI move using chess-llama with proper difficulty scaling"""
        if game_id not in self.games:
            return {'success': False, 'error': 'Game not found'}
        
        game = self.games[game_id]
        board = game['board']
        
        if game['game_over']:
            return {'success': False, 'error': 'Game is already over'}
        
        if not list(board.legal_moves):
            return {'success': False, 'error': 'No legal moves available'}
        
        try:
            # Get move from chess-llama
            ai_move = self.llama_engine.get_move(board, game['difficulty_elo'])
            
            if ai_move is None:
                return {'success': False, 'error': 'AI could not generate a move'}
            
            # Validate AI move (double-check)
            if ai_move not in board.legal_moves:
                logger.warning(f"AI generated illegal move {ai_move}, selecting random legal move")
                ai_move = random.choice(list(board.legal_moves))
            
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
engine = AdvancedChessEngine()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'engine': 'chess-llama'})

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

if __name__ == '__main__':
    print("🚀 Starting Advanced Chess API Server with chess-llama...")
    print("📍 Backend running on: http://localhost:5000")
    print("🏥 Health check: http://localhost:5000/api/health")
    print("🎯 API endpoints available at /api/*")
    print("🧠 Using Hugging Face chess-llama model for intelligent play")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
