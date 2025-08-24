@echo off
echo 🚀 Setting up Smooth Chess Game...
echo ==================================

REM Setup Backend
echo 📦 Setting up Python Backend...
cd backend

REM Install Python dependencies
echo Installing Python packages...
pip install -r requirements.txt

echo ✅ Backend setup complete!

REM Setup Frontend
echo 📦 Setting up React Frontend...
cd ..\frontend

REM Install Node.js dependencies
echo Installing Node.js packages...
npm install

echo ✅ Frontend setup complete!

cd ..

echo.
echo 🎉 Setup Complete!
echo ===================
echo.
echo To start the application:
echo.
echo 1. Start the backend (Terminal 1):
echo    cd backend ^&^& python app.py
echo.
echo 2. Start the frontend (Terminal 2):
echo    cd frontend ^&^& npm start
echo.
echo 3. Open your browser to: http://localhost:3000
echo.
echo Features:
echo ✨ Smooth 700ms CSS animations
echo 🎯 Zero jitter with Framer Motion
echo 🤖 Adjustable AI difficulty (400-3000 ELO)
echo ♟️  Professional chess experience
