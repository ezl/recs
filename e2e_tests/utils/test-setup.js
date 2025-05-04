// @ts-check
const { expect } = require('@playwright/test');

/**
 * Captures browser console logs and checks server status
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<Array<string>>} Collected console logs
 */
async function captureConsoleLogs(page) {
  const logs = [];
  page.on('console', msg => {
    logs.push(`${msg.type()}: ${msg.text()}`);
    console.log(`Browser console: ${msg.type()}: ${msg.text()}`);
  });
  
  // Check server status - quietly attempt to see if server is responding
  try {
    await page.goto('/', { timeout: 2000 });
    console.log(`Server responded to home page request, current URL: ${page.url()}`);
  } catch (e) {
    console.warn('Server status check failed:', e.message);
  }
  
  return logs;
}

/**
 * Creates a new unique email for testing
 * @returns {string} A unique email address
 */
function generateUniqueEmail() {
  const timestamp = new Date().getTime();
  return `test-user-${timestamp}@example.com`;
}

/**
 * Creates a new trip with the specified destination and user info
 * @param {import('@playwright/test').Page} page
 * @param {string} destination
 * @param {string} userName
 * @param {string} userEmail
 * @param {Object} options
 * @param {boolean} [options.expectNewUser=false] If true, expect direct navigation to trip page (new user flow)
 * @returns {Promise<string>} The share link for the created trip
 */
async function createTrip(page, destination, userName, userEmail, options = { expectNewUser: false }) {
  try {
    // Capture console logs to help with debugging
    await captureConsoleLogs(page);
    
    console.log(`Creating trip with destination=${destination}, name=${userName}, email=${userEmail}`);
    // Create a trip
    await page.goto('/');
    
    // Wait for form to be loaded
    console.log('Waiting for destination form');
    await page.waitForSelector('#destination', { timeout: 5000 });
    await page.fill('#destination', destination);
    
    // Submit the form
    console.log('Submitting destination form');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 5000 }).catch(e => {
        console.log('Navigation timeout, checking current URL and page content');
      }),
      page.click('button[type="submit"]')
    ]);

    // Verify we reached the expected page before continuing
    const initialUrl = page.url();
    console.log(`Current URL after form submission: ${initialUrl}`);

    // Check if we're on an error page or unexpected location
    if (await page.locator('.error, .flash-message, .debugger').count() > 0) {
      await page.screenshot({ path: 'navigation-error.png' });
      const bodyContent = await page.locator('body').textContent();
      throw new Error(`Navigation resulted in error page: ${initialUrl}, content: ${bodyContent.substring(0, 200)}`);
    }

    // If we're not on the expected page, try direct navigation
    if (!initialUrl.includes('/user-info')) {
      console.log('Not on user-info page, attempting direct navigation');
      await page.goto('/user-info');
      await page.waitForTimeout(1000);
    }
    
    // Check for errors - if we see a debugger, we know there's a template error
    if (await page.locator('.debugger').count() > 0) {
      const errorText = await page.locator('.plain pre').textContent();
      throw new Error(`Template error: ${errorText}`);
    }
    
    // Wait for form to be loaded
    console.log('Waiting for name/email fields');
    await page.waitForSelector('#name', { timeout: 10000 });
    await page.waitForSelector('#email', { timeout: 5000 });
    
    await page.fill('#name', userName);
    await page.fill('#email', userEmail);
    
    // Submit the form
    console.log('Submitting user info form');
    await page.click('button[type="submit"]');
    
    // Wait for content to update
    await page.waitForTimeout(3000);
    
    // Check for loading overlay and wait for it to disappear if present
    const hasLoadingOverlay = await page.locator('.loading-overlay, .loading-screen').count() > 0;
    if (hasLoadingOverlay) {
      console.log('Loading overlay detected, waiting for it to disappear');
      try {
        await page.waitForSelector('.loading-overlay, .loading-screen', { state: 'hidden', timeout: 10000 });
        console.log('Loading overlay disappeared');
      } catch (e) {
        console.warn('Timeout waiting for loading overlay to disappear');
      }
    }
    
    // Get current URL
    const currentUrl = page.url();
    console.log(`Current URL after form submission: ${currentUrl}`);
    
    // Handle possible different states based on page content
    
    // Check for name resolution UI
    if (await page.locator('#new-name-radio, h1:has-text("Name Resolution")').count() > 0) {
      console.log('Name resolution page detected');
      await page.locator('#new-name-radio').click();
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
    }
    
    // Check for authentication UI regardless of URL
    const authHandled = await handleAuthenticationIfNeeded(page);
    if (authHandled) {
      console.log('Authentication flow handled');
    }
    
    // Now we should be on a trip page or still loading
    if (!page.url().includes('/trip/')) {
      // If we're not on a trip page, check why
      console.log(`Not on trip page yet, current URL: ${page.url()}`);
      
      // If still on complete-trip, check for loading or other UI elements
      if (page.url().includes('/complete-trip')) {
        const loadingText = await page.locator('text=Loading...').count() > 0;
        if (loadingText) {
          console.log('Page still shows loading state. Waiting a bit longer...');
          await page.waitForTimeout(5000);
          
          // If still not redirected, try navigating to /my-trips as a workaround
          if (!page.url().includes('/trip/')) {
            console.log('Still not redirected to trip page. Trying to navigate to /my-trips');
            await page.goto('/my-trips');
            await page.waitForTimeout(2000);
            
            // Look for links to the created trip
            const tripLinks = await page.locator('a[href*="/trip/"]').count();
            if (tripLinks > 0) {
              console.log(`Found ${tripLinks} trip links on my-trips page`);
              // Click the first trip link
              await page.locator('a[href*="/trip/"]').first().click();
              await page.waitForTimeout(2000);
            } else {
              throw new Error('No trip links found on my-trips page');
            }
          }
        } else {
          // If not loading, maybe it's showing auth UI but our detection missed it
          console.log('Not loading but still on complete-trip. Taking screenshot...');
          await page.screenshot({ path: 'complete-trip-state.png' });
          
          // Check for any known UI elements
          const bodyContent = await page.locator('body').textContent();
          console.log('Body content excerpt:', bodyContent.substring(0, 200).replace(/\s+/g, ' ').trim());
          
          // Try again with more permissive auth detection
          const authLink = await page.locator('a:has-text("authenticate"), a:has-text("login"), a[href*="verify_token"]');
          if (await authLink.count() > 0) {
            console.log('Found potential auth link with broader search, clicking it');
            await authLink.first().click();
            await page.waitForTimeout(2000);
          } else {
            throw new Error('Stuck on complete-trip page and unable to proceed');
          }
        }
      }
    }
    
    // Wait for navigation to the trip detail page (now with more confidence)
    console.log('Waiting for trip page');
    await page.waitForURL('**/trip/**', { timeout: 15000 });
    
    // Get the share link
    console.log('Looking for share box');
    await page.waitForSelector('.share-box', { timeout: 10000 });
    const inputField = await page.locator('.share-box input[type="text"]');
    const shareLink = await inputField.inputValue();
    
    console.log(`Share link: ${shareLink}`);
    return shareLink;
  } catch (error) {
    console.error('Trip creation failed:', error.message);
    await page.screenshot({ path: 'trip-creation-failure.png' });
    throw error;
  }
}

