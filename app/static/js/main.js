// This file contains global JavaScript functionality

// Helper function to simplify query selection
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Flask Starter App initialized');
  
  // Add current year to footer if the block exists
  const currentYear = new Date().getFullYear();
  const yearElement = $('.footer-year');
  if (yearElement) {
    yearElement.textContent = currentYear;
  }
  
  // Initialize form loading indicators - attach to all forms with data-show-loading="true"
  const loadingForms = $$('form[data-show-loading="true"]');
  loadingForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      // Get custom loading messages from data attributes if provided
      const loadingTitle = this.dataset.loadingTitle || "Loading...";
      const loadingSubtitle = this.dataset.loadingSubtitle || "Please wait for awesomeness.";
      
      // Show the loading overlay with custom messages
      if (typeof showLoadingOverlay === 'function') {
        showLoadingOverlay(loadingTitle, loadingSubtitle);
      }
    });
  });
}); 