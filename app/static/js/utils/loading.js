console.log('loading.js loaded');

// Check if loading overlay HTML is present
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('loading-overlay');
    const titleEl = document.getElementById('loading-title');
    const subtitleEl = document.getElementById('loading-subtitle');
    
    console.log('Loading overlay elements on page load:', {
        overlay: !!overlay,
        titleEl: !!titleEl,
        subtitleEl: !!subtitleEl
    });
});

/**
 * Loading overlay utilities
 * Functions to show and hide the loading overlay component
 */

/**
 * Shows the loading overlay
 * @param {string} title - Optional custom title text (defaults to "Loading...")
 * @param {string} subtitle - Optional custom subtitle text (defaults to "Please wait for awesomeness.")
 */
function showLoadingOverlay(title = "Loading...", subtitle = "Please wait for awesomeness.") {
    console.log('showLoadingOverlay called with:', { title, subtitle });
    const overlay = document.getElementById('loading-overlay');
    const titleEl = document.getElementById('loading-title');
    const subtitleEl = document.getElementById('loading-subtitle');
    
    console.log('Loading overlay elements:', {
        overlay: !!overlay,
        titleEl: !!titleEl,
        subtitleEl: !!subtitleEl
    });
    
    if (overlay && titleEl && subtitleEl) {
        titleEl.textContent = title;
        subtitleEl.textContent = subtitle;
        overlay.classList.remove('hidden');
        console.log('Loading overlay shown successfully');
    } else {
        console.error('Missing required loading overlay elements!');
    }
    
    // Prevent body scrolling while overlay is shown
    document.body.style.overflow = 'hidden';
}

/**
 * Hides the loading overlay
 */
function hideLoadingOverlay() {
    // Get the overlay element
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        console.error("Loading overlay element not found");
        return;
    }
    
    // Hide the overlay
    overlay.classList.add('hidden');
    
    // Restore body scrolling
    document.body.style.overflow = '';
}

// Export functions for use in other modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showLoadingOverlay,
        hideLoadingOverlay
    };
} 