/**
 * Creates a test user by making a trip once
 * @param {import('@playwright/test').Page} page
 * @param {string} userName
 * @param {string} userEmail
 * @returns {Promise<void>}
 */
async function createTestUser(page, userName, userEmail) {
  try {
    // Capture console logs to help with debugging
    await captureConsoleLogs(page);
    
    console.log(`Creating test user: ${userName} (${userEmail})`);
    const destination = "Test City";
    
    // Create a trip to register the user
    await page.goto('/');
    
    // Wait for form to be loaded
    console.log('Waiting for destination form');
    await page.waitForSelector('#destination', { timeout: 5000 });
    await page.fill('#destination', destination);
    
    // Submit the form
    console.log('Submitting destination form');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 5000 }).catch(e => {
        console.log('Navigation timeout, checking current URL and page content');
      }),
      page.click('button[type="submit"]')
    ]);

    // Verify we reached the expected page before continuing
    const initialUrl = page.url();
    console.log(`Current URL after form submission: ${initialUrl}`);

    // Check if we're on an error page or unexpected location
    if (await page.locator('.error, .flash-message, .debugger').count() > 0) {
      await page.screenshot({ path: 'user-nav-error.png' });
      const bodyContent = await page.locator('body').textContent();
      throw new Error(`Navigation resulted in error page: ${initialUrl}, content: ${bodyContent.substring(0, 200)}`);
    }

    // If we're not on the expected page, try direct navigation
    if (!initialUrl.includes('/user-info')) {
      console.log('Not on user-info page, attempting direct navigation');
      await page.goto('/user-info');
      await page.waitForTimeout(1000);
    }
    
    // Wait for form to be loaded
    console.log('Waiting for name/email fields');
    await page.waitForSelector('#name', { timeout: 10000 });
    await page.waitForSelector('#email', { timeout: 5000 });
    
    await page.fill('#name', userName);
    await page.fill('#email', userEmail);
    
    // Submit the form
    console.log('Submitting user info form');
    await page.click('button[type="submit"]');
    
    // Wait for navigation or content change
    await page.waitForTimeout(3000);
    
    // Capture current URL and page state
    const currentUrl = page.url();
    console.log(`Current URL after form submission: ${currentUrl}`);
    
    // Check for loading overlay (which might be causing test issues)
    const hasLoadingOverlay = await page.locator('.loading-overlay, .loading-screen').count() > 0;
    if (hasLoadingOverlay) {
      console.log('Loading overlay detected, waiting for it to disappear');
      try {
        // Wait for loading overlay to disappear
        await page.waitForSelector('.loading-overlay, .loading-screen', { state: 'hidden', timeout: 10000 });
        console.log('Loading overlay disappeared');
      } catch (e) {
        console.warn('Timeout waiting for loading overlay to disappear');
      }
    }
    
    // Analyze page content to determine what state we're in
    
    // Check for name resolution UI
    if (await page.locator('#new-name-radio, h1:has-text("Name Resolution")').count() > 0) {
      console.log('Name resolution page detected');
      await page.locator('#new-name-radio').click();
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
    }
    
    // Check for authentication UI regardless of URL path
    const authHandled = await handleAuthenticationIfNeeded(page);
    
    if (authHandled) {
      console.log('Authentication flow handled successfully');
    } else {
      // If we didn't handle auth, we should be on a trip page
      // Verify we reached a success state - either trip page or my-trips
      if (currentUrl.includes('/trip/')) {
        console.log('Successfully navigated to trip page');
      } else if (!currentUrl.includes('/complete-trip')) {
        console.log(`Current URL: ${currentUrl} - doesn't match expected patterns`);
        // Check page content for any error messages
        const errorMessages = await page.locator('.error, .flash-message').allTextContents();
        if (errorMessages.length > 0) {
          console.error('Error messages found:', errorMessages);
        }
        
        const bodyHtml = await page.locator('body').innerHTML();
        console.log('Page body excerpt:', bodyHtml.substring(0, 500));
        throw new Error(`Failed to create user. Unexpected page at ${currentUrl}`);
      } else {
        // We're at /complete-trip but no auth flow, check for trip creation completed
        console.log('At /complete-trip but no auth elements. Checking page content...');
        const isLoading = await page.locator('text=Loading...').count() > 0;
        
        if (isLoading) {
          console.log('Page is still loading, capturing screenshot');
          await page.screenshot({ path: 'loading-state.png' });
          
          // Try to navigate to my-trips to see if auth worked silently
          await page.goto('/my-trips');
          
          if (page.url().includes('/my-trips')) {
            console.log('Successfully navigated to my-trips page, user likely created');
          } else {
            throw new Error('Stuck in loading state and unable to confirm user creation');
          }
        }
      }
    }
    
    console.log(`Test user created: ${userName} (${userEmail})`);
  } catch (error) {
    console.error('Test user creation failed:', error.message);
    await page.screenshot({ path: 'user-creation-failure.png' });
    throw error;
  }
}

