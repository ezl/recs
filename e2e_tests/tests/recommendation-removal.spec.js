// @ts-check
const { test, expect } = require('@playwright/test');
const { createTrip } = require('../utils/test-setup');

/**
 * Helper function to set up the test environment once
 */
async function setupTestEnvironment(page) {
  try {
    console.log('Setting up test environment for recommendation removal tests');
    
    // Create a trip with test user details
    const userName = 'Recommendation Test User';
    const userEmail = 'recommendation-test@example.com';
    const destination = 'Berlin';
    
    // Create a trip using our improved utility function
    console.log('Creating test trip');
    const shareLink = await createTrip(page, destination, userName, userEmail);
    console.log(`Share link for recommendations: ${shareLink}`);
    
    // Navigate to the add recommendation page using the share link
    console.log('Navigating to add recommendation page');
    await page.goto(shareLink);
    
    // Add some text recommendations
    console.log('Adding text recommendations');
    await page.waitForSelector('#text-recommendations', { timeout: 10000 });
    await page.fill('#text-recommendations', 'Visit Brandenburg Gate, Check out Museum Island, Try currywurst at Curry 36, Enjoy the view from TV Tower');
    
    // Submit recommendations
    console.log('Submitting recommendations');
    await page.waitForSelector('#submit-button', { timeout: 10000 });
    await page.click('#submit-button');
    
    // Wait for recommendations to be processed
    console.log('Waiting for recommendations to be processed');
    await page.waitForURL('**/trip/**/process', { timeout: 15000 });
    
    // Wait for recommendation items to appear
    console.log('Waiting for recommendation items to appear');
    await page.waitForSelector('.recommendation-item', { timeout: 10000 });
    
    // Take a baseline screenshot
    await page.screenshot({ path: 'recommendation-setup-complete.png' });
    
    console.log('Test environment setup complete');
    return true;
  } catch (error) {
    console.error('Setup failed:', error.message);
    await page.screenshot({ path: 'setup-failure.png' });
    throw error;
  }
}

/**
 * Verify if a flash message appears on the page
 */
async function verifyFlashMessage(page) {
  console.log('Waiting for flash message');
  try {
    await Promise.race([
      page.waitForSelector('.inline-flash-message', { timeout: 5000, state: 'visible' }),
      page.waitForSelector('#client-flash-container:not(.hidden)', { timeout: 5000, state: 'visible' })
    ]);
    console.log('Flash message appeared');
    return true;
  } catch (error) {
    console.warn('Flash message not detected:', error.message);
    await page.screenshot({ path: 'missing-flash.png' });
    return false;
  }
}

/**
 * Get the type of flash message that's visible
 */
async function getFlashMessageType(page) {
  const hasInlineFlash = await page.locator('.inline-flash-message').isVisible().catch(() => false);
  const hasGlobalFlash = await page.locator('#client-flash-container:not(.hidden)').isVisible().catch(() => false);
  
  if (hasInlineFlash) return 'inline';
  if (hasGlobalFlash) return 'global';
  return null;
}

/**
 * Click the undo button in the flash message
 */
async function clickUndoButton(page) {
  console.log('Attempting to locate and click undo button');
  
  // Wait a bit longer to make sure the flash message and undo button are fully rendered
  await page.waitForTimeout(1000);
  
  // Take a screenshot to help with debugging
  await page.screenshot({ path: 'before-undo-attempt.png' });
  
  // First, check for inline flash message with undo button
  const inlineUndo = page.locator('.inline-flash-message .inline-undo-button');
  const inlineUndoVisible = await inlineUndo.isVisible().catch(() => false);
  
  if (inlineUndoVisible) {
    console.log('Found inline undo button, clicking it');
    await inlineUndo.scrollIntoViewIfNeeded();
    await inlineUndo.click().catch(async error => {
      console.warn(`Error clicking inline undo: ${error.message}`);
      await page.screenshot({ path: 'inline-undo-error.png' });
    });
    return true;
  }
  
  // Next, check for global flash message with undo button
  const globalUndo = page.locator('#client-flash-container #undo-button');
  const globalUndoVisible = await globalUndo.isVisible().catch(() => false);
  
  if (globalUndoVisible) {
    console.log('Found global undo button, clicking it');
    await globalUndo.scrollIntoViewIfNeeded();
    await globalUndo.click().catch(async error => {
      console.warn(`Error clicking global undo: ${error.message}`);
      await page.screenshot({ path: 'global-undo-error.png' });
    });
    return true;
  }
  
  // If we didn't find any undo button with the expected selectors,
  // try a more generic approach to find any element that looks like an undo button
  console.log('Standard undo buttons not found, trying generic selectors');
  
  // Get the DOM content for debugging
  const bodyContent = await page.locator('body').textContent();
  console.log('Page content excerpt:', bodyContent.substring(0, 500));
  
  // Try any of these potential undo buttons
  const potentialUndoSelectors = [
    'button:has-text("Undo")',
    'a:has-text("Undo")',
    '[aria-label="Undo"]',
    '.undo',
    '[data-action="undo"]'
  ];
  
  for (const selector of potentialUndoSelectors) {
    const element = page.locator(selector);
    const isVisible = await element.isVisible().catch(() => false);
    
    if (isVisible) {
      console.log(`Found potential undo element with selector: ${selector}`);
      await element.scrollIntoViewIfNeeded();
      await element.click().catch(async error => {
        console.warn(`Error clicking potential undo element: ${error.message}`);
        await page.screenshot({ path: 'potential-undo-error.png' });
      });
      return true;
    }
  }
  
  // If we still haven't found it, try another approach
  console.log('No undo button found with any selector. Taking screenshot for debugging.');
  await page.screenshot({ path: 'no-undo-button-found.png' });
  
  // Log the HTML structure around flash messages for debugging
  const flashHTML = await page.locator('body').innerHTML();
  console.log('Flash area HTML excerpt:', flashHTML.substring(0, 1000));
  
  // As a fallback, check if the recommendation count has already returned to the expected value
  // This might happen if the UI is auto-updating or there's a non-standard undo mechanism
  return false;
}

