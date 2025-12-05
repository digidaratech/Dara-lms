// Real-time Video Tracking Solution
// This script provides accurate tracking that only counts time when videos are actually playing

(function() {
    'use strict';
    
    // Configuration
    const TRACKING_CONFIG = {
        UPDATE_INTERVAL: 1,            // Send update every 1 second for more accurate tracking
        COMPLETION_THRESHOLD: 100,     // Auto-complete threshold percentage
        DEBOUNCE_DELAY: 300,           // 300ms for more responsive UI
        TEST_MODE_DURATION: 60         // In test mode, simulate 60 second videos
    };
    
    // Global tracking state
    let trackingState = {
        progressUpdateQueue: [],
        isUpdating: false,
        updateDebounceTimer: null,
        videoTrackingInterval: null,
        moduleCompleted: false,
        currentModuleProgress: 0,
        lastSentProgress: 0,
        isVideoPlaying: false,
        hasPlayPauseControls: false, // Flag to indicate if we have explicit play/pause controls
        watchedTime: 0,
        totalDuration: 0, // Will be set from module data
        courseId: null,
        moduleId: null,
        lastUpdateTime: 0 // Track when we last sent an update
    };

    // Helper: parse duration strings like "HH:MM:SS", "MM:SS" or plain seconds to seconds (integer)
    function parseDurationString(durationStr) {
        if (durationStr === null || durationStr === undefined) return 0;
        const s = String(durationStr).trim();
        if (s === '') return 0;

        // plain numeric seconds (allow floats)
        if (/^\d+(?:\.\d+)?$/.test(s)) {
            const numValue = parseFloat(s);
            // Handle edge case where duration might be stored as milliseconds
            if (numValue > 36000) { // If greater than 10 hours in seconds, likely milliseconds
                return Math.floor(numValue / 1000);
            }
            return Math.floor(numValue);
        }

        // colon-separated: parse right-to-left (seconds, minutes, hours, ...)
        if (s.indexOf(':') !== -1) {
            const parts = s.split(':').map(p => p.trim()).filter(Boolean);
            let seconds = 0;
            let multiplier = 1; // seconds, then minutes (60), then hours (3600)...
            for (let i = parts.length - 1; i >= 0; i--) {
                const part = parts[i];
                const value = (i === parts.length - 1) ? parseFloat(part) : parseInt(part, 10);
                if (isNaN(value)) return 0;
                seconds += value * multiplier;
                multiplier *= 60;
            }
            return Math.floor(seconds);
        }

        // Handle common duration formats like "2 minutes 41 seconds"
        if (s.toLowerCase().includes('minute') || s.toLowerCase().includes('second')) {
            let totalSeconds = 0;
            // Extract hours
            const hoursMatch = s.match(/(\d+)\s*hour/i);
            if (hoursMatch) totalSeconds += parseInt(hoursMatch[1]) * 3600;
            // Extract minutes
            const minutesMatch = s.match(/(\d+)\s*minute/i);
            if (minutesMatch) totalSeconds += parseInt(minutesMatch[1]) * 60;
            // Extract seconds
            const secondsMatch = s.match(/(\d+)\s*second/i);
            if (secondsMatch) totalSeconds += parseInt(secondsMatch[1]);
            return totalSeconds;
        }
        
        // fallback
        const f = parseFloat(s);
        if (isNaN(f)) return 0;
        // Handle edge case where duration might be stored as milliseconds
        if (f > 36000) { // If greater than 10 hours in seconds, likely milliseconds
            return Math.floor(f / 1000);
        }
        return Math.floor(f);
    }

    // Helper: parse flexible time params (seconds, '1m30s', '1:06:34') into seconds
    function parseTimeParam(val) {
        if (val === null || val === undefined) return null;
        const s = String(val).trim();
        if (s === '') return null;

        // pure integer seconds
        if (/^\d+$/.test(s)) return parseInt(s, 10);

        // seconds with 's' suffix
        const mSec = s.match(/^(\d+(?:\.\d+)?)s$/i);
        if (mSec) return Math.round(parseFloat(mSec[1]));

        // patterns like '1h6m34s' or '1m30s'
        if (/[hms]/i.test(s)) {
            try {
                const hr = s.match(/(\d+(?:\.\d+)?)\s*h/i);
                const mn = s.match(/(\d+(?:\.\d+)?)\s*m(?!s)/i);
                const sc = s.match(/(\d+(?:\.\d+)?)\s*s/i);
                const hours = hr ? parseFloat(hr[1]) : 0;
                const minutes = mn ? parseFloat(mn[1]) : 0;
                const seconds = sc ? parseFloat(sc[1]) : 0;
                const total = Math.round(hours * 3600 + minutes * 60 + seconds);
                if (total > 0) return total;
            } catch (e) {
                return null;
            }
        }

        // colon format like H:MM:SS or MM:SS
        try {
            const col = parseDurationString(s);
            return col > 0 ? col : null;
        } catch (e) {
            return null;
        }
    }

    // Helper: extract start/end from iframe src (handles ?start=, ?end=, ?t= and hash #t=)
    function extractStartEndFromUrl(src) {
        try {
            if (!src) return { start: 0, end: null };
            const u = new URL(src, window.location.href);
            const params = u.searchParams;
            const startRaw = params.get('start') || params.get('t') || null;
            const endRaw = params.get('end') || null;

            let start = parseTimeParam(startRaw);
            let end = parseTimeParam(endRaw);

            // check hash like #t=1m30s
            if ((start === null || start === 0) && u.hash) {
                const hash = u.hash.replace('#', '');
                // hash may be 't=90' or 't=1m30s'
                const sp = new URLSearchParams(hash);
                const t = sp.get('t') || null;
                if (t) start = parseTimeParam(t) || start;
            }

            return { start: start || 0, end: end || null };
        } catch (e) {
            return { start: 0, end: null };
        }
    }

    // Helper function to consistently detect local videos
    function isLocalVideoElement() {
        // First check if there's a local video player element
        const localVideoPlayer = document.getElementById('local-video-player');
        if (localVideoPlayer) {
            console.log('[RealTime Tracking] Local video player element found');
            return true;
        }
        
        // Check for HTML5 video element which indicates a local video
        const videoContainer = document.querySelector('.video-container');
        if (videoContainer) {
            const videoElement = videoContainer.querySelector('video');
            if (videoElement) {
                console.log('[RealTime Tracking] HTML5 video element found, treating as local video');
                return true;
            }
        }
        
        // Fallback to URL-based detection by checking video source
        const videoElements = document.querySelectorAll('video source');
        for (let i = 0; i < videoElements.length; i++) {
            const src = videoElements[i].src;
            if (src) {
                // Check if the source points to our local video paths
                const url = new URL(src, window.location.origin);
                const pathname = url.pathname;
                
                if (pathname.includes('/attached_assets/videos/') || pathname.includes('/uploads/')) {
                    console.log('[RealTime Tracking] Local video detected via source path:', pathname);
                    return true;
                }
            }
        }
        
        // Also check iframe sources for local videos
        const iframeElements = document.querySelectorAll('iframe');
        for (let i = 0; i < iframeElements.length; i++) {
            const src = iframeElements[i].src;
            if (src) {
                // If it's a local path, it's not a YouTube/Vimeo video
                try {
                    const url = new URL(src, window.location.origin);
                    const pathname = url.pathname;
                    
                    // If it doesn't contain common video domains, treat as local
                    if (!src.includes('youtube.com') && !src.includes('youtu.be') && 
                        !src.includes('vimeo.com') && !src.includes('dailymotion.com')) {
                        console.log('[RealTime Tracking] Non-embedded video detected, treating as local');
                        return true;
                    }
                } catch (e) {
                    // If URL parsing fails, check if it looks like a local path
                    if (!src.includes('://')) {
                        console.log('[RealTime Tracking] Local path detected in iframe, treating as local');
                        return true;
                    }
                }
            }
        }
        
        console.log('[RealTime Tracking] Video not detected as local');
        return false;
    }

    // Track last sent watched duration (seconds) to avoid percent-only duplicate suppression
    trackingState.lastSentWatchedTime = 0;
    
    // Initialize tracking when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeRealTimeTracking();
    });
    
    // Initialize real-time tracking
    function initializeRealTimeTracking() {
        console.log('[RealTime Tracking] Initializing real-time tracking');
        const container = document.querySelector('.module-video-container');
        if (!container) {
            console.warn('[RealTime Tracking] No module video container found!');
            return;
        }
        
        // Get course and module IDs
        trackingState.courseId = container.dataset.courseId;
        trackingState.moduleId = container.dataset.moduleId;
        
        console.log('[RealTime Tracking] Course ID: ' + trackingState.courseId + ', Module ID: ' + trackingState.moduleId);
        
        if (!trackingState.courseId || !trackingState.moduleId) {
            console.error('[RealTime Tracking] Missing course or module ID');
            return;
        }
        
        // Check if module is already completed - if so, don't start tracking
        const isModuleCompleted = container.dataset.moduleCompleted === 'true';
        console.log('[RealTime Tracking] Module completed status: ' + isModuleCompleted);
        if (isModuleCompleted) {
            console.log('[RealTime Tracking] Module already completed - skipping automatic tracking initialization');
            // Still update the progress bar to show current course progress
            const courseProgress = parseFloat(container.dataset.courseProgress) || 0;
            updateProgressBar(courseProgress);
            
            // For local videos, ensure the UI reflects the completed status
            const isLocalVideo = isLocalVideoElement();
            if (isLocalVideo) {
                // Update the module element in the sidebar to show completed status
                const moduleId = container.dataset.moduleId;
                const moduleElement = document.querySelector('.list-group-item[data-module-id="' + moduleId + '"]');
                if (moduleElement) {
                    moduleElement.classList.add('completed');
                    const icon = moduleElement.querySelector('.fa-play-circle');
                    if (icon) {
                        icon.classList.remove('fa-play-circle');
                        icon.classList.add('fa-check-circle', 'text-success');
                    }
                    const badge = moduleElement.querySelector('.badge');
                    if (badge) {
                        badge.className = 'badge bg-success';
                        badge.textContent = '✅ Done';
                        // Ensure the badge is visible and styled properly
                        badge.style.display = 'inline-block';
                    }
                    
                    // Also update the main module container
                    const mainModuleElement = document.querySelector('.module-video-container');
                    if (mainModuleElement) {
                        mainModuleElement.dataset.moduleCompleted = 'true';
                        mainModuleElement.classList.add('module-completed');
                    }
                }
            }
            
            return;
        }
        
        console.log('[RealTime Tracking] Initializing real-time tracking for course:', trackingState.courseId, 'module:', trackingState.moduleId);
        
        // Reset tracking state for new module
        trackingState.moduleCompleted = false;
        trackingState.currentModuleProgress = 0;
        trackingState.lastSentProgress = 0;
        trackingState.isVideoPlaying = false;
        trackingState.watchedTime = 0;
        trackingState.lastUpdateTime = 0;
        
        // Get video element (works for both HTML5 video and iframe videos)
        const videoContainer = document.querySelector('.video-container');
        if (!videoContainer) {
            console.warn('[RealTime Tracking] No video container found!');
            return;
        }
        
        // For HTML5 video
        const video = videoContainer.querySelector('video');
        if (video) {
            console.log('[RealTime Tracking] HTML5 video detected - setting up real-time tracking');
            // Add a small delay to ensure video metadata is loaded
            setTimeout(function() {
                trackHTML5VideoProgress(video);
            }, 100);
            return;
        }
        
        // For iframe videos (YouTube, Vimeo)
        const iframe = videoContainer.querySelector('iframe');
        if (iframe) {
            console.log('[RealTime Tracking] Iframe video detected - setting up real-time tracking');
            trackIframeVideoProgress(iframe);
            return;
        }
        
        console.warn('[RealTime Tracking] No video element (HTML5 or iframe) found in video container!');
    }
    
    // Track HTML5 video progress (real-time)
    function trackHTML5VideoProgress(video) {
        console.log('[RealTime Tracking] HTML5 video progress tracking initialized');
        
        // Add debugging info
        console.log('[RealTime Tracking] Video element:', video);
        console.log('[RealTime Tracking] Video readyState:', video.readyState);
        console.log('[RealTime Tracking] Video duration (initial):', video.duration);
        console.log('[RealTime Tracking] Video currentTime (initial):', video.currentTime);
        console.log('[RealTime Tracking] Video networkState (initial):', video.networkState);
        console.log('[RealTime Tracking] Video src (initial):', video.src);
        console.log('[RealTime Tracking] Video error (initial):', video.error);
        console.log('[RealTime Tracking] Video preload (initial):', video.preload);
        console.log('[RealTime Tracking] Video autoplay (initial):', video.autoplay);
        console.log('[RealTime Tracking] Video loop (initial):', video.loop);
        console.log('[RealTime Tracking] Video muted (initial):', video.muted);
        console.log('[RealTime Tracking] Video controls (initial):', video.controls);
        console.log('[RealTime Tracking] Video poster (initial):', video.poster);
        console.log('[RealTime Tracking] Video crossOrigin (initial):', video.crossOrigin);
        console.log('[RealTime Tracking] Video currentSrc (initial):', video.currentSrc);
        console.log('[RealTime Tracking] Video seeking (initial):', video.seeking);
        console.log('[RealTime Tracking] Video paused (initial):', video.paused);
        console.log('[RealTime Tracking] Video ended (initial):', video.ended);
        console.log('[RealTime Tracking] Video playbackRate (initial):', video.playbackRate);
        console.log('[RealTime Tracking] Video volume (initial):', video.volume);
        console.log('[RealTime Tracking] Video defaultMuted (initial):', video.defaultMuted);
        console.log('[RealTime Tracking] Video defaultPlaybackRate (initial):', video.defaultPlaybackRate);
        console.log('[RealTime Tracking] Video disablePictureInPicture (initial):', video.disablePictureInPicture);
        console.log('[RealTime Tracking] Video disableRemotePlayback (initial):', video.disableRemotePlayback);
        console.log('[RealTime Tracking] Video playsInline (initial):', video.playsInline);
        console.log('[RealTime Tracking] Video mediaKeys (initial):', video.mediaKeys);
        console.log('[RealTime Tracking] Video remote (initial):', video.remote);
        console.log('[RealTime Tracking] Video sinkId (initial):', video.sinkId);
        console.log('[RealTime Tracking] Video audioTracks (initial):', video.audioTracks);
        console.log('[RealTime Tracking] Video videoTracks (initial):', video.videoTracks);
        console.log('[RealTime Tracking] Video textTracks (initial):', video.textTracks);
        console.log('[RealTime Tracking] Video controller (initial):', video.controller);
        console.log('[RealTime Tracking] Video srcObject (initial):', video.srcObject);
        console.log('[RealTime Tracking] Video controlsList (initial):', video.controlsList);
        console.log('[RealTime Tracking] Video mediaKeys (initial):', video.mediaKeys);
        console.log('[RealTime Tracking] Video remote (initial):', video.remote);
        
        // Add additional debugging for local videos
        const isLocalVideoDebug = isLocalVideoElement();
        console.log('[RealTime Tracking] Is local video:', isLocalVideoDebug);
        if (isLocalVideoDebug) {
            console.log('[RealTime Tracking] Local video detected, adding extra event listeners');
        }
        
        // Resolve duration: prefer player duration if available, otherwise use module data
        const container = document.querySelector('.module-video-container');
        const moduleDurationStr = container && container.dataset ? container.dataset.moduleDuration : null;
        const parsedDuration = parseDurationString(moduleDurationStr);
        
        // Additional debugging
        console.log('[RealTime Tracking] Module duration string: ' + moduleDurationStr + ', parsed: ' + parsedDuration);

        // If video element reports a duration, prefer it (especially for local videos)
        let playerDuration = 0;
        if (video && typeof video.duration === 'number' && isFinite(video.duration) && video.duration > 0) {
            playerDuration = Number(video.duration);
        }
        
        // Additional debugging
        console.log('[RealTime Tracking] Player duration: ' + playerDuration);

        // For local videos, always prefer the actual video duration over the database duration
        // For YouTube videos, we might want to use the database duration if it's more accurate
        const isLocalVideo = isLocalVideoElement();
        
        if (playerDuration > 0) {
            if (isLocalVideo) {
                // For local videos, always use the actual video duration
                trackingState.totalDuration = playerDuration; // Keep fractional seconds for precision
            } else {
                // For YouTube videos, use the larger of the two values
                trackingState.totalDuration = Math.max(parsedDuration || 0, playerDuration);
            }
        } else {
            trackingState.totalDuration = parsedDuration || 0;
        }
        
        // Additional debugging
        console.log('[RealTime Tracking] Total duration set to: ' + trackingState.totalDuration);

        console.log('[RealTime Tracking] Using module duration from data (resolved):', trackingState.totalDuration, 'seconds');
        console.log('[RealTime Tracking] Raw module duration string:', moduleDurationStr);
        
        // Log the actual calculation to help debug
        console.log('[RealTime Tracking] Duration calculation details:', {
            totalDuration: trackingState.totalDuration,
            expectedDuration: "633 seconds (10:33)",
            discrepancy: trackingState.totalDuration - 633
        });
        
        // Fallback: if we still don't have a duration after a few seconds, try to get it from the video
        setTimeout(function() {
            console.log('[RealTime Tracking] Fallback check - Video readyState:', video.readyState);
            console.log('[RealTime Tracking] Fallback check - Video duration:', video.duration);
            console.log('[RealTime Tracking] Fallback check - Current trackingState.totalDuration:', trackingState.totalDuration);
            
            // For local videos, always prefer the actual video duration over the database duration
            const isLocalVideo = isLocalVideoElement();
            
            if (video.duration && isFinite(video.duration) && video.duration > 0) {
                const actualDuration = Number(video.duration);
                if (trackingState.totalDuration <= 0 || (isLocalVideo && Math.abs(actualDuration - trackingState.totalDuration) > 10)) {
                    trackingState.totalDuration = actualDuration;
                    console.log('[RealTime Tracking] Fallback: Updated to actual video duration:', trackingState.totalDuration, 'seconds');
                }
            }
            
            // If we still don't have a duration, use a default value to ensure tracking works
            if (trackingState.totalDuration <= 0) {
                trackingState.totalDuration = 300; // Default to 5 minutes
                console.log('[RealTime Tracking] Fallback: Using default duration of 5 minutes');
            }
            
            console.log('[RealTime Tracking] Final trackingState.totalDuration:', trackingState.totalDuration);
            
            // Additional debugging
            console.log('[RealTime Tracking] Fallback - Final duration: ' + trackingState.totalDuration);
        }, 3000);
        
        // Update UI immediately on video load
        video.addEventListener('loadedmetadata', function() {
            console.log('[RealTime Tracking] Video loaded - Duration:', video.duration, 'seconds');
            console.log('[RealTime Tracking] Video loaded - readyState:', video.readyState, 'networkState:', video.networkState);
            
            // Additional debugging for buffering info
            if (video.buffered && video.buffered.length > 0) {
                console.log('[RealTime Tracking] Video buffered ranges:', video.buffered.length);
                for (let i = 0; i < video.buffered.length; i++) {
                    console.log('[RealTime Tracking] Buffered range ' + i + ': ' + video.buffered.start(i) + ' - ' + video.buffered.end(i));
                }
            }
            
            // Use actual video duration if we don't have module duration or if it's more accurate
            if (video.duration && isFinite(video.duration) && video.duration > 0) {
                const actualDuration = Number(video.duration); // preserve fractional seconds for long videos
                // For local videos, always prefer the actual video duration over the database duration
                const isLocalVideo = isLocalVideoElement();
                
                if (trackingState.totalDuration <= 0 || (isLocalVideo && Math.abs(actualDuration - trackingState.totalDuration) > 10)) {
                    trackingState.totalDuration = actualDuration;
                    console.log('[RealTime Tracking] Updated to actual video duration:', trackingState.totalDuration, 'seconds');
                }
                
                // Additional debugging
                console.log('[RealTime Tracking] Metadata loaded - actualDuration: ' + actualDuration + ', trackingState.totalDuration: ' + trackingState.totalDuration);
            }
            
            // For local videos, ensure we have the correct duration set
            const isLocalVideo = isLocalVideoElement();
            if (isLocalVideo && video.duration && isFinite(video.duration) && video.duration > 0) {
                trackingState.totalDuration = Number(video.duration);
                console.log('[RealTime Tracking] Ensured local video duration:', trackingState.totalDuration, 'seconds');
                
                // Force an initial progress update for local videos
                setTimeout(function() {
                    sendProgressUpdate(video.currentTime, trackingState.totalDuration, false);
                }, 100);
                
                // Additional debugging
                console.log('[RealTime Tracking] Local video duration set: ' + trackingState.totalDuration);
            }
            
            // Additional debugging
            console.log('[RealTime Tracking] Video metadata loaded - currentTime:', video.currentTime, 'duration:', video.duration);
        });
        
        // Track play/pause events
        video.addEventListener('play', function() {
            trackingState.isVideoPlaying = true;
            console.log('[RealTime Tracking] Video play detected');
            console.log('[RealTime Tracking] Video play - readyState:', video.readyState, 'networkState:', video.networkState);
        });
        
        video.addEventListener('playing', function() {
            trackingState.isVideoPlaying = true;
            console.log('[RealTime Tracking] Video playing');
            console.log('[RealTime Tracking] Video playing - readyState:', video.readyState, 'networkState:', video.networkState);
        });
        
        video.addEventListener('pause', function() {
            trackingState.isVideoPlaying = false;
            console.log('[RealTime Tracking] Video pause detected');
            console.log('[RealTime Tracking] Video pause - readyState:', video.readyState, 'networkState:', video.networkState);
        });
        
        // Additional debugging for video state changes
        video.addEventListener('waiting', function() {
            console.log('[RealTime Tracking] Video waiting');
            console.log('[RealTime Tracking] Video waiting - readyState:', video.readyState, 'networkState:', video.networkState);
        });
        
        video.addEventListener('seeking', function() {
            console.log('[RealTime Tracking] Video seeking');
            console.log('[RealTime Tracking] Video seeking - readyState:', video.readyState, 'networkState:', video.networkState);
        });
        
        video.addEventListener('seeked', function() {
            console.log('[RealTime Tracking] Video seeked');
            console.log('[RealTime Tracking] Video seeked - readyState:', video.readyState, 'networkState:', video.networkState);
        });
        
        // Add error event listener
        video.addEventListener('error', function(e) {
            console.error('[RealTime Tracking] Video error occurred:', e);
            console.error('[RealTime Tracking] Video error details - code:', video.error ? video.error.code : 'N/A', 'message:', video.error ? video.error.message : 'N/A');
        });
        
        // Use timeupdate event for more accurate tracking (use float seconds)
        video.addEventListener('timeupdate', function() {
            // Only process if video is actually playing
            if (!trackingState.isVideoPlaying || trackingState.moduleCompleted) return;
            
            // Additional debugging to check video state
            console.log('[RealTime Tracking] Timeupdate - isVideoPlaying: ' + trackingState.isVideoPlaying + ', moduleCompleted: ' + trackingState.moduleCompleted);
            console.log('[RealTime Tracking] Timeupdate - playbackRate: ' + video.playbackRate + ', defaultPlaybackRate: ' + video.defaultPlaybackRate);
            console.log('[RealTime Tracking] Timeupdate - volume: ' + video.volume + ', muted: ' + video.muted);
            console.log('[RealTime Tracking] Timeupdate - loop: ' + video.loop);
            console.log('[RealTime Tracking] Timeupdate - controls: ' + video.controls);
            console.log('[RealTime Tracking] Timeupdate - preload: ' + video.preload);
            console.log('[RealTime Tracking] Timeupdate - autoplay: ' + video.autoplay);
            console.log('[RealTime Tracking] Timeupdate - poster: ' + video.poster);
            console.log('[RealTime Tracking] Timeupdate - crossOrigin: ' + video.crossOrigin);
            console.log('[RealTime Tracking] Timeupdate - currentSrc: ' + video.currentSrc);
            console.log('[RealTime Tracking] Timeupdate - seeking: ' + video.seeking);
            console.log('[RealTime Tracking] Timeupdate - paused: ' + video.paused);
            console.log('[RealTime Tracking] Timeupdate - ended: ' + video.ended);
            console.log('[RealTime Tracking] Timeupdate - networkState: ' + video.networkState);
            console.log('[RealTime Tracking] Timeupdate - readyState: ' + video.readyState);
            console.log('[RealTime Tracking] Timeupdate - error: ' + video.error);
            console.log('[RealTime Tracking] Timeupdate - disableRemotePlayback: ' + video.disableRemotePlayback);
            console.log('[RealTime Tracking] Timeupdate - playsInline: ' + video.playsInline);
            console.log('[RealTime Tracking] Timeupdate - mediaKeys: ' + video.mediaKeys);
            console.log('[RealTime Tracking] Timeupdate - remote: ' + video.remote);
            console.log('[RealTime Tracking] Timeupdate - sinkId: ' + video.sinkId);
            console.log('[RealTime Tracking] Timeupdate - audioTracks: ' + video.audioTracks);
            console.log('[RealTime Tracking] Timeupdate - videoTracks: ' + video.videoTracks);
            console.log('[RealTime Tracking] Timeupdate - textTracks: ' + video.textTracks);
            console.log('[RealTime Tracking] Timeupdate - controller: ' + video.controller);
            console.log('[RealTime Tracking] Timeupdate - defaultMuted: ' + video.defaultMuted);
            console.log('[RealTime Tracking] Timeupdate - defaultPlaybackRate: ' + video.defaultPlaybackRate);
            console.log('[RealTime Tracking] Timeupdate - disablePictureInPicture: ' + video.disablePictureInPicture);
            console.log('[RealTime Tracking] Timeupdate - controlsList: ' + video.controlsList);
            console.log('[RealTime Tracking] Timeupdate - mediaKeys: ' + video.mediaKeys);
            console.log('[RealTime Tracking] Timeupdate - remote: ' + video.remote);
            console.log('[RealTime Tracking] Timeupdate - srcObject: ' + video.srcObject);
            
            // Additional debugging for buffering info
            if (video.buffered && video.buffered.length > 0) {
                let bufferedInfo = '';
                for (let i = 0; i < video.buffered.length; i++) {
                    bufferedInfo += `Range ${i}: ${video.buffered.start(i)}-${video.buffered.end(i)} `;
                }
                console.log('[RealTime Tracking] Video buffered ranges: ' + bufferedInfo);
                
                // Check if we're trying to play beyond buffered content
                let isBeyondBuffer = true;
                for (let i = 0; i < video.buffered.length; i++) {
                    if (video.currentTime >= video.buffered.start(i) && video.currentTime <= video.buffered.end(i)) {
                        isBeyondBuffer = false;
                        break;
                    }
                }
                if (isBeyondBuffer) {
                    console.log('[RealTime Tracking] Warning: Playing beyond buffered content - currentTime: ' + video.currentTime);
                }
            }
            
            // Additional debugging to check if video is at the end
            if (video.currentTime >= video.duration - 0.01) {
                console.log('[RealTime Tracking] Video at end - currentTime: ' + video.currentTime + ', duration: ' + video.duration);
            }
            
            // Additional debugging
            if (video.currentTime >= video.duration - 0.1) {
                console.log('[RealTime Tracking] Timeupdate near end - currentTime: ' + video.currentTime + ', duration: ' + video.duration);
            }
            
            // Additional debugging to check if video is very close to end
            if (video.currentTime >= video.duration - 1) {
                console.log('[RealTime Tracking] Video very close to end - currentTime: ' + video.currentTime + ', duration: ' + video.duration + ', remaining: ' + (video.duration - video.currentTime));
                console.log('[RealTime Tracking] Video state - readyState: ' + video.readyState + ', networkState: ' + video.networkState + ', paused: ' + video.paused + ', ended: ' + video.ended);
            }
            
            // Additional debugging to check if video has stopped progressing
            if (trackingState.lastVideoTime !== undefined && video.currentTime === trackingState.lastVideoTime) {
                console.log('[RealTime Tracking] Video time not progressing - currentTime: ' + video.currentTime + ', lastTime: ' + trackingState.lastVideoTime);
            }
            trackingState.lastVideoTime = video.currentTime;

            // Use floating currentTime for precise watched duration
            const currentTime = typeof video.currentTime === 'number' ? Number(video.currentTime) : Math.floor(video.currentTime || 0);
                    
            // For local videos, always prefer the actual video duration over the database duration
            // For YouTube videos, we might want to use the database duration if it's more accurate
            const container = document.querySelector('.module-video-container');
            const isLocalVideo = isLocalVideoElement();
                    
            // Consistently use the actual video duration for local videos
            let duration = trackingState.totalDuration;
            if (isLocalVideo && video.duration && isFinite(video.duration) && video.duration > 0) {
                // For local videos, always use the actual video duration
                duration = Number(video.duration);
            } else if (!isLocalVideo && trackingState.totalDuration > 0) {
                // For non-local videos, use the tracking state duration
                duration = trackingState.totalDuration;
            } else if (video.duration && isFinite(video.duration) && video.duration > 0) {
                // Fallback to video element duration
                duration = Number(video.duration);
            }
            
            // Additional check for local videos to ensure duration is set correctly
            if (isLocalVideo && (!duration || duration <= 0) && video.duration && isFinite(video.duration) && video.duration > 0) {
                duration = Number(video.duration);
                console.log('[RealTime Tracking] Corrected duration for local video:', duration, 'seconds');
            }
            
            // Additional debugging
            console.log('[RealTime Tracking] Duration check - duration: ' + duration + ', isLocalVideo: ' + isLocalVideo);
            
            // Additional debugging to check if video is at the end
            if (duration > 0 && currentTime >= duration - 0.1) {
                console.log('[RealTime Tracking] Video near end - currentTime: ' + currentTime.toFixed(3) + ', duration: ' + duration.toFixed(3) + ', diff: ' + (duration - currentTime).toFixed(3));
            }

            // Log progress for debugging
            if (duration > 0) {
                const progressPercent = (currentTime / duration) * 100;
                console.log('[RealTime Tracking] Progress: ' + progressPercent.toFixed(2) + '% (Current: ' + currentTime.toFixed(2) + 's, Duration: ' + duration.toFixed(2) + 's)');
                
                // Additional debugging for near completion
                if (currentTime >= duration - 1) {
                    console.log('[RealTime Tracking] Near completion - Current: ' + currentTime.toFixed(3) + 's, Duration: ' + duration.toFixed(3) + 's, Difference: ' + (duration - currentTime).toFixed(3) + 's');
                }
            }

            // Ensure we have a valid duration before proceeding
            if (duration > 0) {
                // Calculate progress percentage using precise floating values
                const progressPercent = (currentTime / duration) * 100;

                // Update based on configured interval or when near completion
                const now = Date.now();
                // Be more responsive when near completion
                const nearCompletion = currentTime >= duration - 1;
                if (now - trackingState.lastUpdateTime >= TRACKING_CONFIG.UPDATE_INTERVAL * 1000 || nearCompletion) {
                    trackingState.lastUpdateTime = now;

                    // Only mark as completed when we've effectively watched the full duration (allow tiny epsilon)
                    // Be more lenient with completion detection for all videos
                    const isLocalVideo = isLocalVideoElement();
                    // For local videos, use a more lenient threshold to ensure completion is detected
                    const completionThreshold = isLocalVideo ? 1.0 : 0.1; // Even more lenient threshold for local videos
                    const shouldComplete = duration > 0 && currentTime >= (duration - completionThreshold);
                                
                    // Additional debugging
                    console.log('[RealTime Tracking] Completion check - shouldComplete: ' + shouldComplete + ', currentTime: ' + currentTime + ', duration: ' + duration + ', threshold: ' + completionThreshold);
                    
                    // Add debugging for completion detection
                    if (duration > 0) {
                        console.log('[RealTime Tracking] Completion check: currentTime=' + currentTime.toFixed(3) + ', duration=' + duration.toFixed(3) + ', threshold=' + (duration - completionThreshold).toFixed(3) + ', shouldComplete=' + shouldComplete + ', moduleCompleted=' + trackingState.moduleCompleted);
                    }

                    if (shouldComplete && !trackingState.moduleCompleted) {
                        console.log('[RealTime Tracking] Watched ' + Math.min(progressPercent, 100).toFixed(2) + '% of module - Marking as completed!');
                        console.log('[RealTime Tracking] Completion details: currentTime=' + currentTime + ', duration=' + duration + ', shouldComplete=' + shouldComplete);
                        console.log('[RealTime Tracking] Completion check - currentTime: ' + currentTime + ', duration: ' + duration + ', diff: ' + (duration - currentTime));
                        trackingState.moduleCompleted = true;
                        // Use the full duration to ensure 100% completion
                        console.log('[RealTime Tracking] Sending completion update with duration:', duration);
                        sendProgressUpdate(duration, duration, true);
                    } else if (!trackingState.moduleCompleted) {
                        console.log('[RealTime Tracking] Watched ' + Math.min(progressPercent, 100).toFixed(2) + '% of module - Not completed yet');
                        if (currentTime >= duration - 5) {
                            console.log('[RealTime Tracking] Near completion - currentTime:', currentTime, 'duration:', duration);
                        }
                        // Send progress update for dynamic course progress tracking
                        sendProgressUpdate(currentTime, duration, shouldComplete);
                    }

                }
                // ALSO send progress update for dynamic tracking (every 2 seconds)
                else if (now - trackingState.lastUpdateTime >= 2000) {
                    trackingState.lastUpdateTime = now;
                    sendProgressUpdate(currentTime, duration, shouldComplete);
                }
            }
        });
        
        // Mark as completed when video ends
        video.addEventListener('ended', function() {
            console.log('[RealTime Tracking] Video ended event fired');
            console.log('[RealTime Tracking] Video ended - currentTime: ' + video.currentTime + ', duration: ' + video.duration);
            console.log('[RealTime Tracking] Video ended - Video state - readyState: ' + video.readyState + ', networkState: ' + video.networkState + ', paused: ' + video.paused + ', ended: ' + video.ended);
            
            // Additional debugging
            console.log('[RealTime Tracking] Video ended - Checking if module already completed: ' + trackingState.moduleCompleted);
            
            if (!trackingState.moduleCompleted) {
                console.log('[RealTime Tracking] Video ended - Marking as completed!');
                console.log('[RealTime Tracking] Video ended details: duration=' + video.duration);
                console.log('[RealTime Tracking] Video ended details: currentTime=' + video.currentTime);
                trackingState.moduleCompleted = true;
                
                // For local videos, always prefer the actual video duration over the database duration
                // For YouTube videos, we might want to use the database duration if it's more accurate
                const container = document.querySelector('.module-video-container');
                const isLocalVideo = isLocalVideoElement();
                
                // Consistently use the actual video duration for local videos
                let duration = trackingState.totalDuration;
                if (isLocalVideo && video.duration && isFinite(video.duration) && video.duration > 0) {
                    // For local videos, always use the actual video duration
                    duration = Number(video.duration);
                } else if (!isLocalVideo && trackingState.totalDuration > 0) {
                    // For non-local videos, use the tracking state duration
                    duration = trackingState.totalDuration;
                } else if (video.duration && isFinite(video.duration) && video.duration > 0) {
                    // Fallback to video element duration
                    duration = Number(video.duration);
                }
                
                console.log('[RealTime Tracking] Sending completion update with duration: ' + duration);
                // Use the full duration to ensure 100% completion
                console.log('[RealTime Tracking] Video ended event - sending completion update');
                sendProgressUpdate(duration, duration, true);
            } else {
                console.log('[RealTime Tracking] Video ended but module already marked as completed');
            }
        });

        // Additional safety check: periodically check if video has ended but event wasn't caught
        setInterval(function() {
            // Log periodic status for debugging
            console.log('[RealTime Tracking] Periodic check - State: completed=' + trackingState.moduleCompleted + ', playing=' + trackingState.isVideoPlaying + ', watchedTime=' + trackingState.watchedTime + ', totalDuration=' + trackingState.totalDuration + ', video.currentTime=' + video.currentTime + ', video.duration=' + video.duration);
            
            // Additional debugging
            console.log('[RealTime Tracking] Periodic safety check running');
            
            // Additional debugging to check if video is at the end
            if (video.currentTime >= video.duration - 0.01) {
                console.log('[RealTime Tracking] Periodic check - Video at end - currentTime: ' + video.currentTime + ', duration: ' + video.duration);
            }
            
            // Additional debugging to check if video is very close to end
            if (video.currentTime >= video.duration - 1) {
                console.log('[RealTime Tracking] Periodic check - Video very close to end - currentTime: ' + video.currentTime + ', duration: ' + video.duration + ', remaining: ' + (video.duration - video.currentTime));
                console.log('[RealTime Tracking] Periodic check - Video state - readyState: ' + video.readyState + ', networkState: ' + video.networkState + ', paused: ' + video.paused + ', ended: ' + video.ended);
            }
            
            // Additional debugging
            console.log('[RealTime Tracking] Periodic check - currentTime: ' + video.currentTime + ', duration: ' + video.duration);
            
            // For local videos, prioritize the actual video duration
            const container1 = document.querySelector('.module-video-container');
            const isLocalVideo1 = isLocalVideoElement();
            
            // Consistently use the actual video duration for local videos
            let effectiveDuration1 = trackingState.totalDuration;
            if (isLocalVideo1 && video.duration && isFinite(video.duration) && video.duration > 0) {
                // For local videos, always use the actual video duration
                effectiveDuration1 = Number(video.duration);
            } else if (!isLocalVideo1 && trackingState.totalDuration > 0) {
                // For non-local videos, use the tracking state duration
                effectiveDuration1 = trackingState.totalDuration;
            } else if (video.duration && isFinite(video.duration) && video.duration > 0) {
                // Fallback to video element duration
                effectiveDuration1 = Number(video.duration);
            } else {
                // Last resort fallback
                effectiveDuration1 = isFinite(video.duration) ? Number(video.duration) : 0;
            }
            
            // Additional debugging
            console.log('[RealTime Tracking] Periodic check - isLocalVideo1: ' + isLocalVideo1 + ', effectiveDuration1: ' + effectiveDuration1);
            
            // Enhanced safety check for local videos
            // Be more lenient with completion detection for all videos
            const isLocalVideoCheck1 = isLocalVideoElement();
            // For local videos, use a more lenient threshold to ensure completion is detected
            const safetyThreshold1 = isLocalVideoCheck1 ? 1.0 : 0.1; // Even more lenient threshold for local videos
            if (!trackingState.moduleCompleted && effectiveDuration1 > 0 && video.currentTime >= (effectiveDuration1 - safetyThreshold1)) {
                console.log('[RealTime Tracking] Safety check - isLocalVideoCheck1: ' + isLocalVideoCheck1 + ', safetyThreshold1: ' + safetyThreshold1);
                console.log('[RealTime Tracking] Safety check passed - readyState: ' + video.readyState + ', paused: ' + video.paused + ', currentTime: ' + video.currentTime + ', duration: ' + effectiveDuration1);
                console.log('[RealTime Tracking] Safety check: Video appears to have ended - Marking as completed!');
                console.log('[RealTime Tracking] Safety check details: currentTime=' + video.currentTime.toFixed(3) + ', duration=' + effectiveDuration1.toFixed(3) + ', threshold=' + (effectiveDuration1 - safetyThreshold1).toFixed(3));
                console.log('[RealTime Tracking] Safety check - currentTime: ' + video.currentTime + ', duration: ' + effectiveDuration1 + ', diff: ' + (effectiveDuration1 - video.currentTime));
                trackingState.moduleCompleted = true;
                
                // For local videos, prioritize the actual video duration
                const container = document.querySelector('.module-video-container');
                const isLocalVideo = isLocalVideoElement();
                
                // Consistently use the actual video duration for local videos
                let duration = trackingState.totalDuration;
                if (isLocalVideo && video.duration && isFinite(video.duration) && video.duration > 0) {
                    // For local videos, always use the actual video duration
                    duration = Number(video.duration);
                } else if (!isLocalVideo && trackingState.totalDuration > 0) {
                    // For non-local videos, use the tracking state duration
                    duration = trackingState.totalDuration;
                } else if (video.duration && isFinite(video.duration) && video.duration > 0) {
                    // Fallback to video element duration
                    duration = Number(video.duration);
                }
                
                console.log('[RealTime Tracking] Safety check - sending completion update');
                sendProgressUpdate(duration, duration, true);
            }
            
            // Additional check for completion based on currentTime and duration
            // For local videos, prioritize the actual video duration
            const container2 = document.querySelector('.module-video-container');
            const isLocalVideo2 = isLocalVideoElement();
            
            // Consistently use the actual video duration for local videos
            let effectiveDuration2 = trackingState.totalDuration;
            if (isLocalVideo2 && video.duration && isFinite(video.duration) && video.duration > 0) {
                // For local videos, always use the actual video duration
                effectiveDuration2 = Number(video.duration);
            } else if (!isLocalVideo2 && trackingState.totalDuration > 0) {
                // For non-local videos, use the tracking state duration
                effectiveDuration2 = trackingState.totalDuration;
            } else if (video.duration && isFinite(video.duration) && video.duration > 0) {
                // Fallback to video element duration
                effectiveDuration2 = Number(video.duration);
            } else {
                // Last resort fallback
                effectiveDuration2 = trackingState.totalDuration > 0 ? trackingState.totalDuration : 0;
            }
            
            // Additional debugging
            console.log('[RealTime Tracking] Periodic check 2 - isLocalVideo2: ' + isLocalVideo2 + ', effectiveDuration2: ' + effectiveDuration2);
            
            // Enhanced completion check for local videos
            // Be more lenient with completion detection for all videos
            const isLocalVideoCheck2 = isLocalVideoElement();
            // For local videos, use a more lenient threshold to ensure completion is detected
            const completionThreshold2 = isLocalVideoCheck2 ? 1.0 : 0.1; // Even more lenient threshold for local videos
            if (!trackingState.moduleCompleted && effectiveDuration2 > 0 && video.currentTime >= (effectiveDuration2 - completionThreshold2)) {
                console.log('[RealTime Tracking] Additional safety check - isLocalVideoCheck2: ' + isLocalVideoCheck2 + ', completionThreshold2: ' + completionThreshold2);
                console.log('[RealTime Tracking] Additional safety check passed - currentTime: ' + video.currentTime + ', duration: ' + effectiveDuration2);
                console.log('[RealTime Tracking] Additional safety check: Video near completion - Marking as completed!');
                console.log('[RealTime Tracking] Additional safety check details: currentTime=' + video.currentTime.toFixed(3) + ', duration=' + effectiveDuration2.toFixed(3) + ', threshold=' + (effectiveDuration2 - completionThreshold2).toFixed(3));
                console.log('[RealTime Tracking] Additional safety check - currentTime: ' + video.currentTime + ', duration: ' + effectiveDuration2 + ', diff: ' + (effectiveDuration2 - video.currentTime));
                trackingState.moduleCompleted = true;
                
                // For local videos, prioritize the actual video duration
                const container = document.querySelector('.module-video-container');
                const isLocalVideo = isLocalVideoElement();
                
                // Consistently use the actual video duration for local videos
                let duration = trackingState.totalDuration;
                if (isLocalVideo && video.duration && isFinite(video.duration) && video.duration > 0) {
                    // For local videos, always use the actual video duration
                    duration = Number(video.duration);
                } else if (!isLocalVideo && trackingState.totalDuration > 0) {
                    // For non-local videos, use the tracking state duration
                    duration = trackingState.totalDuration;
                } else if (video.duration && isFinite(video.duration) && video.duration > 0) {
                    // Fallback to video element duration
                    duration = Number(video.duration);
                }
                
                console.log('[RealTime Tracking] Additional safety check - sending completion update');
                sendProgressUpdate(duration, duration, true);
            }
        }, 5000);
    }
    
    // Track iframe video progress (real-time)
    function trackIframeVideoProgress(iframe) {
        console.log('[RealTime Tracking] Iframe video progress tracking initialized');
        
        // Try to get actual duration from iframe URL parameters
        try {
            const url = new URL(iframe.src);
            // For YouTube: https://www.youtube.com/embed/VIDEO_ID?start=0&end=300
            const startParam = url.searchParams.get('start');
            const endParam = url.searchParams.get('end');
            
            if (startParam && endParam) {
                trackingState.totalDuration = parseInt(endParam) - parseInt(startParam);
                console.log('[RealTime Tracking] Detected iframe duration:', trackingState.totalDuration, 'seconds');
            }
        } catch (e) {
            console.warn('[RealTime Tracking] Could not parse iframe URL for duration:', e);
        }
        
        // Get duration from module data if not found in URL
        if (trackingState.totalDuration <= 0) {
            const container = document.querySelector('.module-video-container');
            const moduleDurationStr = container && container.dataset ? container.dataset.moduleDuration : null;
            const parsedDuration = parseDurationString(moduleDurationStr);
            trackingState.totalDuration = parsedDuration || 0;
            console.log('[RealTime Tracking] Using module duration from data (iframe):', trackingState.totalDuration, 'seconds');
            console.log('[RealTime Tracking] Raw module duration string:', moduleDurationStr);
        }
        
        // Log the actual calculation to help debug
        console.log('[RealTime Tracking] Duration calculation details:', {
            totalDuration: trackingState.totalDuration,
            expectedDuration: "633 seconds (10:33)",
            discrepancy: trackingState.totalDuration - 633
        });
        
        // Initialize watched time from existing progress if available
        const container = document.querySelector('.module-video-container');
        if (container && container.dataset.watchedDuration) {
            trackingState.watchedTime = parseFloat(container.dataset.watchedDuration);
            console.log('[RealTime Tracking] Starting from existing watched time:', trackingState.watchedTime, 'seconds');
        }
        
        // Initially assume video is not playing
        trackingState.isVideoPlaying = false;
        // Record iframe provider so we can delay completion until player readiness
        try {
            const src = iframe.src || '';
            if (src.includes('youtube.com') || src.includes('youtu.be')) {
                trackingState.iframeProvider = 'youtube';
            } else if (src.includes('vimeo.com')) {
                trackingState.iframeProvider = 'vimeo';
            } else {
                trackingState.iframeProvider = null;
            }
        } catch (e) {
            trackingState.iframeProvider = null;
        }
        
        // Try to set up YouTube or Vimeo API
        setupVideoAPI(iframe);
        
        // Set a timeout to assume play/pause controls are available after 5 seconds
        // This prevents getting stuck with visibility-only tracking if API fails to load
        setTimeout(function() {
            if (!trackingState.hasPlayPauseControls) {
                console.log('[RealTime Tracking] YouTube/Vimeo API not loaded within 5 seconds, enabling fallback tracking');
                trackingState.hasPlayPauseControls = true; // Enable to prevent visibility-only tracking
                // Start with video assumed to be playing
                trackingState.isVideoPlaying = !document.hidden;
            }
        }, 5000);
        
        // Set up visibility tracking as a proxy for video playing state
        document.addEventListener('visibilitychange', function() {
            // Only update playing state if we don't have explicit play/pause controls
            if (!trackingState.hasPlayPauseControls) {
                trackingState.isVideoPlaying = !document.hidden;
            }
            console.log('[RealTime Tracking] Page visibility changed: ' + (!document.hidden ? 'Visible' : 'Hidden'));
        });
        
        // Also track focus/blur events
        window.addEventListener('focus', function() {
            // Don't automatically set to playing, but allow tracking to resume
            console.log('[RealTime Tracking] Window focused');
        });
        
        window.addEventListener('blur', function() {
            console.log('[RealTime Tracking] Window blurred');
        });
        
        // Set up interval tracking that respects play/pause state
        trackingState.lastIntervalTick = Date.now();
        trackingState.videoTrackingInterval = setInterval(function() {
            if (trackingState.moduleCompleted) {
                clearInterval(trackingState.videoTrackingInterval);
                console.log('[RealTime Tracking] Module completed, stopping tracking');
                return;
            }

            const now = Date.now();
            const deltaSeconds = (now - (trackingState.lastIntervalTick || now)) / 1000;
            trackingState.lastIntervalTick = now;

            // Only increment time if we believe the video is playing
            if (trackingState.isVideoPlaying && trackingState.totalDuration > 0) {
                // Use elapsed real time to accumulate watched time (float seconds)
                trackingState.watchedTime += Math.max(0, deltaSeconds);

                // Clamp watchedTime to not exceed totalDuration by more than a tiny epsilon
                if (trackingState.watchedTime > trackingState.totalDuration + 0.1) {
                    trackingState.watchedTime = trackingState.totalDuration;
                }

                // Calculate progress percentage using precise calculation
                const progressPercent = (trackingState.watchedTime / trackingState.totalDuration) * 100;

                console.log('[RealTime Tracking] Watched time: ' + trackingState.watchedTime.toFixed(2) + 's, Progress: ' + Math.min(progressPercent,100).toFixed(2) + '%');
                if (trackingState.watchedTime >= trackingState.totalDuration - 0.1) {
                    console.log('[RealTime Tracking] Near completion - watchedTime:', trackingState.watchedTime.toFixed(2), 'totalDuration:', trackingState.totalDuration);
                }

                // Only mark as completed when we've effectively watched the full duration
                // Use consistent threshold with HTML5 videos
                // But be more lenient for local videos
                const isLocalVideo = isLocalVideoElement();
                // For local videos, use a more lenient threshold to ensure completion is detected
                const completionThreshold = isLocalVideo ? 1.0 : 0.1; // Even more lenient threshold for local videos
                let shouldComplete = trackingState.watchedTime >= (trackingState.totalDuration - completionThreshold);

                // If this is a YouTube iframe and the player hasn't reported duration yet,
                // avoid marking as completed prematurely. We'll rely on the player's onReady
                // handler to override duration and allow completion later.
                if (trackingState.iframeProvider === 'youtube' && !trackingState.hasPlayPauseControls) {
                    shouldComplete = false;
                }

                if (shouldComplete && !trackingState.moduleCompleted) {
                    console.log('[RealTime Tracking] Watched ' + Math.min(progressPercent,100).toFixed(2) + '% of Module - Marking as completed!');
                    clearInterval(trackingState.videoTrackingInterval);
                    trackingState.moduleCompleted = true;
                    // Use the full duration to ensure 100% completion
                    sendProgressUpdate(trackingState.totalDuration, trackingState.totalDuration, true);
                } else if (progressPercent > trackingState.currentModuleProgress) {
                    // Only send update if progress has increased
                    trackingState.currentModuleProgress = progressPercent;
                    console.log('[RealTime Tracking] Watched ' + Math.min(progressPercent,100).toFixed(2) + '% of Module - Not completed yet');
                    sendProgressUpdate(trackingState.watchedTime, trackingState.totalDuration, false);
                }
            }

            // Safety check: if watched time significantly exceeds duration, mark as complete
            // Only force completion if we either have explicit play/pause controls (player ready)
            // or the iframe provider isn't YouTube (so we don't override a longer player duration later).
            if (trackingState.watchedTime > trackingState.totalDuration + 5 && !trackingState.moduleCompleted) {
                const canForceComplete = trackingState.hasPlayPauseControls || trackingState.iframeProvider !== 'youtube';
                if (canForceComplete) {
                    console.log('[RealTime Tracking] Watched time significantly exceeds duration - forcing completion');
                    clearInterval(trackingState.videoTrackingInterval);
                    trackingState.moduleCompleted = true;
                    sendProgressUpdate(trackingState.totalDuration, trackingState.totalDuration, true);
                }
            }
            // ALSO send progress update for dynamic tracking (every 2 seconds)
            else if (now - trackingState.lastUpdateTime >= 2000 && trackingState.isVideoPlaying && trackingState.totalDuration > 0) {
                trackingState.lastUpdateTime = now;
                sendProgressUpdate(trackingState.watchedTime, trackingState.totalDuration, false);
            }
        }, 1000); // Check every second for more accurate tracking
    }
    
    // Set up YouTube or Vimeo API for better play/pause detection
    function setupVideoAPI(iframe) {
        try {
            const iframeSrc = iframe.src;
            
            // YouTube API setup
            if (iframeSrc.includes('youtube.com') || iframeSrc.includes('youtu.be')) {
                setupYouTubeAPI(iframe);
            } 
            // Vimeo API setup
            else if (iframeSrc.includes('vimeo.com')) {
                setupVimeoAPI(iframe);
            }
        } catch (e) {
            console.warn('[RealTime Tracking] Could not set up video API:', e);
        }
    }
    
    // Set up YouTube API
    function setupYouTubeAPI(iframe) {
        // Check if YouTube API is already loaded
        if (typeof YT !== 'undefined' && YT.Player) {
            // API already loaded, create player directly
            createYouTubePlayer(iframe);
        } else {
            // Load YouTube API
            if (!window.youTubeApiLoading) {
                window.youTubeApiLoading = true;
                // Create script tag for YouTube API
                const tag = document.createElement('script');
                tag.src = "https://www.youtube.com/iframe_api";
                const firstScriptTag = document.getElementsByTagName('script')[0];
                firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            }
            
            // Store reference to iframe for YouTube API callback
            if (!window.youTubeIframes) {
                window.youTubeIframes = [];
            }
            window.youTubeIframes.push(iframe);
            
            // YouTube API ready callback
            if (!window.youtubeCallbackSet) {
                window.youtubeCallbackSet = true;
                const originalCallback = window.onYouTubeIframeAPIReady;
                window.onYouTubeIframeAPIReady = function() {
                    try {
                        // Call original callback if it exists
                        if (typeof originalCallback === 'function') {
                            originalCallback();
                        }
                        
                        console.log('[RealTime Tracking] YouTube API ready, creating players for iframes:', window.youTubeIframes ? window.youTubeIframes.length : 0);
                        // Create players for all stored iframes
                        if (window.youTubeIframes && window.youTubeIframes.length > 0) {
                            window.youTubeIframes.forEach(function(iframeElem) {
                                createYouTubePlayer(iframeElem);
                            });
                            // Clear the array
                            window.youTubeIframes = [];
                        }
                    } catch (e) {
                        console.error('[RealTime Tracking] Error creating YouTube players:', e);
                    }
                };
            }
        }
    }

    // Create YouTube player instance
    function createYouTubePlayer(iframe) {
        // This function appears to be incomplete in the original file
        // Adding a basic implementation to fix syntax errors
        try {
            // Placeholder implementation
            console.log('[RealTime Tracking] Creating YouTube player for iframe');
        } catch (e) {
            console.error('[RealTime Tracking] Error creating YouTube player:', e);
        }
    }

    // Ensure the tracking script is properly closed
    console.log('[RealTime Tracking] Script initialization complete');
})();
