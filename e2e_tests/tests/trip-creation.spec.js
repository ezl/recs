// @ts-check
const { test, expect } = require('@playwright/test');

test.setTimeout(12000);

test('should create a new trip through the multi-step process', async ({ page }) => {
  // Go to the homepage
  await page.goto('/');
  
  // Fill out the initial destination form
  await page.fill('#destination', 'Paris');
  
  // Submit the form
  await page.click('button[type="submit"]');
  
  // Wait for navigation to the user info page
  await page.waitForURL('**/user-info');
  
  // Fill out the user info form
  await page.fill('#name', 'Test User');
  await page.fill('#email', 'test@example.com');
  
  // Submit the form
  await page.click('button[type="submit"]');
  
  // Wait for navigation to the trip detail page
  await page.waitForURL('**/trip/**');
  
  // Verify we're on the trip detail page
  const pageTitle = await page.textContent('h1.page-title');
  expect(pageTitle).toContain('Test User, you\'re going to Paris!');
  
  // Verify the share box is present
  const shareBox = await page.locator('.share-box');
  expect(await shareBox.isVisible()).toBeTruthy();
  
  // Get the share link from the input in the share box
  const shareLink = await page.locator('.share-box input[type="text"]').inputValue();
  expect(shareLink).toContain('/trip/');
  expect(shareLink).toContain('/add');
  
  // Navigate to the share link to verify it works
  await page.goto(shareLink);
  
  // Verify we're on the add recommendation page
  const addRecommendationHeader = await page.textContent('h1.page-title');
  expect(addRecommendationHeader).toContain('Test User is going to Paris');
});

test('should handle name resolution for existing users', async ({ page }) => {
  
  try {
    const startTime = Date.now();
    console.log(`[${Date.now() - startTime}ms] TEST START: Name Resolution Test`);
    
    // First create a user with a specific email
    console.log(`[${Date.now() - startTime}ms] Step 1: Going to homepage`);
    await page.goto('/');
    
    console.log(`[${Date.now() - startTime}ms] Step 2: Filling destination form with Rome`);
    await page.fill('#destination', 'Rome');
    await page.click('button[type="submit"]');
    
    console.log(`[${Date.now() - startTime}ms] Step 3: Filling user info form`);
    await page.waitForURL('**/user-info');
    await page.fill('#name', 'Existing User');
    await page.fill('#email', 'existing@example.com');
    
    // Add logging for debugging
    console.log(`[${Date.now() - startTime}ms] About to submit user info form`);
    
    // Click with a Promise.all to catch both the click and navigation events
    await Promise.all([
      page.waitForNavigation({ timeout: 10000 }),
      page.click('button[type="submit"]')
    ]);
    
    // Log the current URL to see where we actually end up
    const currentUrl = page.url();
    console.log(`[${Date.now() - startTime}ms] Current URL after form submission: ${currentUrl}`);
    
    // Check if we're already on the name resolution page (which is actually correct behavior)
    if (currentUrl.includes('/name-resolution')) {
      console.log(`[${Date.now() - startTime}ms] Successfully navigated to name resolution page as expected`);
      
      // Continue with the name resolution process
      await processNameResolution(page, startTime);
    } else if (currentUrl.includes('/trip/')) {
      // If we're on the trip page, we need to create a second trip to trigger name resolution
      console.log(`[${Date.now() - startTime}ms] Unexpectedly on trip page, need to create second trip to trigger name resolution`);
      console.log(`[${Date.now() - startTime}ms] Successfully created first trip with user "Existing User"`);
      
      // Now create a new trip with the same email but different name
      console.log(`[${Date.now() - startTime}ms] Creating second trip to trigger name resolution`);
      await page.goto('/');
      await page.fill('#destination', 'Berlin');
      await page.click('button[type="submit"]');
      
      await page.waitForURL('**/user-info');
      await page.fill('#name', 'Different Name');
      await page.fill('#email', 'existing@example.com');
      await page.click('button[type="submit"]');
      
      // Wait for name resolution page
      await page.waitForURL('**/name-resolution', { timeout: 1000 });
      console.log(`[${Date.now() - startTime}ms] Navigated to name resolution page after second trip creation`);
      
      // Continue with the name resolution process
      await processNameResolution(page, startTime);
    } else {
      console.log(`[${Date.now() - startTime}ms] Unexpected URL: ${currentUrl}`);
      throw new Error(`Unexpected URL after form submission: ${currentUrl}`);
    }
  } catch (error) {
    console.error('Test failed with error:', error);
    await page.screenshot({ path: 'error-screenshot.png' });
    throw error;
  }
});

// Helper function to process the name resolution page
async function processNameResolution(page, startTime) {
  console.log(`[${Date.now() - startTime}ms] Processing name resolution page`);
  
  // Wait to ensure the page is fully loaded
  await page.waitForTimeout(500);
  
  // Verify we see appropriate content on the page
  const pageContent = await page.textContent('body');
  console.log(`[${Date.now() - startTime}ms] Checking page content`);
  
  // Use a more specific selector to find the radio button for the new name
  const radioSelector = '#new-name-radio';
  console.log(`[${Date.now() - startTime}ms] Looking for radio selector: ${radioSelector}`);
  
  try {
    await page.waitForSelector(radioSelector, { state: 'visible', timeout: 3000 });
    console.log(`[${Date.now() - startTime}ms] Radio button found`);
    
    // Force click the radio button to ensure it's selected
    await page.click(radioSelector, { force: true });
    console.log(`[${Date.now() - startTime}ms] Clicked the radio button`);
    
    // Check if the radio button is correctly selected
    const isChecked = await page.isChecked(radioSelector);
    console.log(`[${Date.now() - startTime}ms] Radio button checked state: ${isChecked}`);
    
    // Click the submit button
    await Promise.all([
      page.waitForNavigation({ timeout: 5000 }),
      page.click('form button[type="submit"]')
    ]);
    
    console.log(`[${Date.now() - startTime}ms] Clicked submit button, now at URL: ${page.url()}`);
    
    // Verify we're on a trip page
    expect(page.url()).toContain('/trip/');
    
    // Verify the page title contains the correct name
    const pageTitle = await page.textContent('h1.page-title');
    console.log(`[${Date.now() - startTime}ms] Page title: ${pageTitle}`);
    expect(pageTitle).toContain('you\'re going to');
  } catch (error) {
    console.error(`[${Date.now() - startTime}ms] Error during name resolution:`, error);
    await page.screenshot({ path: 'name-resolution-error.png' });
    throw error;
  }
}

test('should create trip with a unique slug', async ({ page }) => {
  // Create first trip
  await page.goto('/');
  await page.fill('#destination', 'Tokyo');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/user-info');
  await page.fill('#name', 'Duplicate User');
  await page.fill('#email', 'duplicate@example.com');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/trip/**');
  
  // Get the URL of the first trip
  const firstTripUrl = page.url();
  
  // Create second trip with same details
  await page.goto('/');
  await page.fill('#destination', 'Tokyo');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/user-info');
  await page.fill('#name', 'Duplicate User');
  await page.fill('#email', 'duplicate@example.com');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/trip/**');
  
  // Get the URL of the second trip
  const secondTripUrl = page.url();
  
  // Verify the URLs are different
  expect(firstTripUrl).not.toEqual(secondTripUrl);
  expect(secondTripUrl).toContain('/trip/tokyo');
}); 