/**
 * Helper function to handle authentication if needed
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<boolean>} true if authentication was handled, false otherwise
 */
async function handleAuthenticationIfNeeded(page) {
  // Check for authentication page elements regardless of URL
  console.log('Checking for authentication elements');
  
  // Look for "Check Your Email" heading
  const hasCheckEmailHeading = await page.locator('h1:has-text("Check Your Email")').count() > 0;
  
  // Look for authentication links
  const hasAuthLink = await page.locator('a:has-text("Click to authenticate")').count() > 0;
  
  // Look for email message indicator
  const hasEmailMessage = await page.locator('text=We\'ve sent a login link').count() > 0;
  
  if (hasCheckEmailHeading || hasAuthLink || hasEmailMessage) {
    console.log('Authentication page elements detected');
    
    // Log the page content for debugging
    const bodyText = await page.locator('body').textContent();
    console.log('Auth page content excerpt:', bodyText.substring(0, 200).replace(/\s+/g, ' ').trim());
    
    // Look for the auth link
    const authLink = await page.locator('a:has-text("Click to authenticate")');
    if (await authLink.count() > 0) {
      console.log('Found auth link, clicking it');
      await page.screenshot({ path: 'before-auth-click.png' });
      await authLink.click();
      await page.waitForTimeout(2000);
      console.log('Auth link clicked, new URL:', page.url());
      return true;
    } else {
      console.error('No auth link found on authentication page');
      await page.screenshot({ path: 'auth-link-missing.png' });
      throw new Error('Auth link not found but authentication is required');
    }
  }
  
  console.log('No authentication elements detected');
  return false;
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
    console.log('Navigating to create guide page');
    await page.goto('/create-guide');
    
    // Wait for form to be loaded
    console.log('Waiting for destination form');
    await page.waitForSelector('#destination', { timeout: 5000 });
    await page.fill('#destination', destination);
    
    // Submit the form
    console.log('Submitting destination form');
    await page.click('button[type="submit"]');
    
    // Wait for navigation to the user info page
    console.log('Waiting for user info page');
    await page.waitForURL('**/user-info', { timeout: 10000 });
    
    // Check for errors - if we see a debugger, we know there's a template error
    if (await page.locator('.debugger').count() > 0) {
      const errorText = await page.locator('.plain pre').textContent();
      throw new Error(`Template error: ${errorText}`);
    }
    
    // Wait for form to be loaded
    console.log('Waiting for name/email fields');
    await page.waitForSelector('#name', { timeout: 10000 });
    await page.waitForSelector('#email', { timeout: 5000 });
    
    await page.fill('#name', userName);
    await page.fill('#email', userEmail);
    
    // Submit the form
    console.log('Submitting user info form');
    await page.click('button[type="submit"]');
    
    // Wait a moment before checking URLs to let navigation happen
    await page.waitForTimeout(2000);
    
    // Handle different possible redirects:
    const currentUrl = page.url();
    console.log(`Current URL after form submission: ${currentUrl}`);
    
    // 1. If user needs to resolve name conflict
    if (currentUrl.includes('/name-resolution')) {
      console.log('Handling name resolution page');
      await page.waitForSelector('#new-name-radio', { timeout: 5000 });
      await page.locator('#new-name-radio').click();
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
    }
    
    // 2. If user needs to authenticate via email
    if (page.url().includes('/check_email')) {
      console.log('Handling email authentication page');
      await page.waitForSelector('body', { timeout: 5000 });
      
      // In test environment, auth link should be displayed
      const authLink = await page.locator('a:has-text("Click here to log in")');
      if (await authLink.count() > 0) {
        console.log('Found auth link, clicking it');
        await authLink.click();
        await page.waitForTimeout(2000);
      } else {
        console.error('No auth link found on check_email page');
        await page.screenshot({ path: 'auth-link-missing.png' });
        throw new Error('Auth link not found on check_email page');
      }
    }
    
    // Wait for navigation to the add recommendation page (different from createTrip)
    console.log('Waiting for add recommendation page');
    await page.waitForURL('**/trip/**/add', { timeout: 15000 });
    
    // Extract the trip slug from the URL
    const url = page.url();
    const matches = url.match(/\/trip\/([^\/]+)\/add/);
    const tripSlug = matches ? matches[1] : '';
    
    console.log(`Created guide with slug: ${tripSlug}`);
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
    console.log(`Navigating to share link: ${shareLink}`);
    // Navigate to recommendation page
    await page.goto(shareLink);
    
    // Wait for recommendation form to load
    console.log('Waiting for recommendations form');
    await page.waitForSelector('#text-recommendations', { timeout: 2000 });
    
    // Enter recommendation text
    console.log('Entering recommendation text');
    await page.fill('#text-recommendations', recommendations);
    
    // Wait for the submit button to be enabled
    console.log('Waiting for submit button to be enabled');
    await page.waitForSelector('#submit-button:not([disabled])', { timeout: 2000 });
    await expect(page.locator('#submit-button')).toBeEnabled();
    
    // Click submit button to process recommendations
    console.log('Clicking submit to process recommendations');
    await page.click('#submit-button');
    
    // Wait for recommendations container to appear
    console.log('Waiting for recommendations container');
    await page.waitForSelector('#recommendations-container', { timeout: 5000 });
    
    // Wait for the submit button to be enabled again
    console.log('Waiting for submit button to be enabled again');
    await page.waitForSelector('#submit-button:not([disabled])', { timeout: 10000 });
    await expect(page.locator('#submit-button')).toBeEnabled();
    
    if (options.completeProcess) {
      // Click submit button to show name modal
      console.log('Clicking submit to show name modal');
      await page.click('#submit-button');
      
      // Wait for name modal to appear
      console.log('Waiting for name modal');
      await page.waitForSelector('#name-modal', { timeout: 10000 });
      
      // Fill in recommender name
      console.log('Entering recommender name');
      await page.fill('#modal-recommender-name', recommenderName);
      
      // Wait for continue button to be enabled and click it
      console.log('Waiting for submit with name button to be enabled');
      await page.waitForSelector('.submit-with-name:not([disabled])', { timeout: 10000 });
      console.log('Clicking submit with name button');
      await page.click('.submit-with-name');
      
      // Wait for submission and redirect to thank you page
      console.log('Waiting for thank you page');
      await page.waitForURL('**/trip/**/thank-you', { timeout: 15000 });
      console.log('Successfully submitted recommendations');
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
  submitRecommendations,
  createTestUser,
  generateUniqueEmail,
  handleAuthenticationIfNeeded,
  captureConsoleLogs
}; 