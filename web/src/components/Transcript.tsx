// Modern Transcript panel with chat-like interface and enhanced features

import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, Copy, Trash2, MessageSquare, Clock, CheckCircle, Play } from 'lucide-react';
import { useSession } from '../state/SessionContext';
import { formatTimestamp } from '../lib/throttle';

interface TranscriptProps {
  onReplayText: (text: string) => void;
}

export function Transcript({ onReplayText }: TranscriptProps) {
  const { state, clearTranscript } = useSession();

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could show a toast notification here
      console.log('Copied to clipboard:', text);
    });
  };

  return (
    <motion.div 
      className="relative h-80 flex flex-col"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header with clear button */}
      {state.transcript.length > 0 && (
        <div className="flex justify-end mb-3">
          <motion.button
            onClick={clearTranscript}
            className="p-1.5 rounded-lg bg-red-500/20 border border-red-500/30 hover:bg-red-500/30 text-red-400 hover:text-red-300 text-xs transition-all duration-200"
            aria-label="Clear transcript"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Trash2 className="h-4 w-4" />
          </motion.button>
        </div>
      )}

      {/* Transcript chat list */}
      <div className="relative flex-1 overflow-y-auto space-y-3 min-h-0">
        {state.transcript.length === 0 ? (
          <motion.div 
            className="text-center py-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <motion.div 
              className="flex items-center justify-center w-12 h-12 mb-3 mx-auto bg-gray-700/30 border border-gray-600/50 rounded-xl"
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ repeat: Infinity, duration: 3 }}
            >
              <Volume2 className="h-6 w-6 text-gray-400" />
            </motion.div>
            <h3 className="text-sm font-medium text-gray-300 mb-1">No voice entries yet</h3>
            <p className="text-xs text-gray-400">
              Start describing to see AI responses
            </p>
          </motion.div>
        ) : (
          <AnimatePresence initial={false}>
            {state.transcript.map((entry, index) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ 
                  duration: 0.3, 
                  delay: index * 0.05,
                  type: "spring",
                  bounce: 0.2
                }}
                className="group"
              >
                {/* Chat bubble */}
                <div className="flex items-start gap-3">
                  {/* Avatar */}
                  <motion.div 
                    className={`
                      flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2
                      ${entry.spoken 
                        ? 'bg-emerald-500/20 border-emerald-500/50' 
                        : 'bg-slate-700/50 border-slate-600/50'
                      }
                    `}
                    whileHover={{ scale: 1.1 }}
                  >
                    {entry.spoken ? (
                      <CheckCircle className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <Clock className="h-5 w-5 text-slate-400" />
                    )}
                  </motion.div>

                  {/* Message bubble */}
                  <div className="flex-1 min-w-0">
                    <motion.div
                      className={`
                        relative p-4 rounded-2xl border transition-all duration-200
                        ${entry.spoken 
                          ? 'bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-emerald-500/30' 
                          : 'bg-gradient-to-r from-slate-800/60 to-slate-800/40 border-slate-700/50'
                        }
                        group-hover:border-slate-600/70 group-hover:shadow-lg
                      `}
                      whileHover={{ scale: 1.02 }}
                      transition={{ duration: 0.2 }}
                    >
                      {/* Message content */}
                      <p className="text-white text-sm leading-relaxed break-words mb-3">
                        {entry.text}
                      </p>
                      
                      {/* Message metadata */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTimestamp(entry.timestamp)}
                          </span>
                          {entry.spoken && (
                            <motion.span 
                              className="text-xs text-emerald-400 bg-emerald-500/20 px-2 py-1 rounded-full border border-emerald-500/30 flex items-center gap-1"
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              transition={{ delay: 0.2 }}
                            >
                              <Volume2 className="h-3 w-3" />
                              Spoken
                            </motion.span>
                          )}
                        </div>

                        {/* Action buttons */}
                        <motion.div 
                          className="flex items-center gap-1"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.3 }}
                        >
                          {/* Replay button */}
                          <motion.button
                            onClick={() => onReplayText(entry.text)}
                            className="p-2 rounded-lg bg-blue-500/20 border border-blue-500/30 hover:bg-blue-500/30 text-blue-400 hover:text-blue-300 focus-ring transition-all duration-200"
                            aria-label="Replay this text"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                          >
                            <Play className="h-3.5 w-3.5" />
                          </motion.button>

                          {/* Copy button */}
                          <motion.button
                            onClick={() => copyToClipboard(entry.text)}
                            className="p-2 rounded-lg bg-slate-600/20 border border-slate-600/30 hover:bg-slate-600/40 text-slate-400 hover:text-slate-300 focus-ring transition-all duration-200"
                            aria-label="Copy text to clipboard"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                          >
                            <Copy className="h-3.5 w-3.5" />
                          </motion.button>
                        </motion.div>
                      </div>
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Enhanced footer stats */}
      {state.transcript.length > 0 && (
        <motion.div 
          className="relative px-6 py-3 border-t border-slate-700/50 bg-gradient-to-r from-slate-800/60 to-slate-800/40"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4 text-slate-300">
              <span className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-emerald-400" />
                {state.transcript.length} total
              </span>
              <span className="flex items-center gap-2">
                <Volume2 className="h-4 w-4 text-green-400" />
                {state.transcript.filter(entry => entry.spoken).length} spoken
              </span>
            </div>
            <div className="text-slate-400 text-xs">
              Vietnamese Speech History
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}