/**
 * Remove a recommendation at the specified index
 */
async function removeRecommendation(page, index = 0) {
  // Get the current count
  const initialCount = await page.locator('.recommendation-item').count();
  console.log(`Initial recommendation count: ${initialCount}`);
  
  if (initialCount <= index) {
    console.warn(`Cannot remove recommendation at index ${index}, only ${initialCount} recommendations exist`);
    return { success: false, initialCount, newCount: initialCount };
  }
  
  // Ensure the remove button is visible
  console.log(`Locating remove button for item ${index + 1}`);
  const removeButton = page.locator('.recommendation-item').nth(index).locator('.remove-recommendation');
  
  try {
    await removeButton.waitFor({ state: 'visible', timeout: 5000 });
  } catch (error) {
    console.warn(`Remove button not visible: ${error.message}`);
    await page.screenshot({ path: 'remove-button-not-visible.png' });
    return { success: false, initialCount, newCount: initialCount };
  }
  
  // Remove the recommendation
  console.log('Clicking remove button');
  await removeButton.click();
  
  // Wait for the flash message
  await verifyFlashMessage(page);
  
  // Wait for the DOM to update
  await page.waitForTimeout(1500);
  
  // Count recommendations after removal
  const newCount = await page.locator('.recommendation-item').count();
  console.log(`New recommendation count: ${newCount}`);
  
  return { 
    success: newCount < initialCount, 
    initialCount, 
    newCount 
  };
}

/**
 * Test 1: Tests recommendation removal functionality including:
 * - Single recommendation removal
 * - Undo recommendation removal
 */
test('should remove and undo recommendation removal', async ({ page }) => {
  test.setTimeout(60000);
  
  // Set up the test environment
  await setupTestEnvironment(page);
  
  console.log('Starting recommendation removal and undo test');
  
  // 1. First, test basic removal
  console.log('PART 1: Testing removal');
  const { success, initialCount, newCount } = await removeRecommendation(page);
  
  // Verify removal was successful
  expect(success).toBeTruthy();
  expect(newCount).toBe(initialCount - 1);
  console.log('Removal verified successfully');
  
  // 2. Next, test removal and undo on another recommendation
  console.log('PART 2: Testing undo functionality');
  
  // Try removing a different recommendation
  const secondRemoveResult = await removeRecommendation(page, 0);
  expect(secondRemoveResult.success).toBeTruthy();
  
  // Take screenshot before undo
  await page.screenshot({ path: 'before-undo.png' });
  
  // Record the recommendation count before attempting undo
  const preUndoCount = await page.locator('.recommendation-item').count();
  console.log(`Recommendation count before undo attempt: ${preUndoCount}`);
  
  // Try to undo the removal
  const undoSuccess = await clickUndoButton(page);
  
  // The test should fail if we couldn't find an undo button
  if (!undoSuccess) {
    console.error('❌ CRITICAL ERROR: Undo button could not be found');
    await page.screenshot({ path: 'undo-button-failure.png' });
    
    // Log more details about the page to help with debugging
    const pageContent = await page.content();
    console.log('Page HTML at failure point:\n', pageContent.substring(0, 1000));
    
    // Fail the test explicitly
    expect(undoSuccess, 'Undo button should be present and clickable').toBeTruthy();
  }
  
  // Wait for the DOM to update
  console.log('Waiting for DOM update after undo attempt');
  await page.waitForTimeout(2000);
  
  // Verify recommendation count after undo attempt
  const afterUndoCount = await page.locator('.recommendation-item').count();
  console.log(`After undo recommendation count: ${afterUndoCount}`);
  
  // The count should be at least as high as after the first removal
  expect(afterUndoCount).toBeGreaterThanOrEqual(newCount);
  console.log('Undo functionality verified successfully');
});

/**
 * Test 2: Tests submitting after removing a recommendation
 */
