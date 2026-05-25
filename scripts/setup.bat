@echo off
REM Quick setup script for RAG Research Assistant (Windows)

echo.
echo ========================================
echo RAG Research Assistant - Quick Setup
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo [OK] Docker and Docker Compose found
echo.

REM Check .env file
if not exist .env (
    echo [INFO] Creating .env file from template...
    copy .env.example .env
    echo.
    echo [WARNING] IMPORTANT: Edit .env and set your GOOGLE_API_KEY and passwords!
    echo           Open .env in Notepad and configure it.
    echo.
    pause
)

REM Validate API key
findstr /C:"your-google-ai-studio-api-key" .env >nul
if not errorlevel 1 (
    echo [ERROR] Please set GOOGLE_API_KEY in .env file
    pause
    exit /b 1
)

echo [OK] Environment configured
echo.

REM Start services
echo [INFO] Starting Docker services...
docker-compose up -d

echo.
echo [INFO] Waiting for services to be ready...
timeout /t 15 /nobreak >nul

REM Check health
echo [INFO] Checking service health...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend may still be starting. Check logs if issues persist.
    echo           Run: docker-compose logs backend
) else (
    echo [OK] Backend is healthy
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Access points:
echo   Frontend:    http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo   Prometheus:  http://localhost:9090
echo   Grafana:     http://localhost:3001 (admin/admin)
echo.
echo Next steps:
echo   1. Open http://localhost:3000
echo   2. Register a new account
echo   3. Upload a research paper (PDF)
echo   4. Start asking questions!
echo.
echo For detailed documentation, see:
echo   - README.md (architecture and features)
echo   - SETUP.md (detailed setup guide)
echo.
echo Useful commands:
echo   View logs:    docker-compose logs -f
echo   Stop all:     docker-compose down
echo   Restart:      docker-compose restart
echo.
pause
