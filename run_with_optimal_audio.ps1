# run_with_optimal_audio.ps1
# PowerShell script để chạy AI Eyes với audio tối ưu

Write-Host "🎵 Setting up optimal Windows audio for AI Eyes..." -ForegroundColor Cyan

# Set WASAPI driver for best Windows audio performance
$env:SDL_AUDIODRIVER = "wasapi"
Write-Host "✅ Audio driver set to WASAPI" -ForegroundColor Green

# Verify Python environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
} elseif (Test-Path "yolov5\myenvs\yolov5env\Scripts\Activate.ps1") {
    Write-Host "✅ YOLOv5 environment found" -ForegroundColor Green  
    & yolov5\myenvs\yolov5env\Scripts\Activate.ps1
} else {
    Write-Host "⚠️ No virtual environment found, using system Python" -ForegroundColor Yellow
}

# Display current configuration
Write-Host "`n🎚️ Audio Configuration:" -ForegroundColor Cyan
Write-Host "   Driver: $env:SDL_AUDIODRIVER" -ForegroundColor White
Write-Host "   Throttling: 1.8s minimum between speech" -ForegroundColor White
Write-Host "   Deduplication: 3.5s window" -ForegroundColor White
Write-Host "   Fallback: Online gTTS -> Offline pyttsx3" -ForegroundColor White

Write-Host "`n🚀 Starting AI Eyes Vision Assistant..." -ForegroundColor Cyan
Write-Host "Expected behavior:" -ForegroundColor Yellow
Write-Host "   - Less frequent speech announcements" -ForegroundColor Yellow
Write-Host "   - Stable WASAPI audio output" -ForegroundColor Yellow  
Write-Host "   - Auto cleanup of temp files" -ForegroundColor Yellow
Write-Host "   - Offline fallback if network issues" -ForegroundColor Yellow

# Run the application
streamlit run .\main.py