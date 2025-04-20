// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

test.setTimeout(12000);

test.describe('Audio Recording and Transcription', () => {
  // Setup - create a trip before each test
  test.beforeEach(async ({ page }) => {
    try {
      // Create a trip
      await page.goto('/');
      
      // Wait for form to be loaded
      await page.waitForSelector('#destination', { timeout: 1000 });
      
      await page.fill('#destination', 'London');
      
      // Submit the form
      await page.click('button[type="submit"]');
      
      // Wait for navigation to the user info page
      await page.waitForURL('**/user-info');
      
      // Wait for form to be loaded
      await page.waitForSelector('#name', { timeout: 1000 });
      await page.waitForSelector('#email', { timeout: 1000 });
      
      await page.fill('#name', 'Audio Tester');
      await page.fill('#email', 'audio@example.com');
      
      // Submit the form
      await page.click('button[type="submit"]');
      
      // Wait for navigation to the trip detail page
      await page.waitForURL('**/trip/**');
      
      // Take a screenshot for debugging
      await page.screenshot({ path: 'trip-detail-audio.png' });
      
      // Wait for share box to be visible
      await page.waitForSelector('.share-box', { timeout: 1000 });
      
      // Navigate to recommendation page
      const inputField = await page.locator('.share-box input[type="text"]');
      const shareLink = await inputField.inputValue();
      await page.goto(shareLink);
    } catch (error) {
      console.error('Setup failed:', error.message);
      // Take a screenshot to help debug
      await page.screenshot({ path: 'setup-failure-audio.png' });
      throw error;
    }
  });
  
  test('should toggle between text and audio input modes', async ({ page }) => {
    // Initially, text input should be visible
    await page.waitForSelector('#text-input-container', { timeout: 1000 });
    await expect(page.locator('#text-input-container')).toBeVisible();
    
    try {
      // Check if audio input is not visible
      if (await page.locator('#audio-input-container').count() > 0) {
        await expect(page.locator('#audio-input-container')).not.toBeVisible();
      }
      
      // Make sure toggle button exists
      await page.waitForSelector('#toggle-input-btn', { timeout: 1000 });
      
      // Click the toggle button to switch to audio mode
      await page.click('#toggle-input-btn');
      
      // Now audio input should be visible
      await page.waitForSelector('#audio-input-container', { timeout: 1000 });
      await expect(page.locator('#audio-input-container')).toBeVisible();
      
      // Text input should be hidden
      await expect(page.locator('#text-input-container')).not.toBeVisible();
      
      // Click the toggle button again to switch back to text mode
      await page.click('#toggle-input-btn');
      
      // Now text input should be visible again
      await page.waitForSelector('#text-input-container', { state: 'visible', timeout: 1000 });
      await expect(page.locator('#text-input-container')).toBeVisible();
      
      // Audio input should be hidden
      if (await page.locator('#audio-input-container').count() > 0) {
        await expect(page.locator('#audio-input-container')).not.toBeVisible();
      }
    } catch (error) {
      console.error('Toggle test failed:', error.message);
      await page.screenshot({ path: 'toggle-failure.png' });
      throw error;
    }
  });
  
  // Note: Using a simplified test that doesn't depend on mock transcription
  test('should show recording UI elements correctly', async ({ page }) => {
    try {
      // Make sure toggle button exists
      await page.waitForSelector('#toggle-input-btn', { timeout: 1000 });
      
      // Switch to audio mode
      await page.click('#toggle-input-btn');
      
      // Verify recording UI elements
      await page.waitForSelector('#record-btn', { timeout: 1000 });
      await expect(page.locator('#record-btn')).toBeVisible();
      
      await page.waitForSelector('#recording-time', { timeout: 1000 });
      await expect(page.locator('#recording-time')).toBeVisible();
      
      // Testing the player element (would be shown after recording)
      if (await page.locator('#audio-player-container').count() > 0) {
        await expect(page.locator('#audio-player-container')).not.toBeVisible();
      }
    } catch (error) {
      console.error('Recording UI test failed:', error.message);
      await page.screenshot({ path: 'recording-ui-failure.png' });
      throw error;
    }
  });
}); 