/**
 * StreamWave Entertainment - Member Library & Catalogue Logic
 * Academic Serverless Prototype with Signed Cookie Access Control
 */

(function () {
    'use strict';

    // App State
    const state = {
        media: [],
        activeType: '',
        activeGenre: '',
        searchQuery: '',
        currentTrack: null,
        activeVideoMovie: null,
        lastFocusedElement: null,
        loggedVideoEvents: new Set(),
        sessionId: 'sess-' + Math.random().toString(36).substring(2, 9),
        playerMinimized: false,
        memberEmail: null
    };

    // DOM Elements
    const elements = {
        searchInput: document.getElementById('search-input'),
        clearSearchBtn: document.getElementById('clear-search'),
        typeTabs: document.querySelectorAll('.type-tab'),
        genreSelect: document.getElementById('genre-select'),
        itemCount: document.getElementById('item-count'),
        memberEmailText: document.getElementById('member-email-text'),
        
        // Views
        loadingState: document.getElementById('loading-state'),
        errorState: document.getElementById('error-state'),
        errorMessage: document.getElementById('error-message'),
        emptyState: document.getElementById('empty-state'),
        mediaGrid: document.getElementById('media-grid'),

        // Details Modal
        detailsDialog: document.getElementById('details-dialog'),
        closeDialogBtn: document.getElementById('close-dialog'),
        dialogBody: document.getElementById('dialog-body'),
        
        // Video Modal
        videoDialog: document.getElementById('video-dialog'),
        closeVideoBtn: document.getElementById('close-video-btn'),
        closeVideoX: document.getElementById('close-video-x'),
        videoModalTitle: document.getElementById('video-modal-title'),
        videoElement: document.getElementById('html5-video'),
        videoSource: document.getElementById('video-source'),
        videoReplayBtn: document.getElementById('video-replay-btn'),

        // Audio Player
        audioBar: document.getElementById('audio-player-bar'),
        playerToggleBtn: document.getElementById('player-toggle-btn'),
        audioElement: document.getElementById('html5-audio'),
        audioSource: document.getElementById('audio-source'),
        playerThumb: document.getElementById('player-thumb'),
        playerTitle: document.getElementById('player-title'),
        playerArtist: document.getElementById('player-artist'),
        eventLogText: document.getElementById('event-log-text'),
        eventDot: document.querySelector('.event-dot')
    };

    /**
     * Verifies active member session, binds event listeners and fetches initial media list
     */
    async function init() {
        bindEvents();
        const isAuthenticated = await checkMemberSession();
        if (isAuthenticated) {
            fetchMedia();
        }
    }

    /**
     * Checks member authorization with GET /api/session
     */
    async function checkMemberSession() {
        try {
            const res = await fetch('/api/session');
            if (res.ok) {
                const data = await res.json();
                if (data.authenticated) {
                    state.memberEmail = data.email;
                    if (elements.memberEmailText) {
                        elements.memberEmailText.textContent = data.email || 'Demo Member';
                    }
                    return true;
                }
            }
        } catch (err) {
            console.error('Session check error:', err);
        }

        // Unpaid user attempting to access /library -> redirect to checkout or landing
        window.location.href = '/checkout';
        return false;
    }

    /**
     * Signs out member by calling POST /api/logout and clearing session cookie
     */
    async function signOut() {
        try {
            await fetch('/api/logout', { method: 'POST' });
        } catch (e) {
            console.error('Logout error:', e);
        }
        window.location.href = '/';
    }

    /**
     * Assessment reset control endpoint wrapper
     */
    async function resetDemoSession() {
        try {
            await fetch('/api/reset-demo', { method: 'POST' });
        } catch (e) {
            console.error('Reset demo error:', e);
        }
        window.location.href = '/';
    }

    /**
     * Binds user interaction listeners
     */
    function bindEvents() {
        // Search input with debounce
        let searchTimeout;
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', (e) => {
                state.searchQuery = e.target.value.trim();
                elements.clearSearchBtn.style.display = state.searchQuery ? 'block' : 'none';
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => fetchMedia(), 250);
            });
        }

        if (elements.clearSearchBtn) {
            elements.clearSearchBtn.addEventListener('click', () => {
                elements.searchInput.value = '';
                state.searchQuery = '';
                elements.clearSearchBtn.style.display = 'none';
                fetchMedia();
            });
        }

        // Type tabs
        elements.typeTabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                elements.typeTabs.forEach((t) => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');
                state.activeType = tab.getAttribute('data-type');
                fetchMedia();
            });
        });

        // Genre filter select
        if (elements.genreSelect) {
            elements.genreSelect.addEventListener('change', (e) => {
                state.activeGenre = e.target.value;
                fetchMedia();
            });
        }

        // Details Modal close button
        if (elements.closeDialogBtn) {
            elements.closeDialogBtn.addEventListener('click', () => {
                elements.detailsDialog.close();
            });
        }

        // Close details modal on backdrop click
        if (elements.detailsDialog) {
            elements.detailsDialog.addEventListener('click', (e) => {
                const rect = elements.detailsDialog.getBoundingClientRect();
                const isInDialog = (
                    rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
                    rect.left <= e.clientX && e.clientX <= rect.left + rect.width
                );
                if (!isInDialog) {
                    elements.detailsDialog.close();
                }
            });
        }

        // Video Modal Close Handlers
        if (elements.closeVideoBtn) {
            elements.closeVideoBtn.addEventListener('click', closeVideoModal);
        }
        if (elements.closeVideoX) {
            elements.closeVideoX.addEventListener('click', closeVideoModal);
        }

        // Close video modal on backdrop click
        if (elements.videoDialog) {
            elements.videoDialog.addEventListener('click', (e) => {
                const rect = elements.videoDialog.getBoundingClientRect();
                const isInDialog = (
                    rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
                    rect.left <= e.clientX && e.clientX <= rect.left + rect.width
                );
                if (!isInDialog) {
                    closeVideoModal();
                }
            });
        }

        // Video ended listener -> show Replay button
        if (elements.videoElement) {
            elements.videoElement.addEventListener('ended', () => {
                if (elements.videoReplayBtn) {
                    elements.videoReplayBtn.style.display = 'inline-flex';
                }
            });

            // Video play listener -> trigger POST /api/play-events (once per movie playback start)
            elements.videoElement.addEventListener('play', () => {
                if (state.activeVideoMovie) {
                    const movieId = state.activeVideoMovie.id;
                    if (!state.loggedVideoEvents.has(movieId)) {
                        state.loggedVideoEvents.add(movieId);
                        logPlayEvent(movieId);
                    }
                }
            });
        }

        // Replay button click handler
        if (elements.videoReplayBtn) {
            elements.videoReplayBtn.addEventListener('click', () => {
                elements.videoReplayBtn.style.display = 'none';
                if (elements.videoElement) {
                    elements.videoElement.currentTime = 0;
                    elements.videoElement.play().catch(err => console.warn('Replay play error:', err));
                }
            });
        }

        // Global Escape key listener for dialog accessibility
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (elements.videoDialog && elements.videoDialog.open) {
                    closeVideoModal();
                } else if (elements.detailsDialog && elements.detailsDialog.open) {
                    elements.detailsDialog.close();
                }
            }
        });

        // Player mobile minimize toggle
        if (elements.playerToggleBtn) {
            elements.playerToggleBtn.addEventListener('click', () => {
                state.playerMinimized = !state.playerMinimized;
                elements.audioBar.classList.toggle('minimized', state.playerMinimized);
                elements.playerToggleBtn.textContent = state.playerMinimized ? '▲' : '▼';
                elements.playerToggleBtn.setAttribute('aria-label', state.playerMinimized ? 'Expand audio player' : 'Minimize audio player');
            });
        }

        // Audio element playback listener to trigger POST /api/play-events for music
        if (elements.audioElement) {
            elements.audioElement.addEventListener('play', () => {
                if (state.currentTrack) {
                    logPlayEvent(state.currentTrack.id);
                }
            });
        }
    }

    /**
     * Fetches media items from protected FastAPI backend /api/media endpoint
     */
    async function fetchMedia() {
        showView('loading');
        
        try {
            const params = new URLSearchParams();
            if (state.searchQuery) params.append('query', state.searchQuery);
            if (state.activeType) params.append('type', state.activeType);
            if (state.activeGenre) params.append('genre', state.activeGenre);

            const url = `/api/media${params.toString() ? '?' + params.toString() : ''}`;
            const response = await fetch(url);

            if (response.status === 401) {
                // Session expired or unauthorized
                window.location.href = '/checkout';
                return;
            }

            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            state.media = await response.json();
            renderMediaGrid();
        } catch (err) {
            console.error('Error fetching media:', err);
            if (elements.errorMessage) {
                elements.errorMessage.textContent = err.message || 'Failed to connect to StreamWave API.';
            }
            showView('error');
        }
    }

    /**
     * Renders media items in card grid with StreamWave play symbol ("▶ Watch" / "▶ Play")
     */
    function renderMediaGrid() {
        if (elements.itemCount) {
            elements.itemCount.textContent = `${state.media.length} item${state.media.length === 1 ? '' : 's'}`;
        }

        if (state.media.length === 0) {
            showView('empty');
            return;
        }

        elements.mediaGrid.innerHTML = state.media.map((item) => {
            const isMovie = item.type === 'movie';
            const playLabel = isMovie ? 'Watch' : 'Play';
            const playIcon = '▶';
            const clickHandler = isMovie
                ? `window.streamWaveApp.playMoviePreview('${item.id}', this)`
                : `window.streamWaveApp.playMedia('${item.id}')`;
            const escapedTitle = escapeHtml(item.title);

            return `
                <article class="media-card" data-id="${item.id}">
                    <div class="card-thumb-wrapper" onclick="window.streamWaveApp.openDetails('${item.id}', this)" title="View details for ${escapedTitle}">
                        <img class="card-thumb" src="${item.cover_image || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80'}" alt="${escapedTitle}" loading="lazy">
                        <span class="card-badge">${escapeHtml(item.type)}</span>
                        <span class="tech-sample-tag">5-sec technical preview</span>
                    </div>
                    <div class="card-content">
                        <h3 class="card-title" title="${escapedTitle}" onclick="window.streamWaveApp.openDetails('${item.id}', this)">${escapedTitle}</h3>
                        <div class="card-subtitle">${escapeHtml(item.artist_or_director)}</div>
                        <div class="card-meta">
                            <span>${item.year}</span>
                            <span>•</span>
                            <span>${escapeHtml(item.genre)}</span>
                            <span>•</span>
                            <span>${escapeHtml(item.duration)}</span>
                        </div>
                        <div class="card-actions">
                            <button class="btn btn-primary" onclick="${clickHandler}" aria-label="${playLabel} ${escapedTitle}">
                                ${playIcon} ${playLabel}
                            </button>
                            <button class="btn btn-secondary" onclick="window.streamWaveApp.openDetails('${item.id}', this)" aria-label="View details for ${escapedTitle}">
                                ℹ Details
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join('');

        showView('grid');
    }

    /**
     * Switch view state (loading, error, empty, grid)
     */
    function showView(viewName) {
        if (elements.loadingState) elements.loadingState.style.display = viewName === 'loading' ? 'block' : 'none';
        if (elements.errorState) elements.errorState.style.display = viewName === 'error' ? 'block' : 'none';
        if (elements.emptyState) elements.emptyState.style.display = viewName === 'empty' ? 'block' : 'none';
        if (elements.mediaGrid) elements.mediaGrid.style.display = viewName === 'grid' ? 'grid' : 'none';
    }

    /**
     * Opens professional video player modal for movie previews
     */
    async function playMoviePreview(id, triggerElement) {
        const item = state.media.find(m => m.id === id) || await fetchSingleItem(id);
        if (!item) return;

        state.activeVideoMovie = item;
        state.lastFocusedElement = triggerElement || document.activeElement;

        // Populate title
        elements.videoModalTitle.textContent = item.title;

        // Set video source to static preview MP4 URL
        const videoUrl = item.preview_url || item.media_url || '/media/streamwave-preview.mp4';
        elements.videoSource.src = videoUrl;
        elements.videoElement.load();

        // Reset replay button
        if (elements.videoReplayBtn) {
            elements.videoReplayBtn.style.display = 'none';
        }

        // Lock scroll & show modal
        document.body.style.overflow = 'hidden';
        elements.videoDialog.showModal();

        // Start playback after user click interaction
        try {
            await elements.videoElement.play();
        } catch (e) {
            console.warn('Video play prevented or interrupted:', e);
        }

        // Log playback event
        if (!state.loggedVideoEvents.has(id)) {
            state.loggedVideoEvents.add(id);
            logPlayEvent(id);
        }
    }

    /**
     * Closes video modal, resets playback position, and restores focus/scrolling
     */
    function closeVideoModal() {
        if (elements.videoElement) {
            elements.videoElement.pause();
            elements.videoElement.currentTime = 0;
        }

        state.activeVideoMovie = null;
        document.body.style.overflow = '';

        if (elements.videoDialog && elements.videoDialog.open) {
            elements.videoDialog.close();
        }

        // Restore keyboard focus to triggering element
        if (state.lastFocusedElement && typeof state.lastFocusedElement.focus === 'function') {
            state.lastFocusedElement.focus();
        }
    }

    /**
     * Plays music item audio file using HTML5 Audio Player
     */
    async function playMedia(id) {
        const item = state.media.find(m => m.id === id) || await fetchSingleItem(id);
        if (!item) return;

        // If item is a movie, delegate to playMoviePreview
        if (item.type === 'movie') {
            playMoviePreview(id);
            return;
        }

        state.currentTrack = item;
        elements.playerTitle.textContent = item.title;
        elements.playerArtist.textContent = `${item.artist_or_director} (${item.genre})`;
        elements.playerThumb.textContent = '🎵';

        // Unminimize player bar if minimized
        if (state.playerMinimized) {
            state.playerMinimized = false;
            elements.audioBar.classList.remove('minimized');
            if (elements.playerToggleBtn) elements.playerToggleBtn.textContent = '▼';
        }

        // Set audio source to static file URL (defaults to /media/demo.wav for demo)
        const audioUrl = item.media_url || '/media/demo.wav';
        elements.audioSource.src = audioUrl;
        elements.audioElement.load();
        
        try {
            await elements.audioElement.play();
        } catch (e) {
            console.warn('Autoplay prevented or failed:', e);
        }

        // Trigger POST /api/play-events
        logPlayEvent(id);
    }

    /**
     * Fetches a single media item by ID
     */
    async function fetchSingleItem(id) {
        try {
            const res = await fetch(`/api/media/${id}`);
            if (res.ok) return await res.json();
        } catch (e) {
            console.error('Error fetching item detail:', e);
        }
        return null;
    }

    /**
     * Sends playback event log to POST /api/play-events
     */
    async function logPlayEvent(mediaId) {
        updateEventBadge('Logging...', true);
        try {
            const payload = {
                media_id: mediaId,
                session_id: state.sessionId,
                client_timestamp: new Date().toISOString()
            };

            const res = await fetch('/api/play-events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                updateEventBadge(`Event Logged (${data.event.server_timestamp.slice(11, 19)} UTC)`, false);
            } else {
                updateEventBadge('Event Log Error', false);
            }
        } catch (err) {
            console.error('Play event error:', err);
            updateEventBadge('Event Log Failed', false);
        }
    }

    /**
     * Updates status dot badge near audio player
     */
    function updateEventBadge(text, isActive) {
        if (!elements.eventLogText) return;
        elements.eventLogText.textContent = text;
        if (isActive && elements.eventDot) {
            elements.eventDot.classList.add('active');
        } else if (elements.eventDot) {
            elements.eventDot.classList.remove('active');
        }
    }

    /**
     * Opens accessible details dialog
     */
    async function openDetails(id, triggerElement) {
        const item = state.media.find(m => m.id === id) || await fetchSingleItem(id);
        if (!item) return;

        state.lastFocusedElement = triggerElement || document.activeElement;
        const isMovie = item.type === 'movie';
        const playLabel = isMovie ? 'Watch' : 'Play';
        const playIcon = '▶';
        const clickHandler = isMovie
            ? `window.streamWaveApp.playMoviePreview('${item.id}'); document.getElementById('details-dialog').close();`
            : `window.streamWaveApp.playMedia('${item.id}'); document.getElementById('details-dialog').close();`;

        elements.dialogBody.innerHTML = `
            <div class="dialog-header-meta">
                <span class="meta-tag">${escapeHtml(item.type)}</span>
                <span class="meta-separator">•</span>
                <span style="color: var(--text-secondary); font-size: 0.85rem;">${item.year}</span>
                <span class="meta-separator">•</span>
                <span class="tech-sample-pill">${isMovie ? '5-sec MP4 preview' : 'Technical audio sample'}</span>
            </div>
            <h2 id="dialog-title" class="dialog-title">${escapeHtml(item.title)}</h2>
            <div class="dialog-artist">By ${escapeHtml(item.artist_or_director)}</div>
            <p id="dialog-desc" class="dialog-description">${escapeHtml(item.description)}</p>
            
            <div class="dialog-info-grid">
                <div class="info-item">
                    <div class="info-label">Genre</div>
                    <div class="info-value">${escapeHtml(item.genre)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Duration</div>
                    <div class="info-value">${escapeHtml(item.duration)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Media ID</div>
                    <div class="info-value">${escapeHtml(item.id)}</div>
                </div>
            </div>

            <div class="dialog-actions" style="display: flex; gap: 0.75rem;">
                <button class="btn btn-primary" onclick="${clickHandler}">
                    ${playIcon} ${playLabel}
                </button>
            </div>
        `;

        elements.detailsDialog.showModal();
    }

    /**
     * Resets filter parameters
     */
    function resetFilters() {
        state.searchQuery = '';
        state.activeType = '';
        state.activeGenre = '';
        if (elements.searchInput) elements.searchInput.value = '';
        if (elements.genreSelect) elements.genreSelect.value = '';
        if (elements.clearSearchBtn) elements.clearSearchBtn.style.display = 'none';
        elements.typeTabs.forEach((tab, index) => {
            tab.classList.toggle('active', index === 0);
            tab.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
        });
        fetchMedia();
    }

    /**
     * Basic HTML escaping to prevent XSS
     */
    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Expose global methods for inline button onclick handlers
    window.streamWaveApp = {
        fetchMedia,
        playMedia,
        playMoviePreview,
        openDetails,
        closeVideoModal,
        signOut,
        resetDemoSession,
        resetFilters
    };

    // Initialize on DOM load if on library page
    if (window.location.pathname === '/library') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    }
})();
