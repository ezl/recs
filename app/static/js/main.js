console.log('main.js loaded');

// This file contains global JavaScript functionality

// Helper function to simplify query selection
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOMContentLoaded event fired in main.js');
  
  // Add current year to footer if the block exists
  const currentYear = new Date().getFullYear();
  const yearElement = $('.footer-year');
  if (yearElement) {
    yearElement.textContent = currentYear;
  }
  
  // Handle forms with data-show-loading attribute
  $$('form[data-show-loading="true"]').forEach(form => {
    form.addEventListener('submit', function(e) {
      // Get custom loading messages if specified
      const loadingTitle = this.dataset.loadingTitle || "Processing...";
      const loadingSubtitle = this.dataset.loadingSubtitle || "Please wait while we process your request.";
      
      // Show loading overlay if the function exists
      if (typeof showLoadingOverlay === 'function') {
        console.log('Showing loading overlay for form submission with:', { loadingTitle, loadingSubtitle });
        showLoadingOverlay(loadingTitle, loadingSubtitle);
      } else {
        console.warn('showLoadingOverlay function not found, but form has data-show-loading attribute');
      }
    });
    
    console.log('Added submit handler with loading overlay to form:', form.id || form.action || 'unnamed form');
  });
}); 