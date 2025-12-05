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
        
        // Fallback to URL-based detection
        const container = document.querySelector('.module-video-container');
        if (!container || !container.dataset || !container.dataset.moduleVideoUrl) {
            return false;
        }
        
        const videoUrl = container.dataset.moduleVideoUrl;
        console.log('[RealTime Tracking] Checking if video is local. URL:', videoUrl);
        
        // Local videos are those that:
        // 1. Start with 'attached_assets/videos/' or 'uploads/'
        // 2. Don't contain '://' (not a full URL)
        // 3. Don't contain '/' but also don't contain '://' (e.g., just 'Video.mp4')
        const isLocal = videoUrl.startsWith('attached_assets/videos/') || 
               videoUrl.startsWith('uploads/') || 
               (videoUrl.includes('/') === false && videoUrl.includes('://') === false) ||
               (videoUrl.includes('://') === false && videoUrl.includes('/') === false);
               
        console.log('[RealTime Tracking] Is local video (URL-based):', isLocal);
        return isLocal;
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
        
        console.log([RealTime Tracking] Course ID: ${trackingState.courseId}, Module ID: ${trackingState.moduleId});
        
        if (!trackingState.courseId || !trackingState.moduleId) {
            console.error('[RealTime Tracking] Missing course or module ID');
            return;
        }
        
        // Check if module is already completed - if so, don't start tracking
        const isModuleCompleted = container.dataset.moduleCompleted === 'true';
        console.log([RealTime Tracking] Module completed status: ${isModuleCompleted});
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
                const moduleElement = document.querySelector(.list-group-item[data-module-id="${moduleId}"]);
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
        console.log([RealTime Tracking] Module duration string: ${moduleDurationStr}, parsed: ${parsedDuration});

        // If video element reports a duration, prefer it (especially for local videos)
        let playerDuration = 0;
        if (video && typeof video.duration === 'number' && isFinite(video.duration) && video.duration > 0) {
            playerDuration = Number(video.duration);
        }
        
        // Additional debugging
        console.log([RealTime Tracking] Player duration: ${playerDuration});

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
        console.log([RealTime Tracking] Total duration set to: ${trackingState.totalDuration});

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
            console.log([RealTime Tracking] Fallback - Final duration: ${trackingState.totalDuration});
        }, 3000);
        
        // Update UI immediately on video load
        video.addEventListener('loadedmetadata', function() {
            console.log('[RealTime Tracking] Video loaded - Duration:', video.duration, 'seconds');
            console.log('[RealTime Tracking] Video loaded - readyState:', video.readyState, 'networkState:', video.networkState);
            
            // Additional debugging for buffering info
            if (video.buffered && video.buffered.length > 0) {
                console.log('[RealTime Tracking] Video buffered ranges:', video.buffered.length);
                for (let i = 0; i < video.buffered.length; i++) {
                    console.log([RealTime Tracking] Buffered range ${i}: ${video.buffered.start(i)} - ${video.buffered.end(i)});
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
                console.log([RealTime Tracking] Metadata loaded - actualDuration: ${actualDuration}, trackingState.totalDuration: ${trackingState.totalDuration});
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
                console.log([RealTime Tracking] Local video duration set: ${trackingState.totalDuration});
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
            console.log([RealTime Tracking] Timeupdate - isVideoPlaying: ${trackingState.isVideoPlaying}, moduleCompleted: ${trackingState.moduleCompleted});
            console.log([RealTime Tracking] Timeupdate - playbackRate: ${video.playbackRate}, defaultPlaybackRate: ${video.defaultPlaybackRate});
            console.log([RealTime Tracking] Timeupdate - volume: ${video.volume}, muted: ${video.muted});
            console.log([RealTime Tracking] Timeupdate - loop: ${video.loop});
            console.log([RealTime Tracking] Timeupdate - controls: ${video.controls});
            console.log([RealTime Tracking] Timeupdate - preload: ${video.preload});
            console.log([RealTime Tracking] Timeupdate - autoplay: ${video.autoplay});
            console.log([RealTime Tracking] Timeupdate - poster: ${video.poster});
            console.log([RealTime Tracking] Timeupdate - crossOrigin: ${video.crossOrigin});
            console.log([RealTime Tracking] Timeupdate - currentSrc: ${video.currentSrc});
            console.log([RealTime Tracking] Timeupdate - seeking: ${video.seeking});
            console.log([RealTime Tracking] Timeupdate - paused: ${video.paused});
            console.log([RealTime Tracking] Timeupdate - ended: ${video.ended});
            console.log([RealTime Tracking] Timeupdate - networkState: ${video.networkState});
            console.log([RealTime Tracking] Timeupdate - readyState: ${video.readyState});
            console.log([RealTime Tracking] Timeupdate - error: ${video.error});
            console.log([RealTime Tracking] Timeupdate - disableRemotePlayback: ${video.disableRemotePlayback});
            console.log([RealTime Tracking] Timeupdate - playsInline: ${video.playsInline});
            console.log([RealTime Tracking] Timeupdate - mediaKeys: ${video.mediaKeys});
            console.log([RealTime Tracking] Timeupdate - remote: ${video.remote});
            console.log([RealTime Tracking] Timeupdate - sinkId: ${video.sinkId});
            console.log([RealTime Tracking] Timeupdate - audioTracks: ${video.audioTracks});
            console.log([RealTime Tracking] Timeupdate - videoTracks: ${video.videoTracks});
            console.log([RealTime Tracking] Timeupdate - textTracks: ${video.textTracks});
            console.log([RealTime Tracking] Timeupdate - controller: ${video.controller});
            console.log([RealTime Tracking] Timeupdate - defaultMuted: ${video.defaultMuted});
            console.log([RealTime Tracking] Timeupdate - defaultPlaybackRate: ${video.defaultPlaybackRate});
            console.log([RealTime Tracking] Timeupdate - disablePictureInPicture: ${video.disablePictureInPicture});
            console.log([RealTime Tracking] Timeupdate - controlsList: ${video.controlsList});
            console.log([RealTime Tracking] Timeupdate - mediaKeys: ${video.mediaKeys});
            console.log([RealTime Tracking] Timeupdate - remote: ${video.remote});
            console.log([RealTime Tracking] Timeupdate - srcObject: ${video.srcObject});
            
            // Additional debugging for buffering info
            if (video.buffered && video.buffered.length > 0) {
                let bufferedInfo = '';
                for (let i = 0; i < video.buffered.length; i++) {
                    bufferedInfo += `Range ${i}: ${video.buffered.start(i)}-${video.buffered.end(i)} `;
                }
                console.log([RealTime Tracking] Video buffered ranges: ${bufferedInfo});
                
                // Check if we're trying to play beyond buffered content
                let isBeyondBuffer = true;
                for (let i = 0; i < video.buffered.length; i++) {
                    if (video.currentTime >= video.buffered.start(i) && video.currentTime <= video.buffered.end(i)) {
                        isBeyondBuffer = false;
                        break;
                    }
                }
                if (isBeyondBuffer) {
                    console.log([RealTime Tracking] Warning: Playing beyond buffered content - currentTime: ${video.currentTime});
                }
            }
            
            // Additional debugging to check if video is at the end
            if (video.currentTime >= video.duration - 0.01) {
                console.log([RealTime Tracking] Video at end - currentTime: ${video.currentTime}, duration: ${video.duration});
            }
            
            // Additional debugging
            if (video.currentTime >= video.duration - 0.1) {
                console.log([RealTime Tracking] Timeupdate near end - currentTime: ${video.currentTime}, duration: ${video.duration});
            }
            
            // Additional debugging to check if video is very close to end
            if (video.currentTime >= video.duration - 1) {
                console.log([RealTime Tracking] Video very close to end - currentTime: ${video.currentTime}, duration: ${video.duration}, remaining: ${video.duration - video.currentTime});
                console.log([RealTime Tracking] Video state - readyState: ${video.readyState}, networkState: ${video.networkState}, paused: ${video.paused}, ended: ${video.ended});
            }
            
            // Additional debugging to check if video has stopped progressing
            if (trackingState.lastVideoTime !== undefined && video.currentTime === trackingState.lastVideoTime) {
                console.log([RealTime Tracking] Video time not progressing - currentTime: ${video.currentTime}, lastTime: ${trackingState.lastVideoTime});
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
            console.log([RealTime Tracking] Duration check - duration: ${duration}, isLocalVideo: ${isLocalVideo});
            
            // Additional debugging to check if video is at the end
            if (duration > 0 && currentTime >= duration - 0.1) {
                console.log([RealTime Tracking] Video near end - currentTime: ${currentTime.toFixed(3)}, duration: ${duration.toFixed(3)}, diff: ${(duration - currentTime).toFixed(3)});
            }

            // Log progress for debugging
            if (duration > 0) {
                const progressPercent = (currentTime / duration) * 100;
                console.log([RealTime Tracking] Progress: ${progressPercent.toFixed(2)}% (Current: ${currentTime.toFixed(2)}s, Duration: ${duration.toFixed(2)}s));
                
                // Additional debugging for near completion
                if (currentTime >= duration - 1) {
                    console.log([RealTime Tracking] Near completion - Current: ${currentTime.toFixed(3)}s, Duration: ${duration.toFixed(3)}s, Difference: ${(duration - currentTime).toFixed(3)}s);
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
                    console.log([RealTime Tracking] Completion check - shouldComplete: ${shouldComplete}, currentTime: ${currentTime}, duration: ${duration}, threshold: ${completionThreshold});
                    
                    // Add debugging for completion detection
                    if (duration > 0) {
                        console.log([RealTime Tracking] Completion check: currentTime=${currentTime.toFixed(3)}, duration=${duration.toFixed(3)}, threshold=${(duration - completionThreshold).toFixed(3)}, shouldComplete=${shouldComplete}, moduleCompleted=${trackingState.moduleCompleted});
                    }

                    if (shouldComplete && !trackingState.moduleCompleted) {
                        console.log([RealTime Tracking] Watched ${Math.min(progressPercent, 100).toFixed(2)}% of module - Marking as completed!);
                        console.log([RealTime Tracking] Completion details: currentTime=${currentTime}, duration=${duration}, shouldComplete=${shouldComplete});
                        console.log([RealTime Tracking] Completion check - currentTime: ${currentTime}, duration: ${duration}, diff: ${duration - currentTime});
                        trackingState.moduleCompleted = true;
                        // Use the full duration to ensure 100% completion
                        console.log('[RealTime Tracking] Sending completion update with duration:', duration);
                        sendProgressUpdate(duration, duration, true);
                    } else if (!trackingState.moduleCompleted) {
                        console.log([RealTime Tracking] Watched ${Math.min(progressPercent, 100).toFixed(2)}% of module - Not completed yet);
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
            console.log([RealTime Tracking] Video ended - currentTime: ${video.currentTime}, duration: ${video.duration});
            console.log([RealTime Tracking] Video ended - Video state - readyState: ${video.readyState}, networkState: ${video.networkState}, paused: ${video.paused}, ended: ${video.ended});
            
            // Additional debugging
            console.log([RealTime Tracking] Video ended - Checking if module already completed: ${trackingState.moduleCompleted});
            
            if (!trackingState.moduleCompleted) {
                console.log('[RealTime Tracking] Video ended - Marking as completed!');
                console.log([RealTime Tracking] Video ended details: duration=${video.duration});
                console.log([RealTime Tracking] Video ended details: currentTime=${video.currentTime});
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
                
                console.log([RealTime Tracking] Sending completion update with duration: ${duration});
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
            console.log([RealTime Tracking] Periodic check - State: completed=${trackingState.moduleCompleted}, playing=${trackingState.isVideoPlaying}, watchedTime=${trackingState.watchedTime}, totalDuration=${trackingState.totalDuration}, video.currentTime=${video.currentTime}, video.duration=${video.duration});
            
            // Additional debugging
            console.log('[RealTime Tracking] Periodic safety check running');
            
            // Additional debugging to check if video is at the end
            if (video.currentTime >= video.duration - 0.01) {
                console.log([RealTime Tracking] Periodic check - Video at end - currentTime: ${video.currentTime}, duration: ${video.duration});
            }
            
            // Additional debugging to check if video is very close to end
            if (video.currentTime >= video.duration - 1) {
                console.log([RealTime Tracking] Periodic check - Video very close to end - currentTime: ${video.currentTime}, duration: ${video.duration}, remaining: ${video.duration - video.currentTime});
                console.log([RealTime Tracking] Periodic check - Video state - readyState: ${video.readyState}, networkState: ${video.networkState}, paused: ${video.paused}, ended: ${video.ended});
            }
            
            // Additional debugging
            console.log([RealTime Tracking] Periodic check - currentTime: ${video.currentTime}, duration: ${video.duration});
            
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
            console.log([RealTime Tracking] Periodic check - isLocalVideo1: ${isLocalVideo1}, effectiveDuration1: ${effectiveDuration1});
            
            // Enhanced safety check for local videos
            // Be more lenient with completion detection for all videos
            const isLocalVideoCheck1 = isLocalVideoElement();
            // For local videos, use a more lenient threshold to ensure completion is detected
            const safetyThreshold1 = isLocalVideoCheck1 ? 1.0 : 0.1; // Even more lenient threshold for local videos
            if (!trackingState.moduleCompleted && effectiveDuration1 > 0 && video.currentTime >= (effectiveDuration1 - safetyThreshold1)) {
                console.log([RealTime Tracking] Safety check - isLocalVideoCheck1: ${isLocalVideoCheck1}, safetyThreshold1: ${safetyThreshold1});
                console.log([RealTime Tracking] Safety check passed - readyState: ${video.readyState}, paused: ${video.paused}, currentTime: ${video.currentTime}, duration: ${effectiveDuration1});
                console.log('[RealTime Tracking] Safety check: Video appears to have ended - Marking as completed!');
                console.log([RealTime Tracking] Safety check details: currentTime=${video.currentTime.toFixed(3)}, duration=${effectiveDuration1.toFixed(3)}, threshold=${(effectiveDuration1 - safetyThreshold1).toFixed(3)});
                console.log([RealTime Tracking] Safety check - currentTime: ${video.currentTime}, duration: ${effectiveDuration1}, diff: ${effectiveDuration1 - video.currentTime});
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
            console.log([RealTime Tracking] Periodic check 2 - isLocalVideo2: ${isLocalVideo2}, effectiveDuration2: ${effectiveDuration2});
            
            // Enhanced completion check for local videos
            // Be more lenient with completion detection for all videos
            const isLocalVideoCheck2 = isLocalVideoElement();
            // For local videos, use a more lenient threshold to ensure completion is detected
            const completionThreshold2 = isLocalVideoCheck2 ? 1.0 : 0.1; // Even more lenient threshold for local videos
            if (!trackingState.moduleCompleted && effectiveDuration2 > 0 && video.currentTime >= (effectiveDuration2 - completionThreshold2)) {
                console.log([RealTime Tracking] Additional safety check - isLocalVideoCheck2: ${isLocalVideoCheck2}, completionThreshold2: ${completionThreshold2});
                console.log([RealTime Tracking] Additional safety check passed - currentTime: ${video.currentTime}, duration: ${effectiveDuration2});
                console.log('[RealTime Tracking] Additional safety check: Video near completion - Marking as completed!');
                console.log([RealTime Tracking] Additional safety check details: currentTime=${video.currentTime.toFixed(3)}, duration=${effectiveDuration2.toFixed(3)}, threshold=${(effectiveDuration2 - completionThreshold2).toFixed(3)});
                console.log([RealTime Tracking] Additional safety check - currentTime: ${video.currentTime}, duration: ${effectiveDuration2}, diff: ${effectiveDuration2 - video.currentTime});
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
            console.log([RealTime Tracking] Page visibility changed: ${!document.hidden ? 'Visible' : 'Hidden'});
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

                console.log([RealTime Tracking] Watched time: ${trackingState.watchedTime.toFixed(2)}s, Progress: ${Math.min(progressPercent,100).toFixed(2)}%);
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
                    console.log([RealTime Tracking] Watched ${Math.min(progressPercent,100).toFixed(2)}% of Module - Marking as completed!);
                    clearInterval(trackingState.videoTrackingInterval);
                    trackingState.moduleCompleted = true;
                    // Use the full duration to ensure 100% completion
                    sendProgressUpdate(trackingState.totalDuration, trackingState.totalDuration, true);
                } else if (progressPercent > trackingState.currentModuleProgress) {
                    // Only send update if progress has increased
                    trackingState.currentModuleProgress = progressPercent;
                    console.log([RealTime Tracking] Watched ${Math.min(progressPercent,100).toFixed(2)}% of Module - Not completed yet);
                    sendProgressUpdate(trackingState.watchedTime, trackingState.totalDuration, false);
                }
            }

            // Safety check: if watched time significantly exceeds duration, mark as complete
            // Only force completion if we either have explicit play/pause controls (player ready)
            // or the iframe provider isn't YouTube (so we don't override a longer player duration later).
            if (trackingState.watchedTime > trackingState.totalDuration + 5 && !trackingState.moduleCompleted) {
                const canForceComplete = trackingState.hasPlayPauseControls || trackingState.iframeProvider !== 'youtube';
                if (canForceComplete) {
                    console.log([RealTime Tracking] Watched time significantly exceeds duration - forcing completion);
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
        try {
            const playerId = 'youtube-player-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
            iframe.id = playerId;
            
            new YT.Player(playerId, {
                events: {
                    'onReady': function(event) {
                        console.log('[RealTime Tracking] YouTube player ready for iframe:', iframe);
                        trackingState.hasPlayPauseControls = true;

                        // When the player is ready, prefer its reported duration over metadata.
                        // Read metadata duration from container (if any)
                        try {
                            const container = document.querySelector('.module-video-container');
                            const moduleDurationStr = container && container.dataset ? container.dataset.moduleDuration : null;
                            const metadataDuration = (typeof parseDurationString === 'function') ? parseDurationString(moduleDurationStr) : 0;

                            const player = event.target;

                            const applyPlayerDuration = () => {
                                try {
                                    if (!player || typeof player.getDuration !== 'function') return false;
                                    let playerDuration = Number(player.getDuration());
                                    if (!isFinite(playerDuration) || playerDuration <= 0) return false;

                                    // Parse start/end/time params from iframe.src to compute effective playable duration
                                    const urlSrc = (iframe && iframe.src) ? iframe.src : null;
                                    const { start, end } = extractStartEndFromUrl(urlSrc);

                                    // Compute effective duration: respect start/end if present
                                    let effectiveDuration = playerDuration;
                                    if (end !== null) {
                                        effectiveDuration = Math.max(0, Math.min(playerDuration, end) - (start || 0));
                                    } else if (start && start > 0) {
                                        effectiveDuration = Math.max(0, playerDuration - start);
                                    }

                                    // Fallback: if computed effectiveDuration is zero or invalid, use playerDuration
                                    if (!isFinite(effectiveDuration) || effectiveDuration <= 0) {
                                        effectiveDuration = playerDuration;
                                    }

                                    const currentTotal = Number(trackingState.totalDuration) || 0;
                                    const epsilon = 0.5; // small tolerance

                                    // Replace if effective duration is meaningfully different or metadata missing
                                    if (effectiveDuration > (currentTotal + epsilon) || currentTotal <= 0) {
                                        trackingState.totalDuration = effectiveDuration;
                                        console.log('[RealTime Tracking] Overriding module duration using YouTube player.getDuration() (effective):', effectiveDuration, 'seconds (player:', playerDuration, 'metadata:', metadataDuration, 'start:', start, 'end:', end, ')');

                                        // Clamp watchedTime to not exceed new duration
                                        if (trackingState.watchedTime > trackingState.totalDuration + epsilon) {
                                            trackingState.watchedTime = trackingState.totalDuration;
                                        }
                                    }
                                    return true;
                                } catch (err) {
                                    console.warn('[RealTime Tracking] Error applying YouTube player duration:', err);
                                    return false;
                                }
                            };

                            // Try to apply player duration immediately
                            const applied = applyPlayerDuration();

                            // Retry after a short delay to handle async loading
                            if (!applied) {
                                setTimeout(applyPlayerDuration, 1000);
                            }

                        } catch (metaErr) {
                            console.warn('[RealTime Tracking] Error reading metadata duration:', metaErr);
                        }
                    },
                    'onStateChange': function(event) {
                        // YouTube player states:
                        // -1 = unstarted, 0 = ended, 1 = playing, 2 = paused, 3 = buffering, 5 = video cued
                        if (event.data === YT.PlayerState.PLAYING) {
                            trackingState.isVideoPlaying = true;
                            console.log('[RealTime Tracking] YouTube video playing');
                        } else if (event.data === YT.PlayerState.PAUSED || event.data === YT.PlayerState.ENDED) {
                            trackingState.isVideoPlaying = false;
                            console.log('[RealTime Tracking] YouTube video paused/stopped, state:', event.data);
                            
                            // If video ended, mark as completed
                            if (event.data === YT.PlayerState.ENDED && !trackingState.moduleCompleted) {
                                console.log('[RealTime Tracking] YouTube video ended - Marking as completed!');
                                trackingState.moduleCompleted = true;
                                
                                // Use the full duration to ensure 100% completion
                                sendProgressUpdate(trackingState.totalDuration, trackingState.totalDuration, true);
                            }
                        }
                        
                        // NEW CODE FOR YOUTUBE SEEK - Check for seek events when state changes
                        if (playerInstance && typeof playerInstance.getCurrentTime === 'function') {
                            const currentTime = playerInstance.getCurrentTime();
                            
                            // Detect forward seeks (when user jumps ahead more than 2 seconds)
                            if (currentTime > previousTime + 2) {
                                console.log('[RealTime Tracking] YouTube video seek detected - jumped from', previousTime, 'to', currentTime);
                                
                                // Update watched time to reflect the seek
                                trackingState.watchedTime = currentTime;
                                
                                // Send progress update immediately to reflect the seek
                                if (trackingState.totalDuration > 0) {
                                    sendProgressUpdate(trackingState.watchedTime, trackingState.totalDuration, false);
                                }
                            }
                            
                            previousTime = currentTime;
                        }
                    }
                }
            });
            
            // NEW CODE FOR YOUTUBE SEEK - Poll for time changes to detect seeks
            // This is needed because YouTube API doesn't have a dedicated seek event
            if (playerInstance) {
                const seekPollingInterval = setInterval(function() {
                    if (playerInstance && typeof playerInstance.getCurrentTime === 'function' && 
                        playerInstance.getPlayerState && playerInstance.getPlayerState() === YT.PlayerState.PLAYING) {
                        
                        const currentTime = playerInstance.getCurrentTime();
                        
                        // Detect forward seeks (when user jumps ahead more than 2 seconds)
                        if (currentTime > previousTime + 2) {
                            console.log('[RealTime Tracking] YouTube video seek detected via polling - jumped from', previousTime, 'to', currentTime);
                            
                            // Update watched time to reflect the seek
                            trackingState.watchedTime = currentTime;
                            
                            // Send progress update immediately to reflect the seek
                            if (trackingState.totalDuration > 0) {
                                sendProgressUpdate(trackingState.watchedTime, trackingState.totalDuration, false);
                            }
                        }
                        
                        previousTime = currentTime;
                    }
                }, 1000); // Check every second
                
                // Clean up interval when module is completed
                const originalModuleCompleted = trackingState.moduleCompleted;
                const checkCompletionInterval = setInterval(function() {
                    if (trackingState.moduleCompleted && !originalModuleCompleted) {
                        clearInterval(seekPollingInterval);
                        clearInterval(checkCompletionInterval);
                    }
                }, 1000);
            }
        } catch (e) {
            console.error('[RealTime Tracking] Error creating YouTube player:', e);
        }
    }

    // Set up Vimeo API
    function setupVimeoAPI(iframe) {
        try {
            // Load Vimeo API if not already loaded
            if (!window.Vimeo) {
                const script = document.createElement('script');
                script.src = 'https://player.vimeo.com/api/player.js';
                script.onload = function() {
                    createVimeoPlayer(iframe);
                };
                document.head.appendChild(script);
            } else {
                createVimeoPlayer(iframe);
            }
        } catch (e) {
            console.error('[RealTime Tracking] Error setting up Vimeo API:', e);
        }
    }
    
    // Create Vimeo player instance
    function createVimeoPlayer(iframe) {
        try {
            const player = new Vimeo.Player(iframe);
            
            player.on('play', function() {
                trackingState.isVideoPlaying = true;
                trackingState.hasPlayPauseControls = true;
                console.log('[RealTime Tracking] Vimeo video playing');
            });
            
            player.on('pause', function() {
                trackingState.isVideoPlaying = false;
                console.log('[RealTime Tracking] Vimeo video paused');
            });
            
            player.on('ended', function() {
                trackingState.isVideoPlaying = false;
                if (!trackingState.moduleCompleted) {
                    console.log('[RealTime Tracking] Vimeo video ended - Marking as completed!');
                    trackingState.moduleCompleted = true;
                    sendProgressUpdate(trackingState.totalDuration, trackingState.totalDuration, true);
                }
            });
            
            // Get video duration
            player.getDuration().then(function(duration) {
                if (isFinite(duration) && duration > 0) {
                    const currentTotal = Number(trackingState.totalDuration) || 0;
                    const epsilon = 0.5;
                    
                    // Replace if Vimeo duration is meaningfully different or metadata missing
                    if (duration > (currentTotal + epsilon) || currentTotal <= 0) {
                        trackingState.totalDuration = duration;
                        console.log('[RealTime Tracking] Overriding module duration using Vimeo player.getDuration():', duration, 'seconds');
                        
                        // Clamp watchedTime to not exceed new duration
                        if (trackingState.watchedTime > trackingState.totalDuration + epsilon) {
                            trackingState.watchedTime = trackingState.totalDuration;
                        }
                    }
                }
            }).catch(function(error) {
                console.warn('[RealTime Tracking] Could not get Vimeo video duration:', error);
            });
            
        } catch (e) {
            console.error('[RealTime Tracking] Error creating Vimeo player:', e);
        }
    }

    // Send progress update to server
    function sendProgressUpdate(watchedDuration, totalDuration, isCompleted = false) {
        // Validate required data
        if (!trackingState.courseId || !trackingState.moduleId) {
            console.error('[RealTime Tracking] Missing course or module ID');
            return;
        }
        
        // Additional debugging
        console.log([RealTime Tracking] sendProgressUpdate called - watchedDuration: ${watchedDuration}, totalDuration: ${totalDuration}, isCompleted: ${isCompleted});
        
        // Calculate progress percentage using precise calculation
        const progressPercent = totalDuration > 0 ? (watchedDuration / totalDuration) * 100 : 0;
        
        // For local videos, ensure we properly handle completion when watched duration equals or exceeds total duration
        // Be more lenient with local video completion detection
        const isLocalVideo = isLocalVideoElement();
        // For local videos, use a more lenient threshold to ensure completion is detected
        const completionThreshold = isLocalVideo ? 1.0 : 0.1; // Even more lenient threshold for local videos
        const isActuallyCompleted = isCompleted || (totalDuration > 0 && watchedDuration >= (totalDuration - completionThreshold));
        
        // Additional debugging
        console.log([RealTime Tracking] sendProgressUpdate - watchedDuration: ${watchedDuration}, totalDuration: ${totalDuration}, isCompleted: ${isCompleted}, isActuallyCompleted: ${isActuallyCompleted});
        
        // Additional debugging
        console.log([RealTime Tracking] Completion calculation - totalDuration: ${totalDuration}, watchedDuration: ${watchedDuration}, completionThreshold: ${completionThreshold});
        
        // Add debugging for completion status
        console.log([RealTime Tracking] Completion status - isCompleted param: ${isCompleted}, isActuallyCompleted: ${isActuallyCompleted}, watchedDuration: ${watchedDuration}, totalDuration: ${totalDuration});

        // Avoid sending duplicate updates - use both percent and watched-time checks.
        // For long videos a 1-second watched change may be a very small percent; ensure we still send updates.
        if (!isActuallyCompleted) {
            const minPercentDelta = 0.1; // smaller percent threshold for responsiveness on long videos
            const minSecondsDelta = 1.0; // send at least when watched time increased by ~1 second

            const secondsDelta = Math.abs(watchedDuration - (trackingState.lastSentWatchedTime || 0));
            const percentDelta = Math.abs(progressPercent - trackingState.lastSentProgress);

            if (percentDelta < minPercentDelta && secondsDelta < minSecondsDelta) {
                return;
            }
        }

        // Update last-sent trackers
        trackingState.lastSentProgress = progressPercent;
        trackingState.lastSentWatchedTime = watchedDuration;
        
        // Ensure proper data types
        const requestData = {
            course_id: parseInt(trackingState.courseId, 10),
            module_id: parseInt(trackingState.moduleId, 10),
            watched_duration: parseFloat(watchedDuration),
            total_duration: parseFloat(totalDuration) || 0,
            provider: trackingState.iframeProvider || null,
            is_completed: Boolean(isActuallyCompleted || isCompleted)
        };
        
        // Additional debugging
        console.log([RealTime Tracking] Request data - is_completed: ${requestData.is_completed});
        
        // Log the request data for debugging
        console.log('[RealTime Tracking] Preparing progress update:', requestData);
        
        // For completion events, send immediately without debouncing
        if (isActuallyCompleted) {
            console.log('[RealTime Tracking] Module completed! Sending immediate update:', requestData);
            console.log('[RealTime Tracking] isActuallyCompleted:', isActuallyCompleted, 'isCompleted:', isCompleted);
            console.log('[RealTime Tracking] Sending completion update immediately');
            sendProgressUpdateNow(requestData);
            return;
        }
        
        // For regular progress updates, debounce to avoid flooding
        clearTimeout(trackingState.updateDebounceTimer);
        trackingState.progressUpdateQueue = [requestData]; // Keep only the latest update
        
        // Immediately update the UI to show real-time progress
        if (!isActuallyCompleted && requestData.watched_duration > 0 && requestData.total_duration > 0) {
            // Get total modules to calculate course progress
            const allModules = document.querySelectorAll('.list-group-item');
            const totalModules = allModules.length;
            
            // Calculate current module progress (0-100)
            const moduleProgress = (requestData.watched_duration / requestData.total_duration) * 100;
            
            // Get completed modules count from the page
            let completedModules = 0;
            const completedModuleElements = document.querySelectorAll('.list-group-item.completed');
            if (completedModuleElements) {
                completedModules = completedModuleElements.length;
            }
            
            // Calculate course progress using the correct formula:
            // lockedCompletedModulesWeight + (currentModuleProgress / 100 * moduleWeight)
            const moduleWeight = totalModules > 0 ? (1.0 / totalModules) : 0;
            const lockedCompletedModulesWeight = completedModules * moduleWeight;
            const currentModuleContribution = (moduleProgress / 100) * moduleWeight;
            const courseProgress = (lockedCompletedModulesWeight + currentModuleContribution) * 100;
            
            // Log detailed progress calculation for debugging
            console.log('[RealTime Tracking] Progress calculation details:', {
                totalModules: totalModules,
                completedModules: completedModules,
                moduleWeight: moduleWeight,
                lockedCompletedModulesWeight: lockedCompletedModulesWeight,
                currentModuleProgress: moduleProgress,
                currentModuleContribution: currentModuleContribution,
                calculatedCourseProgress: courseProgress
            });
            
            // Ensure we don't exceed 100% and handle edge cases
            const finalCourseProgress = Math.min(100, Math.max(0, courseProgress));
            
            // Log course progress calculation for debugging
            console.log('[RealTime Tracking] Course progress calculation:', {
                moduleProgress: moduleProgress.toFixed(2),
                completedModules: completedModules,
                totalModules: totalModules,
                moduleWeight: moduleWeight.toFixed(4),
                lockedCompletedModulesWeight: lockedCompletedModulesWeight.toFixed(4),
                currentModuleContribution: currentModuleContribution.toFixed(4),
                courseProgress: courseProgress.toFixed(2),
                finalCourseProgress: finalCourseProgress.toFixed(2)
            });
            
            // Update progress bar with dynamic course progress
            // Ensure the progress bar reflects the cumulative course progress
            updateProgressBar(finalCourseProgress);
            
            // Also update any other progress indicators on the page
            const progressElements = document.querySelectorAll('[data-progress-indicator]');
            progressElements.forEach(element => {
                element.textContent = ${finalCourseProgress.toFixed(2)}%;
                element.style.width = ${finalCourseProgress}%;
            });
        }
        
        trackingState.updateDebounceTimer = setTimeout(() => {
            if (trackingState.progressUpdateQueue.length > 0 && !trackingState.isUpdating) {
                sendProgressUpdateNow(trackingState.progressUpdateQueue[0]);
                trackingState.progressUpdateQueue = [];
            }
        }, TRACKING_CONFIG.DEBOUNCE_DELAY);
    }
    
    // Send progress update now (AJAX request)
    function sendProgressUpdateNow(requestData) {
        console.log('[RealTime Tracking] sendProgressUpdateNow called with:', requestData);
        console.log([RealTime Tracking] sendProgressUpdateNow - is_completed: ${requestData.is_completed});
        console.log('[RealTime Tracking] sendProgressUpdateNow - Starting AJAX request');
        if (trackingState.isUpdating) {
            console.log('[RealTime Tracking] Update already in progress, queuing request');
            trackingState.progressUpdateQueue.push(requestData);
            return;
        }
        
        trackingState.isUpdating = true;
        const progressPercent = requestData.watched_duration > 0 && requestData.total_duration > 0 ? 
            (requestData.watched_duration / requestData.total_duration) * 100 : 0;
        
        // Log progress before sending update
        console.log([RealTime Tracking] Sending progress update: Module ${requestData.module_id}, Module Progress: ${progressPercent.toFixed(2)}%, Completed: ${requestData.is_completed});
        
        // Show "Updating..." indicator
        const statusBadge = document.getElementById('progress-status');
        if (statusBadge) {
            statusBadge.style.display = 'inline-block';
            statusBadge.textContent = 'Updating...';
            statusBadge.className = 'badge bg-info ms-2';
        }
        
        // Store in localStorage as fallback
        try {
            const fallbackKey = progress_${requestData.course_id}_${requestData.module_id};
            localStorage.setItem(fallbackKey, JSON.stringify(requestData));
        } catch (e) {
            console.warn('[RealTime Tracking] Failed to save progress to localStorage:', e);
        }
        
        // Send AJAX request to update progress
        console.log('[RealTime Tracking] Sending AJAX request to /api/progress/update');
        fetch('/api/progress/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            console.log('[RealTime Tracking] AJAX request response status:', response.status);
            if (!response.ok) {
                throw new Error(HTTP error! status: ${response.status});
            }
            return response.json();
        })
        .then(data => {
            trackingState.isUpdating = false;
            window.retryCount = 0; // Reset retry counter on success
            
            // Hide "Updating..." indicator
            const statusBadge = document.getElementById('progress-status');
            if (statusBadge) {
                statusBadge.style.display = 'none';
            }
            
            console.log('[RealTime Tracking] Server response:', data);
            
            // Additional debugging
            if (data.success && requestData.is_completed) {
                console.log('[RealTime Tracking] Module completion confirmed by server');
            }
            
            // Additional debugging
            console.log('[RealTime Tracking] Processing server response');
            
            if (data.success) {
                // Clear localStorage fallback on success
                try {
                    const fallbackKey = progress_${requestData.course_id}_${requestData.module_id};
                    localStorage.removeItem(fallbackKey);
                } catch (e) {
                    console.warn('[RealTime Tracking] Failed to clear localStorage:', e);
                }
                
                // Additional debugging
                console.log('[RealTime Tracking] Checking if module completion UI update needed');
                
                // If module was just completed, check if quiz questions exist before redirecting
                if (requestData.is_completed) {
                    console.log('[RealTime Tracking] 🎉 Module completed!');
                    console.log('[RealTime Tracking] Updating UI to show module as completed...');
                    console.log('[RealTime Tracking] Request data:', requestData);
                    
                    // Additional debugging
                    console.log('[RealTime Tracking] Module completion UI update triggered');
                                        
                    // Update UI to show module as completed immediately
                    // Select the module element from the sidebar list group
                    const currentModuleElement = document.querySelector(.list-group-item[data-module-id="${requestData.module_id}"]);
                    if (currentModuleElement) {
                        console.log('[RealTime Tracking] Found module element in sidebar, updating UI...');
                        currentModuleElement.classList.add('completed');
                        // Update the icon
                        const icon = currentModuleElement.querySelector('.fa-play-circle');
                        if (icon) {
                            icon.classList.remove('fa-play-circle');
                            icon.classList.add('fa-check-circle', 'text-success');
                        }
                        // Update the badge
                        const badge = currentModuleElement.querySelector('.badge');
                        if (badge) {
                            badge.className = 'badge bg-success';
                            badge.textContent = '✅ Done';
                            // Ensure the badge is visible and styled properly
                            badge.style.display = 'inline-block';
                        }
                        console.log('[RealTime Tracking] UI updated successfully');
                    } else {
                        console.log('[RealTime Tracking] Module element not found in DOM');
                    }
                    
                    // Additional debugging
                    console.log('[RealTime Tracking] Module completion UI update completed');
                    
                    // Also update the current module in the main content area
                    const mainModuleElement = document.querySelector('.module-video-container');
                    if (mainModuleElement) {
                        mainModuleElement.dataset.moduleCompleted = 'true';
                        // Add completed class to main module element for styling
                        mainModuleElement.classList.add('module-completed');
                        console.log('[RealTime Tracking] Updated main module element as completed');
                    }
                                
                    // Ensure local video completion is properly handled
                    const isLocalVideo = isLocalVideoElement();
                    if (isLocalVideo) {
                        console.log('[RealTime Tracking] Local video detected, ensuring completion status is properly set');
                    }
                    
                    // Additional debugging
                    console.log('[RealTime Tracking] Main module element update completed');
                    
                    // Check if questions exist for this module before redirecting to quiz
                    console.log([RealTime Tracking] Checking if module ${requestData.module_id} has quiz questions...);
                    
                    // Add a fallback timeout in case the fetch request hangs
                    const quizCheckTimeout = setTimeout(() => {
                        console.warn('[RealTime Tracking] Quiz check timeout - proceeding without quiz redirection');
                        console.log('[RealTime Tracking] Module completion processing completed without quiz redirection (timeout).');
                    }, 5000); // 5 second timeout
                    
                    fetch(/api/module/${requestData.module_id}/has-questions)
                    .then(response => {
                        console.log('[RealTime Tracking] Quiz questions check response status:', response.status);
                        if (!response.ok) {
                            throw new Error(HTTP error! status: ${response.status});
                        }
                        return response.json();
                    })
                    .then(quizData => {
                        // Clear the timeout since we got a response
                        clearTimeout(quizCheckTimeout);
                        
                        console.log('[RealTime Tracking] Quiz data received:', quizData);
                        if (quizData.has_questions) {
                            console.log('[RealTime Tracking] Module has quiz questions. Redirecting to quiz page...');
                            // Add a small delay before redirecting to allow UI updates
                            setTimeout(() => {
                                window.location.href = /module/${requestData.module_id}/quiz;
                            }, 1500);
                        } else if (quizData.has_questions === false && quizData.question_count === 0) {
                            console.log('[RealTime Tracking] Module confirmed to have no quiz questions.');
                            // Check if course is completed and redirect if so
                            if (data.course_completed && data.redirect_url) {
                                console.log('[RealTime Tracking] 🎉 Course completed! Redirecting to course page...');
                                // Add a small delay before redirecting to allow UI updates
                                setTimeout(() => {
                                    window.location.href = data.redirect_url;
                                }, 2000);
                            }
                        } else {
                            console.log('[RealTime Tracking] Module has no quiz questions. Not redirecting to quiz.');
                            // Even if there are no quiz questions, we should still show the module as completed
                            // and update the UI accordingly
                            console.log('[RealTime Tracking] Module completion processing completed without quiz redirection.');
                            // Check if course is completed and redirect if so
                            if (data.course_completed && data.redirect_url) {
                                console.log('[RealTime Tracking] 🎉 Course completed! Redirecting to course page...');
                                // Add a small delay before redirecting to allow UI updates
                                setTimeout(() => {
                                    window.location.href = data.redirect_url;
                                }, 2000);
                            }
                        }
                    })
                    .catch(error => {
                        // Clear the timeout since we got an error
                        clearTimeout(quizCheckTimeout);
                        
                        console.error('[RealTime Tracking] Error checking for quiz questions:', error);
                        // Even if there's an error checking, we should not redirect to avoid issues
                        console.log('[RealTime Tracking] Not redirecting to quiz due to error checking for questions.');
                        console.log('[RealTime Tracking] Module completion processing completed without quiz redirection (error).');
                        // Check if course is completed and redirect if so (even in error case)
                        if (data.course_completed && data.redirect_url) {
                            console.log('[RealTime Tracking] 🎉 Course completed! Redirecting to course page...');
                            // Add a small delay before redirecting to allow UI updates
                            setTimeout(() => {
                                window.location.href = data.redirect_url;
                            }, 2000);
                        }
                    });
                    
                    // Additional debugging
                    console.log('[RealTime Tracking] Quiz questions check initiated');

                }

                // Process any queued updates
                if (trackingState.progressUpdateQueue.length > 0) {
                    const nextUpdate = trackingState.progressUpdateQueue.shift();
                    setTimeout(() => sendProgressUpdateNow(nextUpdate), 500);
                }
                
                // Additional debugging
                console.log('[RealTime Tracking] Processing queued updates completed');
            } else {
                console.error('[RealTime Tracking] ❌ Failed to update progress:', data.message);
                console.log('[RealTime Tracking] Progress update failed');
                retryFailedUpdate(requestData);
            }
        })
        .catch(error => {
            trackingState.isUpdating = false;
            console.error('[RealTime Tracking] ❌ Error updating progress:', error);
            console.log('[RealTime Tracking] Progress update error occurred');
            retryFailedUpdate(requestData);
        });
    }
    
    // Retry failed update
    function retryFailedUpdate(requestData) {
        // Limit retries to prevent infinite loops
        if (!window.retryCount) {
            window.retryCount = 0;
        }
        
        window.retryCount++;
        
        // Stop retrying after 3 attempts
        if (window.retryCount > 3) {
            console.error('[RealTime Tracking] ❌ Stopping retries after 3 failed attempts');
            trackingState.isUpdating = false;
            // Show error to user
            const statusBadge = document.getElementById('progress-status');
            if (statusBadge) {
                statusBadge.textContent = 'Update Failed';
                statusBadge.className = 'badge bg-danger ms-2';
                statusBadge.style.display = 'inline-block';
            }
            return;
        }
        
        console.log([RealTime Tracking] Retrying failed update (${window.retryCount}/3) in 3 seconds...);
        console.log('[RealTime Tracking] Retry failed update initiated');
        setTimeout(() => {
            if (!trackingState.isUpdating) {
                sendProgressUpdateNow(requestData);
            }
        }, 3000);
    }
    
    // Update progress bar with dynamic course progress and no animations
    function updateProgressBar(courseProgress) {
        // Update the course progress bar in the sidebar
        const progressBar = document.querySelector('.progress-bar');
        const container = document.querySelector('.module-video-container');
        
        if (progressBar) {
            const progress = parseFloat(courseProgress) || 0;

            // Remove all animations for instant updates
            progressBar.style.transition = 'none';
            progressBar.style.animation = 'none';
            progressBar.style.webkitTransition = 'none';
            progressBar.style.mozTransition = 'none';
            progressBar.style.msTransition = 'none';
            progressBar.style.oTransition = 'none';
            
            // Update progress bar width and text immediately with dynamic values
            progressBar.style.width = ${progress}%;
            progressBar.textContent = ${progress.toFixed(2)}%;
            progressBar.setAttribute('aria-valuenow', progress);
            
            // Update the course progress in the container dataset for future calculations
            if (container) {
                container.dataset.courseProgress = progress.toFixed(2);
            }
            
            // Log the course progress update
            console.log(📊 Course Progress Updated: ${progress.toFixed(2)}%);
            
            // Additional debugging
            console.log([RealTime Tracking] Progress bar updated to: ${progress.toFixed(2)}%);
            
            // Progress bar updated with dynamic course progress
            
            // Also update any other progress indicators that might exist
            const additionalProgressBars = document.querySelectorAll('.course-progress-indicator');
            additionalProgressBars.forEach(bar => {
                bar.style.width = ${progress}%;
                bar.textContent = ${progress.toFixed(2)}%;
                bar.setAttribute('aria-valuenow', progress);
            });
        } else {
            console.error('[RealTime Tracking] Progress bar element not found!');
        }
    }
    
    // Expose function globally for backward compatibility
    window.initializeRealTimeTracking = initializeRealTimeTracking;
    
})();
