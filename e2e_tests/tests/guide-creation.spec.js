// @ts-check
const { test, expect } = require('@playwright/test');
const { createGuide, submitRecommendations } = require('../utils/test-setup');

// Increase the test timeout since we're dealing with AI processing
test.setTimeout(30000);

/**
 * Tests the complete flow of:
 * 1. Creating a guide
 * 2. Adding recommendations as the author
 * 3. Processing those recommendations with AI
 * 4. Submitting the final recommendations
 * 5. Checking the trip page
 */
test.describe('Create a Trip Guide', () => {
  let tripSlug;
  
  test('should navigate to the create guide page', async ({ page }) => {
    try {
      // Visit the home page
      await page.goto('/');
      
      // Look for the Create A Guide link in the navigation
      const createGuideLink = page.locator('a:has-text("Create A Guide")').first();
      await expect(createGuideLink).toBeVisible();
      
      // Click on the Create A Guide link
      await createGuideLink.click();
      
      // Verify we're on the create guide page
      await page.waitForURL('**/create-guide');
      
      // Verify the page title
      const pageTitle = page.locator('h1:has-text("Create a Trip Guide to Share with Others")');
      await expect(pageTitle).toBeVisible();
      
      // Verify the destination input has the correct label
      const destinationLabel = page.locator('label:has-text("Where is this guide for?")');
      await expect(destinationLabel).toBeVisible();
    } catch (error) {
      console.error('Navigation test failed:', error.message);
      await page.screenshot({ path: 'guide-navigation-failure.png' });
      throw error;
    }
  });
  
  test('should create a guide and be redirected to add recommendations', async ({ page }) => {
    try {
      // Create a guide
      tripSlug = await createGuide(page, 'Paris', 'Guide Author', 'author@example.com');
      
      // Check if we were redirected to auth page (email already exists)
      if (page.url().includes('/check_email')) {
        // In test environment, auth link should be displayed
        const authLink = await page.locator('a:has-text("Click here to log in")');
        if (await authLink.count() > 0) {
          await authLink.click();
          
          // After auth, we should be redirected to add recommendations page
          await page.waitForURL('**/trip/**/add', { timeout: 10000 });
          
          // Extract trip slug from URL
          const url = page.url();
          const matches = url.match(/\/trip\/([^\/]+)\/add/);
          tripSlug = matches ? matches[1] : tripSlug;
        }
      }
      
      // Or check if we're on name resolution page
      else if (page.url().includes('/name-resolution')) {
        // Choose to use the new name
        await page.locator('#new-name-radio').click();
        await page.click('button[type="submit"]');
        
        // Check if redirected to auth
        if (page.url().includes('/check_email')) {
          // In test environment, auth link should be displayed
          const authLink = await page.locator('a:has-text("Click here to log in")');
          if (await authLink.count() > 0) {
            await authLink.click();
            
            // After auth, we should be redirected to add recommendations page
            await page.waitForURL('**/trip/**/add', { timeout: 10000 });
            
            // Extract trip slug from URL
            const url = page.url();
            const matches = url.match(/\/trip\/([^\/]+)\/add/);
            tripSlug = matches ? matches[1] : tripSlug;
          }
        }
      }
      
      // Verify we're on the add recommendation page
      await page.waitForURL(`**/trip/${tripSlug}/add`);
      
      // Verify the recommendation page has the correct heading for guide creator mode
      const header = page.locator('h1.page-title');
      const headerText = await header.textContent();
      expect(headerText).toContain('Share your favorite places in Paris');
      
      // Test that the recommendations form exists
      await expect(page.locator('#text-recommendations')).toBeVisible();
      
      // Verify the button is disabled initially
      await expect(page.locator('#submit-button')).toBeDisabled();
    } catch (error) {
      console.error('Guide creation test failed:', error.message);
      await page.screenshot({ path: 'guide-creation-flow-failure.png' });
      throw error;
    }
  });
  
  test('should add recommendations to the guide and view the trip page', async ({ page }) => {
    try {
      // Create a guide first
      tripSlug = await createGuide(page, 'Paris', 'Guide Author', 'author@example.com');
      
      // Handle possible redirection to auth or name resolution
      if (page.url().includes('/check_email')) {
        // In test environment, auth link should be displayed
        const authLink = await page.locator('a:has-text("Click here to log in")');
        if (await authLink.count() > 0) {
          await authLink.click();
          await page.waitForURL('**/trip/**/add', { timeout: 10000 });
        }
      } else if (page.url().includes('/name-resolution')) {
        // Choose to use the new name
        await page.locator('#new-name-radio').click();
        await page.click('button[type="submit"]');
        
        // Check if redirected to auth
        if (page.url().includes('/check_email')) {
          const authLink = await page.locator('a:has-text("Click here to log in")');
          if (await authLink.count() > 0) {
            await authLink.click();
            await page.waitForURL('**/trip/**/add', { timeout: 10000 });
          }
        }
      }
      
      // Extract trip slug from current URL if needed
      if (page.url().includes('/add')) {
        const url = page.url();
        const matches = url.match(/\/trip\/([^\/]+)\/add/);
        tripSlug = matches ? matches[1] : tripSlug;
      }
      
      // Add recommendations
      const recommendations = 'The Eiffel Tower is a must-see. Visit the Louvre to see the Mona Lisa. Notre Dame Cathedral is beautiful. Try a croissant at any local bakery.';
      
      // Enter recommendations
      await page.fill('#text-recommendations', recommendations);
      
      // Wait for the submit button to be enabled
      await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
      
      // Submit recommendations
      await page.click('#submit-button');
      
      // Wait for recommendations container to appear
      await page.waitForSelector('#recommendations-container', { timeout: 10000 });
      
      // Verify confirmation page has correct heading for guide creator mode
      const confirmHeader = page.locator('h1:has-text("Your Paris Guide")');
      await expect(confirmHeader).toBeVisible();
      
      // Wait for the submit button to be enabled again
      await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
      
      // Submit the final recommendations
      await page.click('#submit-button');
      
      // If name modal appears, fill it in
      if (await page.locator('#name-modal').isVisible()) {
        await page.fill('#modal-recommender-name', 'Guide Author');
        await page.click('.submit-with-name');
      }
      
      // Wait for the trip page
      await page.waitForURL(`**/trip/${tripSlug}`, { timeout: 10000 });
      
      // Verify we're on the trip page with the title showing it's the user's trip
      const tripTitle = page.locator('h1.page-title');
      const tripTitleText = await tripTitle.textContent();
      expect(tripTitleText.trim()).toContain('Your Paris Trip Recommendations');
      
      // Check for the presence of recommendations
      const recommendationCards = await page.locator('.recommendation-card').count();
      expect(recommendationCards).toBeGreaterThan(0);
      
      // Verify share box exists for the trip owner
      await expect(page.locator('.share-box')).toBeVisible();
    } catch (error) {
      console.error('Adding recommendations test failed:', error.message);
      await page.screenshot({ path: 'guide-recommendations-failure.png' });
      throw error;
    }
  });
}); 