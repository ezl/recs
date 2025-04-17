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
}); 