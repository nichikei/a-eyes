// Snapshots panel showing captured frames with annotations

import { motion, AnimatePresence } from 'framer-motion';
import { Download, Trash2, Image, Calendar } from 'lucide-react';
import { useSession } from '../state/SessionContext';
import { formatTimestamp, downloadBase64Image } from '../lib/throttle';

export function Snapshots() {
  const { state, clearSnapshots } = useSession();

  const downloadSnapshot = (snapshot: typeof state.snapshots[0]) => {
    const timestamp = formatTimestamp(snapshot.timestamp).replace(/:/g, '-');
    const filename = `ai-eyes-snapshot-${timestamp}.jpg`;
    
    // Use annotated image if available, otherwise use regular image
    const imageData = snapshot.annotatedImage || snapshot.image;
    downloadBase64Image(imageData, filename);
  };

  return (
    <div className="h-80 flex flex-col">
      {/* Header with clear button */}
      {state.snapshots.length > 0 && (
        <div className="flex justify-end mb-3">
          <button
            onClick={clearSnapshots}
            className="p-1.5 rounded-lg bg-red-500/20 border border-red-500/30 hover:bg-red-500/30 text-red-400 hover:text-red-300 text-xs transition-all duration-200"
            aria-label="Clear all snapshots"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Snapshots grid */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {state.snapshots.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <Image className="h-8 w-8 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No snapshots yet</p>
            <p className="text-xs text-gray-500 mt-1">
              Captured frames will appear here
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <AnimatePresence initial={false}>
              {state.snapshots.map((snapshot, index) => (
                <motion.div
                  key={snapshot.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="group relative bg-slate-800/50 rounded-lg overflow-hidden border border-slate-700/50 hover:border-slate-600/50 transition-all duration-200"
                >
                  {/* Image */}
                  <div className="aspect-video relative overflow-hidden bg-slate-900">
                    <img
                      src={snapshot.annotatedImage || snapshot.image}
                      alt={snapshot.caption}
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Annotation indicator */}
                    {snapshot.annotatedImage && (
                      <div className="absolute top-2 left-2 bg-green-500/20 border border-green-500/50 rounded px-2 py-1">
                        <span className="text-xs text-green-300 font-medium">
                          Annotated
                        </span>
                      </div>
                    )}

                    {/* Download overlay */}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <button
                        onClick={() => downloadSnapshot(snapshot)}
                        className="p-3 rounded-full bg-white/20 hover:bg-white/30 focus-ring transition-colors"
                        aria-label="Download snapshot"
                      >
                        <Download className="h-5 w-5 text-white" />
                      </button>
                    </div>
                  </div>

                  {/* Caption and metadata */}
                  <div className="p-3">
                    <p className="text-sm text-white leading-relaxed line-clamp-2 mb-2">
                      {snapshot.caption}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{formatTimestamp(snapshot.timestamp)}</span>
                      </div>
                      
                      {snapshot.annotatedImage && (
                        <span className="text-green-400">
                          With annotations
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Footer info */}
      <div className="px-4 py-2 border-t border-slate-700/50 bg-slate-800/30">
        <div className="flex justify-between text-xs text-slate-400">
          <span>
            {state.snapshots.length > 0 
              ? `${state.snapshots.length} snapshot${state.snapshots.length !== 1 ? 's' : ''}` 
              : 'No snapshots'
            }
          </span>
          <span>
            {state.snapshots.filter(s => s.annotatedImage).length} annotated
          </span>
        </div>
      </div>
    </div>
  );
}