# AI Eyes Windows Audio Setup Script
# Run this script before starting the application to configure audio drivers

Write-Host "🚀 AI EYES - Windows Audio Configuration" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Set environment variables for optimal Windows audio support
$env:SDL_AUDIODRIVER = "wasapi"  # Primary driver for Windows 10/11
$env:PYGAME_HIDE_SUPPORT_PROMPT = "1"  # Hide pygame support messages

Write-Host "✅ Audio driver set to: $env:SDL_AUDIODRIVER" -ForegroundColor Yellow

# Test audio system first
Write-Host "`n🔧 Testing audio system..." -ForegroundColor Cyan
try {
    python test_windows_audio.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Audio tests completed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Some audio tests failed - check output above" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Audio test failed: $_" -ForegroundColor Red
    Write-Host "Proceeding anyway..." -ForegroundColor Yellow
}

# Provide fallback instructions
Write-Host "`n💡 If you don't hear audio, try these fallback options:" -ForegroundColor Cyan
Write-Host "   Option 1 (DirectSound): " -NoNewline -ForegroundColor White
Write-Host '$env:SDL_AUDIODRIVER="directsound"; streamlit run .\main.py' -ForegroundColor Gray
Write-Host "   Option 2 (WinMM):       " -NoNewline -ForegroundColor White  
Write-Host '$env:SDL_AUDIODRIVER="winmm"; streamlit run .\main.py' -ForegroundColor Gray

Write-Host "`n🎯 Volume Mixer Check:" -ForegroundColor Cyan
Write-Host "   - Right-click volume icon → Open Volume mixer" -ForegroundColor White
Write-Host "   - Ensure Python/Streamlit is not muted and volume > 0" -ForegroundColor White

# Start the application
Write-Host "`n🚀 Starting AI Eyes Vision Assistant..." -ForegroundColor Green
Write-Host "   Using audio driver: $env:SDL_AUDIODRIVER" -ForegroundColor Yellow
Write-Host "   Expected logs: 'SPOKEN(vi-online): ...' (not vi-mock)" -ForegroundColor Yellow

# Run Streamlit
streamlit run .\main.py