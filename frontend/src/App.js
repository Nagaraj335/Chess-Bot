import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import './index.css';

const PIECE_SYMBOLS = {
  'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
  'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'
};

const API_BASE = 'http://localhost:5000/api';

function App() {
  const [gameState, setGameState] = useState({
    board: Array(64).fill(null),
    selectedSquare: null,
    legalMoves: [],
    gameOver: false,
    result: null,
    humanColor: 'white',
    currentTurn: 'white',
    isCheck: false,
    isCheckmate: false,
    moveHistory: []
  });
  
  const [aiState, setAiState] = useState({
    thinking: false,
    rating: 1500
  });
  
  const [animatingMove, setAnimatingMove] = useState(null);
  const [gameId] = useState('react-game');

  // Convert FEN to board array
  const fenToBoard = useCallback((fen) => {
    const [position] = fen.split(' ');
    const board = Array(64).fill(null);
    let square = 0;
    
    for (const char of position) {
      if (char === '/') continue;
      if (char >= '1' && char <= '8') {
        square += parseInt(char);
      } else {
        board[square] = char;
        square++;
      }
    }
    
    return board;
  }, []);

  // Convert square notation to index
  const squareToIndex = useCallback((square) => {
    const file = square.charCodeAt(0) - 97; // a-h to 0-7
    const rank = parseInt(square[1]) - 1;    // 1-8 to 0-7
    return (7 - rank) * 8 + file;
  }, []);

  // Convert index to square notation
  const indexToSquare = useCallback((index) => {
    const file = String.fromCharCode(97 + (index % 8));
    const rank = 8 - Math.floor(index / 8);
    return file + rank;
  }, []);

  // Initialize game
  useEffect(() => {
    const initGame = async () => {
      try {
        const response = await axios.post(`${API_BASE}/new_game`, {
          game_id: gameId,
          rating: aiState.rating,
          human_color: gameState.humanColor
        });
        
        if (response.data.success) {
          setGameState(prev => ({
            ...prev,
            board: fenToBoard(response.data.board_fen),
            legalMoves: response.data.legal_moves,
            gameOver: response.data.game_over,
            currentTurn: 'white'
          }));
        }
      } catch (error) {
        console.error('Failed to initialize game:', error);
      }
    };

    initGame();
  }, [gameId, aiState.rating, gameState.humanColor, fenToBoard]);

  // Make human move
  const makeMove = async (fromSquare, toSquare) => {
    const moveUci = fromSquare + toSquare;
    
    try {
      // Start animation
      setAnimatingMove({
        from: squareToIndex(fromSquare),
        to: squareToIndex(toSquare),
        piece: gameState.board[squareToIndex(fromSquare)]
      });

      const response = await axios.post(`${API_BASE}/make_move`, {
        game_id: gameId,
        move: moveUci
      });

      if (response.data.success) {
        // Wait for animation to complete
        setTimeout(() => {
          setGameState(prev => ({
            ...prev,
            board: fenToBoard(response.data.board_fen),
            legalMoves: response.data.legal_moves,
            gameOver: response.data.game_over,
            result: response.data.result,
            selectedSquare: null,
            currentTurn: prev.currentTurn === 'white' ? 'black' : 'white'
          }));
          setAnimatingMove(null);

          // Get AI move if game is not over
          if (!response.data.game_over && gameState.humanColor !== 'black') {
            getAiMove();
          }
        }, 700); // Match CSS transition duration
      }
    } catch (error) {
      console.error('Failed to make move:', error);
      setAnimatingMove(null);
    }
  };

  // Get AI move
  const getAiMove = async () => {
    setAiState(prev => ({ ...prev, thinking: true }));
    
    try {
      const response = await axios.post(`${API_BASE}/get_ai_move`, {
        game_id: gameId
      });

      if (response.data.success) {
        const aiMove = response.data.ai_move;
        const fromSquare = aiMove.substring(0, 2);
        const toSquare = aiMove.substring(2, 4);

        // Start AI move animation
        setAnimatingMove({
          from: squareToIndex(fromSquare),
          to: squareToIndex(toSquare),
          piece: gameState.board[squareToIndex(fromSquare)]
        });

        // Wait for animation
        setTimeout(() => {
          setGameState(prev => ({
            ...prev,
            board: fenToBoard(response.data.board_fen),
            legalMoves: response.data.legal_moves,
            gameOver: response.data.game_over,
            result: response.data.result,
            currentTurn: prev.currentTurn === 'white' ? 'black' : 'white'
          }));
          setAnimatingMove(null);
          setAiState(prev => ({ ...prev, thinking: false }));
        }, 700);
      }
    } catch (error) {
      console.error('Failed to get AI move:', error);
      setAiState(prev => ({ ...prev, thinking: false }));
    }
  };

  // Handle square click
  const handleSquareClick = (index) => {
    if (animatingMove || aiState.thinking || gameState.gameOver) return;

    const square = indexToSquare(index);
    
    if (gameState.selectedSquare === null) {
      // Select piece
      if (gameState.board[index]) {
        const piece = gameState.board[index];
        const isWhitePiece = piece === piece.toUpperCase();
        const canMove = (gameState.humanColor === 'white' && isWhitePiece) ||
                       (gameState.humanColor === 'black' && !isWhitePiece);
        
        if (canMove && gameState.currentTurn === gameState.humanColor) {
          setGameState(prev => ({ ...prev, selectedSquare: index }));
        }
      }
    } else {
      // Move piece
      const fromSquare = indexToSquare(gameState.selectedSquare);
      const moveUci = fromSquare + square;
      
      if (gameState.legalMoves.includes(moveUci)) {
        makeMove(fromSquare, square);
      } else {
        setGameState(prev => ({ ...prev, selectedSquare: null }));
      }
    }
  };

  // Reset game
  const resetGame = async () => {
    try {
      const response = await axios.post(`${API_BASE}/reset_game`, {
        game_id: gameId
      });

      if (response.data.success) {
        setGameState(prev => ({
          ...prev,
          board: fenToBoard(response.data.board_fen),
          legalMoves: response.data.legal_moves,
          gameOver: false,
          result: null,
          selectedSquare: null,
          currentTurn: 'white'
        }));
        setAnimatingMove(null);
        setAiState(prev => ({ ...prev, thinking: false }));
      }
    } catch (error) {
      console.error('Failed to reset game:', error);
    }
  };

  // Change difficulty
  const changeDifficulty = async (newRating) => {
    try {
      await axios.post(`${API_BASE}/set_difficulty`, {
        game_id: gameId,
        rating: newRating
      });
      setAiState(prev => ({ ...prev, rating: newRating }));
    } catch (error) {
      console.error('Failed to change difficulty:', error);
    }
  };

  // Get legal moves for selected piece
  const getLegalMovesForSquare = (squareIndex) => {
    if (gameState.selectedSquare !== squareIndex) return [];
    
    const fromSquare = indexToSquare(squareIndex);
    return gameState.legalMoves
      .filter(move => move.startsWith(fromSquare))
      .map(move => squareToIndex(move.substring(2, 4)));
  };

  // Check if square is a legal move destination
  const isLegalMoveDestination = (squareIndex) => {
    if (gameState.selectedSquare === null) return false;
    return getLegalMovesForSquare(gameState.selectedSquare).includes(squareIndex);
  };

  // Render square
  const renderSquare = (index) => {
    const isLight = (Math.floor(index / 8) + index % 8) % 2 === 0;
    const isSelected = gameState.selectedSquare === index;
    const isLegalMove = isLegalMoveDestination(index);
    const piece = gameState.board[index];
    const isAnimatingFrom = animatingMove && animatingMove.from === index;
    
    return (
      <div
        key={index}
        className={`square ${isLight ? 'light' : 'dark'} ${isSelected ? 'selected' : ''} ${isLegalMove ? 'legal-move' : ''}`}
        onClick={() => handleSquareClick(index)}
      >
        {piece && !isAnimatingFrom && (
          <div className="piece">
            {PIECE_SYMBOLS[piece]}
          </div>
        )}
      </div>
    );
  };

  // Render animated piece
  const renderAnimatedPiece = () => {
    if (!animatingMove) return null;

    const fromRow = Math.floor(animatingMove.from / 8);
    const fromCol = animatingMove.from % 8;
    const toRow = Math.floor(animatingMove.to / 8);
    const toCol = animatingMove.to % 8;

    return (
      <motion.div
        className="animated-piece"
        initial={{
          left: `${fromCol * 60 + 30}px`,
          top: `${fromRow * 60 + 30}px`,
        }}
        animate={{
          left: `${toCol * 60 + 30}px`,
          top: `${toRow * 60 + 30}px`,
        }}
        transition={{
          duration: 0.7,
          ease: [0.25, 0.46, 0.45, 0.94]
        }}
      >
        {PIECE_SYMBOLS[animatingMove.piece]}
      </motion.div>
    );
  };

  return (
    <div className="app">
      <div className="game-container">
        <h1 className="game-title">Smooth Chess</h1>
        
        <div className="chessboard">
          {Array(64).fill(null).map((_, index) => renderSquare(index))}
          <AnimatePresence>
            {renderAnimatedPiece()}
          </AnimatePresence>
        </div>

        <div className="game-status">
          {aiState.thinking && <span className="thinking">AI is thinking...</span>}
          {gameState.gameOver && (
            <div className="checkmate">
              Game Over: {gameState.result === 'white_wins' ? 'White Wins!' : 
                         gameState.result === 'black_wins' ? 'Black Wins!' : 'Draw!'}
            </div>
          )}
          {!gameState.gameOver && !aiState.thinking && (
            <div>Turn: {gameState.currentTurn === 'white' ? 'White' : 'Black'}</div>
          )}
        </div>
      </div>

      <div className="controls">
        <div className="control-group">
          <div className="control-label">Game Controls</div>
          <button className="button" onClick={resetGame}>
            New Game
          </button>
        </div>

        <div className="control-group">
          <div className="control-label">AI Difficulty</div>
          <div className="rating-control">
            <button 
              className="rating-button"
              onClick={() => changeDifficulty(Math.max(400, aiState.rating - 200))}
              disabled={aiState.rating <= 400}
            >
              -
            </button>
            <div className="rating-display">{aiState.rating}</div>
            <button 
              className="rating-button"
              onClick={() => changeDifficulty(Math.min(3000, aiState.rating + 200))}
              disabled={aiState.rating >= 3000}
            >
              +
            </button>
          </div>
        </div>

        <div className="status-display">
          <div><strong>You:</strong> {gameState.humanColor}</div>
          <div><strong>AI:</strong> {gameState.humanColor === 'white' ? 'black' : 'white'}</div>
          <div><strong>Rating:</strong> {aiState.rating}</div>
        </div>

        <div className="control-group">
          <div className="control-label">Animation</div>
          <div style={{fontSize: '0.9rem', opacity: 0.8}}>
            ✨ Smooth 700ms CSS transitions<br/>
            🎯 Framer Motion powered<br/>
            🚀 Zero jitter guarantee
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
