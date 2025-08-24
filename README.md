# ♟️ Vexora's Bot - Professional Chess Engine

A sophisticated web-based chess game featuring an intelligent AI opponent with adjustable difficulty levels.

## 🚀 Features

- **Professional Chess Engine**: Rule-compliant gameplay using python-chess library
- **Intelligent AI**: ELO-based difficulty system (400-3000 rating)
- **Smooth Animations**: Hardware-accelerated piece movements with 150ms transitions
# ♟️ Vexora's Bot - Professional Chess Engine

A sophisticated web-based chess game featuring an intelligent AI opponent with adjustable difficulty levels.

## 🚀 Features

- **Professional Chess Engine**: Rule-compliant gameplay using python-chess library
- **Intelligent AI**: ELO-based difficulty system (400-3000 rating)
- **Smooth Animations**: Hardware-accelerated piece movements with 150ms transitions
- **Victory Conditions**: Comprehensive game end detection (checkmate, stalemate, draws)
- **Modern UI**: Clean, professional interface with responsive design
- **Real-time Gameplay**: Instant AI responses with visual thinking indicators

## 🎯 Game Features

### AI Difficulty Levels
- **Beginner (400-800 ELO)**: Random legal moves for new players
- **Intermediate (900-1500 ELO)**: Basic tactical awareness
- **Advanced (1600-2200 ELO)**: Strategic piece positioning
- **Expert (2300-2700 ELO)**: Advanced tactics and combinations
- **Master (2800-3000 ELO)**: Near-perfect play with deep analysis

### Game Mechanics
- ✅ Complete chess rule validation
- ✅ Castling, en passant, pawn promotion
- ✅ Check and checkmate detection
- ✅ Stalemate and draw conditions
- ✅ Move history tracking
- ✅ Legal move highlighting

## 🛠️ Technology Stack

**Frontend:**
- HTML5 + CSS3 + JavaScript
- React (CDN) for component management
- Hardware-accelerated animations
- Responsive design

**Backend:**
- Python 3.8+
- Flask web framework
- python-chess library for game logic
- CORS enabled for cross-origin requests

## 🔧 Installation & Setup

### Prerequisites
```bash
pip install flask flask-cors python-chess
```

### Running the Game
1. **Start the backend server:**
   ```bash
   cd backend
   python lightweight_app.py
   ```

2. **Open the game:**
   Navigate to `http://localhost:5001` in your browser

## � How to Play

1. **Start a Game**: The board loads with standard chess starting position
2. **Make Moves**: Click a piece to select it, then click the destination square
3. **AI Response**: The AI will automatically move after your turn
4. **Adjust Difficulty**: Use the +/- buttons to change AI strength
5. **New Game**: Click "🔄 New Game" to restart

## 📁 Project Structure

```
chess-react-app/
├── chess.html              # Main game interface
├── backend/
│   ├── lightweight_app.py   # Production Flask server
│   └── advanced_app.py      # Experimental HuggingFace integration
├── .gitignore
└── README.md
```

## 🧠 AI Engine Details

The chess engine uses a sophisticated ELO-based system:

- **Move Selection**: Combines random exploration with tactical awareness
- **Difficulty Scaling**: Progressive complexity from beginner to master level
- **Rule Compliance**: 100% legal move validation using python-chess
- **Performance**: Sub-50ms response times for optimal user experience

## 🎨 UI/UX Features

- **Clean Design**: Professional appearance without distracting animations
- **Responsive Layout**: Works on desktop and tablet devices
- **Visual Feedback**: Clear piece selection and legal move indicators
- **Game Status**: Real-time turn indicators and AI thinking status
- **Result Modals**: Professional victory/defeat/draw notifications

## � API Endpoints

- `POST /api/new_game` - Initialize a new chess game
- `POST /api/make_move` - Submit a player move
- `POST /api/get_ai_move` - Request AI opponent move
- `POST /api/set_difficulty` - Adjust AI difficulty level
- `POST /api/reset_game` - Reset current game state

## 🤝 Contributing

Feel free to fork this project and submit pull requests for improvements!

## 📄 License

This project is open source and available under the MIT License.

---

**Built with ♟️ for professional chess gaming**
