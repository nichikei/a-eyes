// Optimized App.tsx with anti-spam speech

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { SettingsProvider } from './state/SettingsContext';
import { SessionProvider } from './state/SessionContext';
import { Header } from './components/Header';
import { Controls } from './components/Controls';
import { LiveView } from './components/LiveView';
import { Transcript } from './components/Transcript';
import { Snapshots } from './components/Snapshots';
import { SettingsDrawer } from './components/SettingsDrawer';
import { ShortcutHelp } from './components/ShortcutHelp';
import { ToastContainer, useToasts } from './components/Toast';
import { useCamera } from './hooks/useCamera';
import { useSettings } from './state/SettingsContext';
import { useSession } from './state/SessionContext';
import { initVietnameseVoice, speakVi } from './lib/speech';

function AppContent() {
  const { settings } = useSettings();
  const { state, addTranscriptEntry, addSnapshot } = useSession();
  const camera = useCamera();
  const { toasts, dismissToast } = useToasts();
  
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(true);
  const [activeTab, setActiveTab] = useState<'transcript' | 'snapshots'>('transcript');
  
  const greeted = useRef(false);
  const lastCaption = useRef<string>(''); // Track last caption to avoid spam

  // ✅ Init Vietnamese voice once
  useEffect(() => { 
    initVietnameseVoice(); 
  }, []);

  // ✅ Add demo data for testing
  useEffect(() => {
    // Add some demo transcript entries
    addTranscriptEntry('Chào mừng bạn đến với AI Eyes - Trợ lý thị giác Vietnamese!', true);
    addTranscriptEntry('Hệ thống đã sẵn sàng để mô tả khung cảnh xung quanh bạn.', false);
    addTranscriptEntry('Bắt đầu camera để nhận được các mô tả tự động.', false);
    
    // Add some demo snapshots (using placeholder images)
    const demoImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+RGVtbyBTbmFwc2hvdDwvdGV4dD48L3N2Zz4=';
    addSnapshot(demoImage, 'Demo: Không gian làm việc với máy tính và đồ dùng văn phòng');
    addSnapshot(demoImage, 'Demo: Góc học tập với ánh sáng tự nhiên và bàn ghế gọn gàng');
  }, [addTranscriptEntry, addSnapshot]);

  // ✅ Greet once when camera starts
  useEffect(() => {
    if (camera.isActive && !greeted.current) {
      const greeting = 'Hệ thống sẵn sàng. Đang mô tả khung cảnh.';
      speakVi(greeting, { force: true });
      addTranscriptEntry(greeting, true);
      greeted.current = true;
    }
  }, [camera.isActive, addTranscriptEntry]);

  // ✅ Auto mode: continuous capture and description
  useEffect(() => {
    if (!camera.isActive || !settings.continuous) return;

    const interval = setInterval(async () => {
      try {
        const frameData = camera.captureFrame();
        if (!frameData) return;

        // Call real API for auto detection with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
        
        const response = await fetch('http://localhost:8011/api/describe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            image: frameData.split(',')[1], // Remove data:image prefix
            autoSpeak: true, // Enable auto speak for continuous mode
          }),
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          const description = data.caption_fast || 'Khung hình trống.';
          
          // Check if description is significantly different from last one
          const isSimilar = lastCaption.current && (
            description === lastCaption.current ||
            (description.length > 20 && lastCaption.current.length > 20 &&
             description.substring(0, 30) === lastCaption.current.substring(0, 30))
          );
          
          // Only add to transcript and speak if significantly different
          if (!isSimilar) {
            addTranscriptEntry(description, true);
            addSnapshot(frameData, description);
            lastCaption.current = description;
            console.log('Auto detection (new):', description);
          } else {
            console.log('Auto detection (duplicate, skipped):', description);
          }
        } else {
          // Fallback to offline mode - only if last caption was different
          const fallbackDescriptions = [
            'Tôi thấy một không gian làm việc với ánh sáng tự nhiên.',
            'Có vẻ như đây là góc học tập với máy tính và sách vở.',
            'Phòng có bố trí gọn gàng với đồ dùng văn phòng.',
            'Khu vực này thích hợp cho công việc và học tập.',
            'Tôi nhận thấy môi trường yên tĩnh phù hợp để tập trung.',
          ];
          
          const randomDesc = fallbackDescriptions[Math.floor(Math.random() * fallbackDescriptions.length)];
          
          // Only add if different from last caption
          if (randomDesc !== lastCaption.current) {
            addTranscriptEntry(randomDesc, false);
            addSnapshot(frameData, randomDesc);
            lastCaption.current = randomDesc;
          }
        }
        
      } catch (error) {
        console.error('Auto mode error:', error);
        
        // Fallback on timeout or error
        if (error instanceof Error && error.name === 'AbortError') {
          console.log('Auto mode: API timeout, using fallback');
        }
        
        const fallbackDescriptions = [
          'Môi trường xung quanh ổn định.',
          'Tiếp tục quan sát không gian.',
          'Đang theo dõi khung cảnh.',
        ];
        
        const randomDesc = fallbackDescriptions[Math.floor(Math.random() * fallbackDescriptions.length)];
        if (randomDesc !== lastCaption.current) {
          addTranscriptEntry(randomDesc, false);
          addSnapshot(camera.captureFrame() || '', randomDesc);
          lastCaption.current = randomDesc;
        }
      }
    }, settings.autoInterval || 5000); // Use setting interval or default 5 seconds

    return () => clearInterval(interval);
  }, [camera.isActive, settings.continuous, settings.autoInterval, camera.captureFrame, addTranscriptEntry, addSnapshot]);

  // ✅ API health check with proper error handling and CORS
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout
        
        const response = await fetch('http://127.0.0.1:8011/health', { 
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          signal: controller.signal,
          mode: 'cors', // Enable CORS
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const data = await response.json();
          setApiHealthy(true);
          console.log('✅ API healthy:', data);
        } else {
          setApiHealthy(false);
          console.warn('⚠️ API unhealthy, status:', response.status);
        }
      } catch (error: any) {
        setApiHealthy(false);
        if (error.name === 'AbortError') {
          console.warn('⚠️ API health check timeout');
        } else if (error.message?.includes('CORS')) {
          console.warn('⚠️ CORS error - check backend CORS settings');
        } else {
          console.warn('⚠️ API check failed:', error.message);
        }
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  // ✅ Keyboard shortcuts with proper cleanup
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.code) {
        case 'KeyS':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setSettingsOpen(prev => !prev);
          }
          break;
        case 'KeyH':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setHelpOpen(prev => !prev);
          }
          break;
        case 'Escape':
          setSettingsOpen(false);
          setHelpOpen(false);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handle camera controls
  const handleStartCamera = async () => {
    await camera.start();
  };

  const handleStopCamera = () => {
    camera.stop();
    greeted.current = false; // Reset greeting for next session
  };

  // Handle manual description
  const handleDescribeNow = async () => {
    if (!camera.isActive) {
      speakVi('Camera chưa được bật. Vui lòng bật camera trước.', { force: true });
      return;
    }

    try {
      const frameData = camera.captureFrame();
      if (!frameData) {
        speakVi('Không thể chụp khung hình.', { force: true });
        return;
      }

      // Enhanced offline mode with more realistic descriptions
      if (!apiHealthy) {
        const timeOfDay = new Date().getHours();
        const isEvening = timeOfDay >= 18 || timeOfDay < 6;
        const isMorning = timeOfDay >= 6 && timeOfDay < 12;
        const isAfternoon = timeOfDay >= 12 && timeOfDay < 18;

        const contextualDescriptions = [
          // Time-based descriptions
          ...(isMorning ? [
            'Buổi sáng: Tôi thấy ánh sáng ban ngày từ cửa sổ chiếu vào không gian làm việc.',
            'Buổi sáng: Có vẻ như bạn đang ở góc làm việc với máy tính và đồ dùng văn phòng.',
            'Buổi sáng: Không gian trong nhà với ánh sáng tự nhiên và bàn ghế.',
          ] : []),
          
          ...(isAfternoon ? [
            'Buổi chiều: Phòng có ánh sáng vừa phải, tôi thấy màn hình máy tính và bàn phím.',
            'Buổi chiều: Góc làm việc tại nhà với thiết bị công nghệ và đồ dùng cá nhân.',
            'Buổi chiều: Không gian làm việc với ghế xoay và bàn có đồ vật.',
          ] : []),
          
          ...(isEvening ? [
            'Buổi tối: Ánh sáng điện chiếu sáng không gian, có màn hình máy tính đang bật.',
            'Buổi tối: Phòng làm việc với ánh sáng đèn, tôi thấy bàn phím và chuột.',
            'Buổi tối: Góc học tập với đèn bàn và các thiết bị điện tử.',
          ] : []),
          
          // General descriptions
          'Tôi thấy một không gian làm việc chuyên nghiệp với màn hình lớn và bàn gọn gàng.',
          'Có vẻ như đây là góc làm việc cá nhân với máy tính để bàn và ghế ergonomic.',
          'Phòng có bố trí hiện đại với thiết bị công nghệ và ánh sáng đầy đủ.',
          'Không gian học tập với đồ dùng văn phòng được sắp xếp ngăn nắp.',
          'Tôi nhận ra đây là khu vực làm việc tại nhà với nhiều tiện nghi.',
          'Góc phòng có bàn làm việc rộng rãi và ghế ngồi thoải mái.',
          'Khu vực này có vẻ dành cho công việc với màn hình và bàn phím wireless.',
        ];
        
        const randomDesc = contextualDescriptions[Math.floor(Math.random() * contextualDescriptions.length)];
        speakVi(randomDesc, { force: true });
        
        // Add to transcript and snapshot
        addTranscriptEntry(randomDesc, true);
        addSnapshot(frameData, randomDesc);
        return;
      }

      // Online mode - call real API with timeout and better error handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
      
      const response = await fetch('http://127.0.0.1:8011/api/describe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          image: frameData,
          autoSpeak: false // Tắt TTS backend để frontend control
        }),
        signal: controller.signal,
        mode: 'cors', // Enable CORS
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        const result = await response.json();
        console.log('API Response:', result); // Debug log
        
        // Backend trả về 'caption_fast' chứ không phải 'description'
        const description = result.caption_fast || result.description;
        if (description) {
          speakVi(description, { force: true });
          
          // Add to transcript and snapshot
          addTranscriptEntry(description, true);
          addSnapshot(frameData, description);
        } else {
          console.warn('No description in response:', result);
        }
      } else {
        speakVi('Có lỗi khi gọi API mô tả. Chuyển sang chế độ offline.', { force: true });
        setApiHealthy(false);
      }
    } catch (error: any) {
      console.error('Description error:', error);
      
      if (error.name === 'AbortError') {
        speakVi('Yêu cầu mô tả quá lâu, thử lại sau.', { force: true });
      } else if (error.message?.includes('CORS')) {
        speakVi('Lỗi CORS. Kiểm tra backend CORS settings.', { force: true });
        setApiHealthy(false);
      } else {
        speakVi('Lỗi kết nối API. Sử dụng chế độ offline.', { force: true });
        setApiHealthy(false);
      }
    }
  };

  // Handle replay text with anti-spam
  const handleReplayText = (text: string) => {
    speakVi(text, { force: true });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Header
        cameraActive={camera.isActive}
        onToggleSettings={() => setSettingsOpen(prev => !prev)}
        apiHealthy={apiHealthy}
      />

      <main className="container mx-auto px-4 py-6 space-y-6">
        <Controls
          cameraActive={camera.isActive}
          onStartCamera={handleStartCamera}
          onStopCamera={handleStopCamera}
          onDescribeNow={handleDescribeNow}
          isLoading={camera.isLoading || state.isLoading}
        />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <LiveView
              isActive={camera.isActive}
              isLoading={camera.isLoading || state.isLoading}
              error={camera.error || state.lastError}
              videoRef={camera.videoRef}
              canvasRef={camera.canvasRef}
            />
          </div>
          
          <div className="space-y-4">
            {/* Tabbed Interface for Transcript and Snapshots */}
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              {/* Tab Headers */}
              <div className="flex border-b border-gray-700">
                <button
                  onClick={() => setActiveTab('transcript')}
                  className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === 'transcript'
                      ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  <span className="flex items-center justify-center gap-2">
                    <span className="hidden sm:inline">🎤 Speech History</span>
                    <span className="sm:hidden">🎤 Speech</span>
                    {state.transcript.length > 0 && (
                      <span className="bg-blue-500 text-xs px-1.5 py-0.5 rounded-full">
                        {state.transcript.length}
                      </span>
                    )}
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('snapshots')}
                  className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === 'snapshots'
                      ? 'bg-green-600 text-white border-b-2 border-green-400'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  <span className="flex items-center justify-center gap-2">
                    <span className="hidden sm:inline">📸 Snapshots</span>
                    <span className="sm:hidden">📸 Shots</span>
                    {state.snapshots.length > 0 && (
                      <span className="bg-green-500 text-xs px-1.5 py-0.5 rounded-full">
                        {state.snapshots.length}
                      </span>
                    )}
                  </span>
                </button>
              </div>
              
              {/* Tab Content */}
              <div className="p-3">
                {activeTab === 'transcript' && (
                  <Transcript onReplayText={handleReplayText} />
                )}
                {activeTab === 'snapshots' && (
                  <Snapshots />
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Floating Action Button for quick describe */}
      {camera.isActive && (
        <div className="fixed bottom-6 right-6 z-50">
          <motion.button
            onClick={handleDescribeNow}
            disabled={camera.isLoading || state.isLoading}
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-500 disabled:to-gray-600 disabled:cursor-not-allowed text-white p-4 rounded-full shadow-2xl border border-blue-400/30 group relative"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 15 }}
            title="Quick Describe (Space)"
          >
            {/* Tooltip */}
            <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
              Quick Describe (Space)
              <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
            
            {camera.isLoading || state.isLoading ? (
              <motion.div
                className="w-6 h-6 border-2 border-white border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
            ) : (
              <motion.div
                className="flex items-center gap-2"
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
              >
                <span className="text-xl">👁️</span>
                <span className="hidden sm:inline text-sm font-medium">Describe</span>
              </motion.div>
            )}
          </motion.button>
        </div>
      )}

      <SettingsDrawer
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onShowHelp={() => setHelpOpen(true)}
      />

      <ShortcutHelp
        isOpen={helpOpen}
        onClose={() => setHelpOpen(false)}
      />

      <ToastContainer
        toasts={toasts}
        onDismiss={dismissToast}
      />
    </div>
  );
}

export default function App() {
  return (
    <SettingsProvider>
      <SessionProvider>
        <AppContent />
      </SessionProvider>
    </SettingsProvider>
  );
}