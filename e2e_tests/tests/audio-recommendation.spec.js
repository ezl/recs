// @ts-check
const { test, expect } = require('@playwright/test');
const { 
  createTrip,
  generateUniqueEmail 
} = require('../utils/test-setup');

test.setTimeout(10000);

test.describe('Audio Recording Interface', () => {
  let shareLink;

  // Setup - just navigate to a recommendation page once for all tests
  test.beforeAll(async ({ browser }) => {
    // Create a test trip once to get a share link we can use for all tests
    const context = await browser.newContext();
    const page = await context.newPage();
    try {
      // Create a trip with a unique email to get a share link
      const uniqueEmail = generateUniqueEmail();
      shareLink = await createTrip(page, 'Test City', 'Audio Test User', uniqueEmail);
      
      // Verify share link exists and has the expected format
      console.log(`Share link for audio tests: ${shareLink}`);
      expect(shareLink).toBeTruthy();
      expect(shareLink).toContain('/add/');
    } catch (error) {
      console.error('Setup failed:', error.message);
      await page.screenshot({ path: 'audio-setup-failure.png' });
      throw error;
    } finally {
      await context.close();
    }
  });

  test('should toggle to audio mode and attempt to access microphone', async ({ page, context, browserName }) => {
    // Handle permissions differently based on browser
    // Note: WebKit (Safari) doesn't support direct permission granting through API
    // Chromium and Firefox do support it
    if (browserName !== 'webkit') {
      await context.grantPermissions(['microphone']);
    } else {
      console.log('Skipping permission granting for WebKit as it is not supported');
      // For WebKit, we can only verify the UI changes, not the actual microphone access
    }
    
    // Navigate directly to the recommendation page
    await page.goto(shareLink);
    
    // Verify initially in text mode
    await page.waitForSelector('#text-input-container', { state: 'visible', timeout: 3000 });
    await expect(page.locator('#text-input-container')).toBeVisible();
    
    // Verify audio mode is hidden
    await expect(page.locator('#audio-input-container')).not.toBeVisible();
    
    // Make sure toggle button exists
    await page.waitForSelector('#toggle-input-btn', { timeout: 3000 });
    
    // Take screenshot before toggle
    await page.screenshot({ path: 'before-audio-toggle.png' });
    
    // Click the toggle button to switch to audio mode
    await page.click('#toggle-input-btn');
    
    // Now audio input should be visible
    await page.waitForSelector('#audio-input-container', { state: 'visible', timeout: 3000 });
    await expect(page.locator('#audio-input-container')).toBeVisible();
    
    // Text input should be hidden
    await expect(page.locator('#text-input-container')).not.toBeVisible();
    
    // Verify microphone UI elements are visible
    await expect(page.locator('#record-btn')).toBeVisible();
    
    // For non-WebKit browsers, we can verify more behavior
    if (browserName !== 'webkit') {
      // The recording should start automatically and show recording status
      await page.waitForSelector('#recording-status', { state: 'visible', timeout: 3000 });
      await expect(page.locator('#recording-status')).toBeVisible();
    }
    
    // Take screenshot of audio mode
    await page.screenshot({ path: `audio-mode-active-${browserName}.png` });
  });
  
  test('should toggle back from audio to text mode', async ({ page }) => {
    // Navigate directly to the recommendation page
    await page.goto(shareLink);
    
    // Verify page loaded with text mode active
    await page.waitForSelector('#text-input-container', { state: 'visible', timeout: 3000 });
    
    // Switch to audio mode first
    await page.click('#toggle-input-btn');
    await page.waitForSelector('#audio-input-container', { state: 'visible', timeout: 3000 });
    
    // Now click toggle again to switch back to text mode
    await page.click('#toggle-input-btn');
    
    // Verify text input container is visible again
    await page.waitForSelector('#text-input-container', { state: 'visible', timeout: 3000 });
    await expect(page.locator('#text-input-container')).toBeVisible();
    
    // Audio input should be hidden
    await expect(page.locator('#audio-input-container')).not.toBeVisible();
  });
}); 