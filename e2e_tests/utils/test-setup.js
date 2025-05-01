// @ts-check
const { expect } = require('@playwright/test');

/**
 * Creates a new trip with the specified destination and user info
 * @param {import('@playwright/test').Page} page
 * @param {string} destination
 * @param {string} userName
 * @param {string} userEmail
 * @returns {Promise<string>} The share link for the created trip
 */
async function createTrip(page, destination, userName, userEmail) {
  try {
    // Create a trip
    await page.goto('/');
    
    // Wait for form to be loaded
    await page.waitForSelector('#destination', { timeout: 5000 });
    await page.fill('#destination', destination);
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for navigation to the user info page
    await page.waitForURL('**/user-info');
    
    // Wait for form to be loaded
    await page.waitForSelector('#name', { timeout: 5000 });
    await page.waitForSelector('#email', { timeout: 5000 });
    
    await page.fill('#name', userName);
    await page.fill('#email', userEmail);
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for navigation to the trip detail page
    await page.waitForURL('**/trip/**');
    
    // Get the share link
    await page.waitForSelector('.share-box', { timeout: 5000 });
    const inputField = await page.locator('.share-box input[type="text"]');
    const shareLink = await inputField.inputValue();
    
    return shareLink;
  } catch (error) {
    console.error('Trip creation failed:', error.message);
    await page.screenshot({ path: 'trip-creation-failure.png' });
    throw error;
  }
}

/**
 * Creates a new guide (as opposed to requesting recommendations)
 * @param {import('@playwright/test').Page} page
 * @param {string} destination
 * @param {string} userName
 * @param {string} userEmail
 * @returns {Promise<string>} The trip slug for the created guide
 */
async function createGuide(page, destination, userName, userEmail) {
  try {
    // Navigate to the create guide page
    await page.goto('/create-guide');
    
    // Wait for form to be loaded
    await page.waitForSelector('#destination', { timeout: 5000 });
    await page.fill('#destination', destination);
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for navigation to the user info page
    await page.waitForURL('**/user-info');
    
    // Wait for form to be loaded
    await page.waitForSelector('#name', { timeout: 5000 });
    await page.waitForSelector('#email', { timeout: 5000 });
    
    await page.fill('#name', userName);
    await page.fill('#email', userEmail);
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Handle different possible redirects:
    
    // 1. If user needs to resolve name conflict
    if (page.url().includes('/name-resolution')) {
      // Select the new name radio button
      await page.locator('#new-name-radio').click();
      await page.click('button[type="submit"]');
    }
    
    // 2. If user needs to authenticate via email
    if (page.url().includes('/check_email')) {
      // In test environment, auth link should be displayed
      const authLink = await page.locator('a:has-text("Click here to log in")');
      if (await authLink.count() > 0) {
        await authLink.click();
      } else {
        throw new Error('Auth link not found on check_email page');
      }
    }
    
    // Wait for navigation to the add recommendation page (different from createTrip)
    await page.waitForURL('**/trip/**/add', { timeout: 10000 });
    
    // Extract the trip slug from the URL
    const url = page.url();
    const matches = url.match(/\/trip\/([^\/]+)\/add/);
    const tripSlug = matches ? matches[1] : '';
    
    return tripSlug;
  } catch (error) {
    console.error('Guide creation failed:', error.message);
    await page.screenshot({ path: 'guide-creation-failure.png' });
    throw error;
  }
}

/**
 * Submits recommendations for a trip and optionally completes the process
 * @param {import('@playwright/test').Page} page
 * @param {string} shareLink
 * @param {string} recommendations
 * @param {string} recommenderName
 * @param {Object} options
 * @param {boolean} [options.completeProcess=true] Whether to complete the full process including name submission
 * @returns {Promise<void>}
 */
async function submitRecommendations(page, shareLink, recommendations, recommenderName, options = { completeProcess: true }) {
  try {
    // Navigate to recommendation page
    await page.goto(shareLink);
    
    // Wait for recommendation form to load
    await page.waitForSelector('#text-recommendations', { timeout: 5000 });
    
    // Enter recommendation text
    await page.fill('#text-recommendations', recommendations);
    
    // Wait for the submit button to be enabled
    await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
    await expect(page.locator('#submit-button')).toBeEnabled();
    
    // Click submit button to process recommendations
    await page.click('#submit-button');
    
    // Wait for recommendations container to appear
    await page.waitForSelector('#recommendations-container', { timeout: 5000 });
    
    // Wait for the submit button to be enabled again
    await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
    await expect(page.locator('#submit-button')).toBeEnabled();
    
    if (options.completeProcess) {
      // Click submit button to show name modal
      await page.click('#submit-button');
      
      // Wait for name modal to appear
      await page.waitForSelector('#name-modal', { timeout: 5000 });
      
      // Fill in recommender name
      await page.fill('#modal-recommender-name', recommenderName);
      
      // Wait for continue button to be enabled and click it
      await page.waitForSelector('.submit-with-name:not([disabled])', { timeout: 5000 });
      await page.click('.submit-with-name');
      
      // Wait for submission and redirect to thank you page
      await page.waitForURL('**/trip/**/thank-you', { timeout: 5000 });
    }
  } catch (error) {
    console.error('Recommendation submission failed:', error.message);
    await page.screenshot({ path: 'recommendation-submission-failure.png' });
    throw error;
  }
}

module.exports = {
  createTrip,
  createGuide,
  submitRecommendations
}; 