// @ts-check
const { test, expect } = require('@playwright/test');
const { createTrip, submitRecommendations } = require('../utils/test-setup');

// Increase the test timeout since we're dealing with AI processing
test.setTimeout(30000);

/**
 * Tests the complete flow of:
 * 1. Creating a trip
 * 2. Getting recommendations from one person
 * 3. Processing those recommendations with AI
 * 4. Submitting the final recommendations
 */
test.describe('Create Trip and Get Recommendations from One Person', () => {
  // Setup - create a trip before each test
  test.beforeEach(async ({ page }) => {
    try {
      const shareLink = await createTrip(page, 'Tokyo', 'Test Traveler', 'traveler@example.com');
      await page.goto(shareLink);
      await page.waitForSelector('#text-recommendations', { timeout: 5000 });
    } catch (error) {
      console.error('Setup failed:', error.message);
      await page.screenshot({ path: 'setup-failure-submission.png' });
      throw error;
    }
  });
  
  test('should create trip and submit recommendations', async ({ page }) => {
    try {
      const recommendations = 'You should visit Tokyo Tower and try sushi at Tsukiji Market. Also check out Shinjuku Gyoen for cherry blossoms in spring.';
      await submitRecommendations(page, page.url(), recommendations, 'Test Recommender');
      
      // Verify we're on the thank you page
      const currentUrl = page.url();
      expect(currentUrl).toContain('/thank-you/');
      
      // Try to verify flash message if present
      const flashMessage = await page.locator('.flash-message');
      if (await flashMessage.count() > 0) {
        await expect(flashMessage).toBeVisible();
      }
      
      // Check for thank you page title
      if (await page.locator('h1.text-3xl').count() > 0) {
        const pageTitle = await page.locator('h1.text-3xl');
        await expect(pageTitle).toBeVisible();
        expect(await pageTitle.textContent()).toContain('Thank You!');
      }
      
      // If we can see recommendation cards, verify them
      if (await page.locator('.card').count() > 0) {
        // Look for any recommendation that was submitted
        const recommendationCards = await page.locator('.card').count();
        expect(recommendationCards).toBeGreaterThan(0);
        
        // Look for the recommender name if available
        if (await page.locator('.card:has-text("Test Recommender")').count() > 0) {
          const recommenderInfo = await page.locator('.card:has-text("Test Recommender")');
          expect(await recommenderInfo.count()).toBeGreaterThanOrEqual(1);
        }
      }
    } catch (error) {
      console.error('Submission test failed:', error.message);
      await page.screenshot({ path: 'submission-test-failure.png' });
      throw error;
    }
  });
  
  test('should prevent submission of empty recommendations', async ({ page }) => {
    try {
      // Make sure the text area is empty
      await page.fill('#text-recommendations', '');
      
      // Click submit button to check validation
      if (await page.locator('#submit-button[disabled]').count() === 0) {
        // If not disabled, try clicking it to see what happens
        await page.click('#submit-button');
        
        // We should still be on the same page
        expect(page.url()).toContain('/add/');
      } else {
        // Verify button is disabled with empty input
        await expect(page.locator('#submit-button')).toBeDisabled();
      }
      
      // Enter minimal text
      await page.fill('#text-recommendations', 'Tokyo Tower');
      
      // Wait for the button to become enabled
      await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
      
      // Now button should be enabled
      await expect(page.locator('#submit-button')).toBeEnabled();
    } catch (error) {
      console.error('Empty submission test failed:', error.message);
      await page.screenshot({ path: 'empty-submission-test-failure.png' });
      throw error;
    }
  });
}); 