test('should submit recommendations after removal', async ({ page }) => {
  test.setTimeout(60000);
  
  // Set up the test environment
  await setupTestEnvironment(page);
  
  console.log('Starting submit after removal test');
  
  // Remove a recommendation first
  const { success } = await removeRecommendation(page);
  expect(success).toBeTruthy();
  
  // Find a description field to fill if any exist
  console.log('Looking for description fields');
  const descriptionFields = await page.locator('textarea[id^="description_"]').all();
  if (descriptionFields.length > 0) {
    console.log(`Found ${descriptionFields.length} description fields, filling the first one`);
    await descriptionFields[0].fill('This is a must-visit place in Berlin');
  } else {
    console.log('No description fields found');
  }
  
  // Make sure submit button is available and enabled
  console.log('Waiting for submit button');
  await page.waitForSelector('#submit-button:not([disabled])', { timeout: 10000 });
  
  // Take screenshot before submitting
  await page.screenshot({ path: 'before-submit.png' });
  
  // Click submit button
  console.log('Clicking submit button');
  await page.click('#submit-button');
  
  // Wait for modal to appear
  console.log('Waiting for recommender name modal');
  await page.waitForSelector('#modal-recommender-name', { timeout: 10000 });
  
  // Fill in the recommender name
  console.log('Filling recommender name');
  await page.fill('#modal-recommender-name', 'Removal Test User');
  
  // Wait for confirm button to be available
  console.log('Waiting for submit with name button');
  await page.waitForSelector('.submit-with-name:not([disabled])', { timeout: 5000 });
  
  // Click the submit button in the modal
  console.log('Clicking submit with name button');
  await page.click('.submit-with-name');
  
  // Wait for submission and redirect with increased timeout
  console.log('Waiting for redirect after submission');
  await page.waitForURL('**/trip/**', { timeout: 15000 });
  
  // Verify we're on a trip page
  const currentUrl = page.url();
  console.log(`Final URL after submission: ${currentUrl}`);
  expect(currentUrl).toContain('/trip/');
  
  console.log('Submit after removal test completed successfully');
});

/**
 * Test 3: Tests removal of multiple recommendations
 * This is a separate test since it makes significant changes that 
 * would interfere with other tests.
 */
test('should handle removal of multiple recommendations', async ({ page }) => {
  test.setTimeout(60000);
  
  // Set up the test environment
  await setupTestEnvironment(page);
  
  console.log('Starting multiple recommendation removal test');
  
  // Count the number of recommendations
  const count = await page.locator('.recommendation-item').count();
  console.log(`Initial recommendation count: ${count}`);
  
  if (count === 0) {
    // If no recommendations, the test is not applicable
    console.log('No recommendations found, skipping test');
    test.skip();
    return;
  }
  
  // In this test we'll try to remove all but one recommendation
  // (leaving one to make sure we can still submit)
  const targetToRemove = Math.max(1, count - 1);
  console.log(`Will attempt to remove ${targetToRemove} of ${count} recommendations`);
  
  // Remove recommendations one by one
  for (let i = 0; i < targetToRemove; i++) {
    console.log(`Removing recommendation ${i+1} of ${targetToRemove}`);
    
    // Check if there are still recommendations to remove (besides the last one)
    const visibleItems = await page.locator('.recommendation-item').count();
    if (visibleItems <= 1) {
      console.log('Only one recommendation left, stopping removal');
      break;
    }
    
    // Try to remove the recommendation
    const { success } = await removeRecommendation(page, 0);
    
    if (!success) {
      console.warn(`Failed to remove recommendation ${i+1}, will try next one`);
      continue;
    }
    
    // Try to dismiss the flash message if it's visible
    try {
      const flashType = await getFlashMessageType(page);
      if (flashType === 'inline') {
        console.log('Dismissing inline flash');
        await page.locator('.inline-flash-message .dismiss-button').click().catch(() => {});
      } else if (flashType === 'global') {
        console.log('Dismissing global flash');
        await page.locator('#client-flash-container button[type="button"]').click().catch(() => {});
      }
    } catch (error) {
      console.warn(`Failed to dismiss flash: ${error.message}`);
    }
    
    // Wait a bit for the UI to stabilize
    await page.waitForTimeout(1000);
  }
  
  // Verify recommendations were removed
  const remainingCount = await page.locator('.recommendation-item').count();
  console.log(`Remaining recommendations: ${remainingCount}`);
  
  // We should have removed at least one recommendation
  expect(remainingCount).toBeLessThan(count);
  console.log('Multiple removal test completed successfully');
  
  // Try to submit the remaining recommendations
  if (remainingCount > 0) {
    // Check if submit button exists and try to submit
    console.log('Checking for submit button after removing multiple recommendations');
    const submitExists = await page.locator('#submit-button').isVisible().catch(() => false);
    
    if (submitExists) {
      console.log('Submit button found, verifying it works after multiple removals');
      // We don't actually submit here to keep the test focused,
      // just verify the button is enabled
      await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
      expect(await page.locator('#submit-button').isEnabled()).toBeTruthy();
    } else {
      console.log('Submit button not found after removing multiple recommendations');
    }
  }
}); 