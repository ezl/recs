// @ts-check
const { test, expect } = require('@playwright/test');
const { createTrip, submitRecommendations } = require('../utils/test-setup');

// Increase the test timeout since we're dealing with AI processing
test.setTimeout(30000);

/**
 * Tests the recommendation removal functionality:
 * 1. Removing a recommendation
 * 2. Undoing the removal
 */
test.describe('Recommendation Removal', () => {
  // Setup - create a trip and submit recommendations before each test
  test.beforeEach(async ({ page }) => {
    try {
      const shareLink = await createTrip(page, 'Berlin', 'Test Traveler', 'traveler@example.com');
      const recommendations = `
        Brandenburg Gate
        A historic landmark and symbol of Berlin's unity.
        
        Museum Island
        A UNESCO World Heritage site with five museums.
        
        Berlin Wall Memorial
        A memorial to the division of Berlin and its victims.
        
        Checkpoint Charlie
        The famous crossing point between East and West Berlin.
      `;
      await submitRecommendations(page, shareLink, recommendations, 'Test Recommender', { completeProcess: false });
    } catch (error) {
      console.error('Setup failed:', error.message);
      await page.screenshot({ path: 'setup-failure-removal.png' });
      throw error;
    }
  });
  
  test('should remove a recommendation', async ({ page }) => {
    // Get initial count of recommendations
    const initialRecommendations = await page.locator('.recommendation-item').count();
    console.log('Initial recommendation count:', initialRecommendations);
    
    // Get the first recommendation's text
    const firstRecommendation = await page.locator('.recommendation-item').first();
    const firstRecommendationText = await firstRecommendation.locator('input[name="recommendations[]"]').inputValue();
    console.log('First recommendation text:', firstRecommendationText);
    
    // Click the remove button on the first recommendation
    const removeButton = firstRecommendation.locator('.remove-recommendation');
    console.log('Clicked remove button');
    await removeButton.click();
    
    // Wait for flash message to appear
    console.log('Waiting for flash message...');
    const flashMessage = await page.locator('.flash-message');
    await expect(flashMessage).toBeVisible();
    
    // Get the type of flash message
    const flashMessageType = await flashMessage.getAttribute('data-type');
    console.log('Flash message type detected:', flashMessageType);
    
    // Verify the flash message content
    await expect(flashMessage).toContainText('Recommendation removed');
    await expect(flashMessage).toContainText('Undo');
    
    // Get the new count of recommendations
    const newRecommendations = await page.locator('.recommendation-item').count();
    expect(newRecommendations).toBe(initialRecommendations - 1);
  });
  
  test('should undo recommendation removal', async ({ page }) => {
    // Get initial count of recommendations
    const initialRecommendations = await page.locator('.recommendation-item').count();
    console.log('Initial recommendation count:', initialRecommendations);
    
    // Get the first recommendation's text
    const firstRecommendation = await page.locator('.recommendation-item').first();
    const firstRecommendationText = await firstRecommendation.locator('input[name="recommendations[]"]').inputValue();
    console.log('First recommendation text:', firstRecommendationText);
    
    // Click the remove button on the first recommendation
    const removeButton = firstRecommendation.locator('.remove-recommendation');
    console.log('Clicked remove button');
    await removeButton.click();
    
    // Wait for flash message to appear
    console.log('Waiting for flash message...');
    const flashMessage = await page.locator('.flash-message');
    await expect(flashMessage).toBeVisible();
    
    // Get the type of flash message
    const flashMessageType = await flashMessage.getAttribute('data-type');
    console.log('Flash message type detected:', flashMessageType);
    
    // Click the undo button in the flash message
    const undoButton = flashMessage.locator('button');
    console.log('Clicking inline undo button');
    await undoButton.click();
    
    // Wait for the flash message to disappear
    await expect(flashMessage).not.toBeVisible();
    
    // Get the new count of recommendations
    const afterUndoRecommendations = await page.locator('.recommendation-item').count();
    console.log('After undo recommendation count:', afterUndoRecommendations);
    expect(afterUndoRecommendations).toBe(initialRecommendations);
    
    // Verify the first recommendation is back with the same text
    const restoredRecommendation = await page.locator('.recommendation-item').first();
    const restoredText = await restoredRecommendation.locator('input[name="recommendations[]"]').inputValue();
    expect(restoredText).toBe(firstRecommendationText);
  });
}); 