// Duration Helper Script
// This script helps with accurate video duration handling for module completion tracking

(function() {
    'use strict';
    
    // Parse duration string (HH:MM:SS, MM:SS, or seconds) to seconds
    function parseDurationToSeconds(durationStr) {
        if (!durationStr) return 0;

        try {
            // Trim whitespace
            const s = String(durationStr).trim();

            // If purely numeric (seconds) - allow floats
            if (/^\d+(?:\.\d+)?$/.test(s)) {
                return Math.floor(parseFloat(s));
            }

            // Handle colon-separated formats (SS, MM:SS, HH:MM:SS, etc.)
            if (s.includes(':')) {
                const parts = s.split(':').map(p => p.trim()).filter(p => p !== '');

                // Support variable-length parts: [...hours,] minutes, seconds
                // Example: ['1','02','30'] => 1h 2m 30s
                let seconds = 0;
                try {
                    // Start from the right (seconds)
                    const len = parts.length;
                    if (len >= 1) {
                        seconds += Math.floor(parseFloat(parts[len - 1]) || 0);
                    }
                    if (len >= 2) {
                        seconds += Math.floor((parseFloat(parts[len - 2]) || 0) * 60);
                    }
                    if (len >= 3) {
                        seconds += Math.floor((parseFloat(parts[len - 3]) || 0) * 3600);
                    }
                    // If there are more than 3 parts, treat higher-order as additional hours
                    if (len > 3) {
                        for (let i = 3; i < len; i++) {
                            seconds += Math.floor((parseFloat(parts[len - 1 - i]) || 0) * Math.pow(60, i));
                        }
                    }
                } catch (e) {
                    console.warn('[Duration Helper] Error parsing colon-separated duration parts:', parts, e);
                    return 0;
                }

                return seconds;
            }

            // Fallback: try parseFloat
            const numericValue = parseFloat(s);
            if (!isNaN(numericValue)) {
                return Math.floor(numericValue);
            }
        } catch (e) {
            console.warn('[Duration Helper] Error parsing duration:', durationStr, e);
        }

        return 0; // Default to 0 if parsing fails
    }
    
    // Format seconds to MM:SS
    function formatSecondsToMMSS(seconds) {
        if (isNaN(seconds) || seconds <= 0) return '00:00';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return ${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')};
    }
    
    // Get actual video duration from metadata
    function getActualVideoDuration(videoElement) {
        return new Promise((resolve) => {
            if (!videoElement || !videoElement.duration) {
                resolve(0);
                return;
            }
            
            // If duration is already available
            if (videoElement.duration && !isNaN(videoElement.duration) && isFinite(videoElement.duration)) {
                resolve(Math.floor(videoElement.duration));
                return;
            }
            
            // Wait for metadata to load
            const onLoadedMetadata = () => {
                videoElement.removeEventListener('loadedmetadata', onLoadedMetadata);
                if (videoElement.duration && !isNaN(videoElement.duration) && isFinite(videoElement.duration)) {
                    resolve(Math.floor(videoElement.duration));
                } else {
                    resolve(0);
                }
            };
            
            videoElement.addEventListener('loadedmetadata', onLoadedMetadata);
            
            // Timeout after 5 seconds
            setTimeout(() => {
                videoElement.removeEventListener('loadedmetadata', onLoadedMetadata);
                resolve(0);
            }, 5000);
        });
    }
    
    // Expose functions globally
    window.DurationHelper = {
        parseDurationToSeconds: parseDurationToSeconds,
        formatSecondsToMMSS: formatSecondsToMMSS,
        getActualVideoDuration: getActualVideoDuration
    };
    
})();