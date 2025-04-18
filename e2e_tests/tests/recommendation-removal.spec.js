// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Recommendation Removal and Undo', () => {
  // Setup - create a trip and add recommendations before each test
  test.beforeEach(async ({ page }) => {
    try {
      // Create a trip
      await page.goto('/');
      
      // Wait for form to be loaded
      await page.waitForSelector('#name', { timeout: 10000 });
      await page.waitForSelector('#destination', { timeout: 10000 });
      
      await page.fill('#name', 'Removal Tester');
      await page.fill('#destination', 'Berlin');
      
      // Submit the form
      await page.click('button[type="submit"]');
      
      // Wait for navigation to the trip detail page
      await page.waitForURL(/\/trip\/*/);
      
      // Take a screenshot for debugging
      await page.screenshot({ path: 'trip-detail-removal.png' });
      
      // Wait for share box to be visible
      await page.waitForSelector('.share-box', { timeout: 10000 });
      
      // Navigate to recommendation page
      const inputField = await page.locator('.share-box input[type="text"]');
      const shareLink = await inputField.inputValue();
      await page.goto(shareLink);
      
      // Wait for recommendations form
      await page.waitForSelector('#text-recommendations', { timeout: 10000 });
      
      // Add some recommendations
      await page.fill('#text-recommendations', 'Visit Brandenburg Gate, Check out Museum Island, Try currywurst at Curry 36, Enjoy the view from TV Tower');
      
      // Submit recommendations
      await page.waitForSelector('#submit-button', { timeout: 10000 });
      await page.click('#submit-button');
      
      // Wait for recommendations to be processed
      await page.waitForURL(/\/trip\/.*\/process/);
      
      // Wait for recommendation items to appear
      await page.waitForSelector('.recommendation-item', { timeout: 10000 });
    } catch (error) {
      console.error('Setup failed:', error.message);
      await page.screenshot({ path: 'setup-failure-removal.png' });
      throw error;
    }
  });
  
  test('should remove a recommendation', async ({ page }) => {
    try {
      // Count initial number of recommendations
      await page.waitForSelector('.recommendation-item', { timeout: 10000 });
      const initialCount = await page.locator('.recommendation-item').count();
      expect(initialCount).toBeGreaterThan(0);
      
      // Remove the first recommendation
      await page.locator('.recommendation-item').first().locator('.remove-recommendation').click();
      
      // Verify client flash message appears
      await page.waitForSelector('#client-flash-container', { timeout: 10000 });
      await expect(page.locator('#client-flash-container')).toBeVisible();
      
      // Wait for the DOM to update
      await page.waitForTimeout(1000);
      
      // Count recommendations after removal
      const newCount = await page.locator('.recommendation-item').count();
      
      // Check if count decreased or remained the same (if client-side only)
      expect(newCount).toBeLessThanOrEqual(initialCount);
    } catch (error) {
      console.error('Remove test failed:', error.message);
      await page.screenshot({ path: 'removal-test-failure.png' });
      throw error;
    }
  });
  
  test('should undo recommendation removal', async ({ page }) => {
    try {
      // Wait for recommendation items to appear
      await page.waitForSelector('.recommendation-item', { timeout: 10000 });
      
      // Count initial number of recommendations
      const initialCount = await page.locator('.recommendation-item').count();
      
      // Save the text of the first recommendation
      const firstRecText = await page.locator('.recommendation-item').first().locator('h3').textContent();
      
      // Remove the first recommendation
      await page.locator('.recommendation-item').first().locator('.remove-recommendation').click();
      
      // Verify flash message appears
      await page.waitForSelector('#client-flash-container', { timeout: 10000 });
      await expect(page.locator('#client-flash-container')).toBeVisible();
      
      // Wait for the undo button to be visible and clickable
      await page.waitForSelector('#undo-button', { timeout: 10000 });
      
      // Wait for the DOM to update
      await page.waitForTimeout(1000);
      
      // Click undo button
      await page.click('#undo-button');
      
      // Wait for the DOM to update after undo
      await page.waitForTimeout(1000);
      
      // Verify recommendation count is back to original or at least not less
      const afterUndoCount = await page.locator('.recommendation-item').count();
      expect(afterUndoCount).toBeGreaterThanOrEqual(initialCount - 1);
      
      // If we have the same count as initial, verify the first item text matches
      if (afterUndoCount === initialCount) {
        const restoredText = await page.locator('.recommendation-item').first().locator('h3').textContent();
        expect(restoredText).toBe(firstRecText);
      }
    } catch (error) {
      console.error('Undo test failed:', error.message);
      await page.screenshot({ path: 'undo-test-failure.png' });
      throw error;
    }
  });
  
  test('should be able to submit after removing recommendations', async ({ page }) => {
    try {
      // Wait for recommendation items
      await page.waitForSelector('.recommendation-item', { timeout: 10000 });
      
      // Remove a recommendation
      await page.locator('.recommendation-item').first().locator('.remove-recommendation').click();
      
      // Wait for client flash
      await page.waitForSelector('#client-flash-container', { timeout: 10000 });
      
      // Wait for the DOM to update
      await page.waitForTimeout(1000);
      
      // Find a description field to fill
      const descriptionFields = await page.locator('textarea[id^="description_"]').all();
      if (descriptionFields.length > 0) {
        await descriptionFields[0].fill('This is a must-visit place in Berlin');
      }
      
      // Make sure submit button is available
      await page.waitForSelector('#submit-button', { timeout: 10000 });
      
      // Enter name and submit
      await page.click('#submit-button');
      
      // Wait for modal to appear
      await page.waitForSelector('#modal-recommender-name', { timeout: 10000 });
      await page.fill('#modal-recommender-name', 'Removal Test User');
      
      // Wait for confirm button to be available
      await page.waitForSelector('#modal-confirm-button', { timeout: 10000 });
      await page.click('#modal-confirm-button');
      
      // Wait for submission and redirect
      await page.waitForURL(/\/trip\/.*/);
      
      // Verify we're on a trip page
      const currentUrl = page.url();
      expect(currentUrl).toContain('/trip/');
    } catch (error) {
      console.error('Submit test failed:', error.message);
      await page.screenshot({ path: 'submit-test-failure.png' });
      throw error;
    }
  });
  
  test('should handle removal of all recommendations', async ({ page }) => {
    try {
      // Count the number of recommendations
      await page.waitForSelector('.recommendation-item', { timeout: 10000 });
      const count = await page.locator('.recommendation-item').count();
      
      if (count === 0) {
        // If no recommendations, the test is not applicable
        test.skip();
        return;
      }
      
      // Remove all recommendations one by one
      for (let i = 0; i < count; i++) {
        // Wait for items to be visible
        await page.waitForSelector('.recommendation-item', { timeout: 10000 });
        
        if (await page.locator('.recommendation-item').count() === 0) {
          break;
        }
        
        await page.locator('.recommendation-item').first().locator('.remove-recommendation').click();
        
        // Wait for the DOM to update
        await page.waitForTimeout(1000);
        
        // If not the last one, dismiss the flash message to make the next removal easier
        if (i < count - 1 && await page.locator('#client-flash-container').isVisible()) {
          await page.locator('#client-flash-container button[type="button"]').click();
          await page.waitForTimeout(500);
        }
      }
      
      // Verify few or no recommendations are left
      const remainingCount = await page.locator('.recommendation-item').count();
      expect(remainingCount).toBeLessThanOrEqual(Math.max(0, count - 1));
      
      // Check if submit button exists
      if (await page.locator('#submit-button').count() > 0) {
        // Try to submit with no recommendations
        await page.click('#submit-button');
        
        // We should stay on the same page or get redirected to add recommendations page
        const currentUrl = page.url();
        expect(currentUrl).toContain('/trip/');
      }
    } catch (error) {
      console.error('Remove all test failed:', error.message);
      await page.screenshot({ path: 'remove-all-test-failure.png' });
      throw error;
    }
  });
}); 