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
    // Get the overlay element
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        console.error("Loading overlay element not found");
        return;
    }
    
    // Update text if provided
    const titleElement = document.getElementById('loading-title');
    const subtitleElement = document.getElementById('loading-subtitle');
    
    if (titleElement && title) {
        titleElement.textContent = title;
    }
    
    if (subtitleElement && subtitle) {
        subtitleElement.textContent = subtitle;
    }
    
    // Show the overlay
    overlay.classList.remove('hidden');
    
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