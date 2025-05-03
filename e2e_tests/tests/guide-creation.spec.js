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
  // Store user email to reuse in returning user test
  let newUserEmail = `guide-test-${Date.now()}@example.com`;
  let tripSlug;
  
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
  
  /**
   * Test A: Create guide for a new user with fixed recommendations
   */
  test('should create guide for new user', async ({ page }) => {
    // City and recommendations for test
    const city = 'Chicago';
    const recommendations = [
      'Wrigley Field - this is where the Chicago Cubs play and such a fun place to catch a baseball game during the summer',
      'Lou Malnatis - a famous restaurant that is known for their deep dish pizza. my absolute favorite.'
    ];
    
    try {
      console.log('Starting test for new user guide creation');
      console.log(`Using email: ${newUserEmail}`);
      
      // 1. Navigate to homepage
      console.log('Navigating to homepage');
      await page.goto('/');
      
      // 2. Click "Create a guide" link
      console.log('Clicking create a guide link');
      await page.locator('a:has-text("Create A Guide")').first().click();
      
      // Verify we're on the create guide page
      await page.waitForURL('**/create-guide');
      
      // Check if create_mode is properly set up
      console.log('Checking for create_mode indicators on create guide page');
      const createPageContent = await page.content();
      console.log('Create page contains trip_mode references:', createPageContent.includes('trip_mode'));
      console.log('Create page contains create_mode references:', createPageContent.includes('create_mode'));
      
      // 3. Enter city name and submit form
      console.log(`Entering city: ${city}`);
      await page.fill('input[name="destination"]', city);
      
      // Try different button selectors as the ID might not be correct
      console.log('Looking for destination submit button');
      const submitButtonSelectors = [
        '#destination-submit-button',
        'button[type="submit"]',
        'button:has-text("Create Guide")',
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'input[type="submit"]'
      ];
      
      let buttonFound = false;
      for (const selector of submitButtonSelectors) {
        const isVisible = await page.locator(selector).isVisible().catch(() => false);
        if (isVisible) {
          console.log(`Found submit button with selector: ${selector}`);
          await page.click(selector);
          buttonFound = true;
          break;
        }
      }
      
      if (!buttonFound) {
        console.error('Could not find destination submit button');
        await page.screenshot({ path: 'missing-submit-button.png' });
        throw new Error('Destination submit button not found');
      }
      
      // 4. Wait for loading overlay and then continue
      console.log('Checking for loading overlay');
      await page.waitForSelector('.loading-overlay', { state: 'visible', timeout: 3000 }).catch(() => {
        console.log('Loading overlay not seen, continuing anyway');
      });
      
      // Enter user info
      console.log('Entering user info');
      await page.waitForSelector('input[name="name"]', { timeout: 5000 });
      await page.fill('input[name="name"]', 'New Guide Tester');
      await page.fill('input[name="email"]', newUserEmail);
      
      // Check URL before submitting user info form to verify we're in the right flow
      console.log('Current URL before submitting user info:', page.url());
      
      await page.click('button[type="submit"]');
      
      // 5. Wait for recommendations page (timeout of 5 seconds)
      console.log('Waiting for recommendations page');
      await page.waitForURL('**/trip/**/add', { timeout: 5000 });
      console.log(`Navigated to: ${page.url()}`);
      
      // Check if trip_mode is properly set for add recommendations page
      console.log('Checking for create_mode indicators on add recommendations page');
      const addRecsContent = await page.content();
      console.log('Add recs page contains trip_mode references:', addRecsContent.includes('trip_mode'));
      console.log('Add recs page contains create_mode references:', addRecsContent.includes('create_mode'));
      
      // Look for heading specific to create_mode
      const headerText = await page.locator('h1.page-title').textContent();
      console.log('Page title text:', headerText);
      console.log('Page title contains expected create_mode text:', 
                  headerText.includes('Share your favorite places in'));
      
      // 6. Add the recommendations
      console.log('Adding recommendations');
      await page.fill('#text-recommendations', recommendations.join('\n\n'));
      
      // Wait for submit button to be enabled
      await page.waitForSelector('#submit-button:not([disabled])', { timeout: 5000 });
      
      // 7. Submit the recommendations
      console.log('Submitting recommendations');
      await page.click('#submit-button');
      
      // 8. Wait for processing page (timeout of 5 seconds)
      console.log('Waiting for processing page');
      await page.waitForURL('**/trip/**/process', { timeout: 5000 });
      console.log(`Navigated to: ${page.url()}`);
      
      // Check if trip_mode is properly set for process page
      console.log('Checking for create_mode indicators on process page');
      const processPageContent = await page.content();
      console.log('Process page contains trip_mode references:', processPageContent.includes('trip_mode'));
      console.log('Process page contains create_mode references:', processPageContent.includes('create_mode'));
      
      // Add JavaScript to check data attributes and variables
      console.log('Checking data-trip-mode attribute and JavaScript variables');
      const tripModeData = await page.evaluate(() => {
        // Check for trip_mode in the DOM
        const tripModeElement = document.querySelector('[data-trip-mode]');
        const formElement = document.getElementById('recommendations-form');
        
        // Log modal elements
        const nameModal = document.getElementById('name-modal');
        const modalVisible = nameModal && !nameModal.classList.contains('hidden');
        
        return {
          tripModeElementExists: !!tripModeElement,
          tripModeValue: tripModeElement ? tripModeElement.getAttribute('data-trip-mode') : null,
          formExists: !!formElement,
          sessionStorageKeys: Object.keys(sessionStorage),
          modalExists: !!nameModal,
          modalVisible: modalVisible,
          documentHTML: document.documentElement.outerHTML.substring(0, 500) // First 500 chars for brevity
        };
      });
      console.log('Trip mode data from page:', JSON.stringify(tripModeData, null, 2));
      
      // Take a screenshot before submit button click
      await page.screenshot({ path: 'before-final-submit.png' });
      
      // 9. Submit the form on the processing page
      console.log('Submitting processed recommendations');
      await page.waitForSelector('#submit-button:not([disabled])', { timeout: 10000 });
      
      // Inject logging JavaScript before clicking submit
      await page.evaluate(() => {
        // Override the original event listener
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
          if (type === 'click' && this.id === 'submit-button') {
            console.log('[INJECT] Submit button click event being attached');
            
            // Wrap the listener to log before execution
            const wrappedListener = function(event) {
              console.log('[INJECT] Submit button clicked, about to execute handler');
              
              // Log trip mode state
              const tripModeElement = document.querySelector('[data-trip-mode]');
              const tripMode = tripModeElement ? tripModeElement.dataset.tripMode : 'request_mode';
              console.log('[INJECT] Trip mode check vars:', {
                elementExists: !!tripModeElement,
                tripMode: tripMode,
                condition: tripMode === 'create_mode'
              });
              
              return listener.apply(this, arguments);
            };
            
            return originalAddEventListener.call(this, type, wrappedListener, options);
          }
          return originalAddEventListener.call(this, type, listener, options);
        };
        
        // Also log when the modal is shown
        const originalShowModal = window.showModal;
        if (originalShowModal) {
          window.showModal = function(modalId) {
            console.log('[INJECT] showModal called with:', modalId);
            console.log('[INJECT] Current trip_mode:', document.querySelector('[data-trip-mode]')?.dataset.tripMode);
            return originalShowModal.apply(this, arguments);
          };
        }
        
        console.log('[INJECT] Modal and submit logging hooks installed');
      });
      
      // Click submit and listen for console logs
      page.on('console', msg => {
        if (msg.text().startsWith('[INJECT]')) {
          console.log(`Browser log: ${msg.text()}`);
        }
      });
      
      await page.click('#submit-button');
      
      // Wait a moment to capture logs
      await page.waitForTimeout(1000);
      
      // Check for modal right after submit click
      console.log('Checking for name modal appearance immediately after submit');
      const modalVisible = await page.locator('#name-modal').isVisible().catch(() => false);
      console.log(`Modal visible after submit: ${modalVisible}`);
      
      if (modalVisible) {
        console.log('Taking screenshot of unexpected modal');
        await page.screenshot({ path: 'unexpected-modal.png' });
        
        // Log the modal contents
        const modalContent = await page.locator('#name-modal').innerHTML();
        console.log('Modal HTML:', modalContent.substring(0, 500)); // First 500 chars
        
        // Check page state
        console.log('Checking page state with visible modal');
        const pageWithModal = await page.evaluate(() => {
          return {
            url: window.location.href,
            tripMode: document.querySelector('[data-trip-mode]')?.dataset.tripMode || 'not found',
            modalTitle: document.getElementById('name-modal-title')?.textContent.trim() || 'not found',
            formAction: document.getElementById('recommendations-form')?.action || 'not found'
          };
        });
        console.log('Page state with modal:', pageWithModal);
      }
      
      // 10. Verify no name modal appears
      console.log('Checking that name modal does NOT appear');
      const finalModalVisible = await page.locator('#name-modal, #modal-recommender-name').isVisible().catch(() => false);
      expect(finalModalVisible).toBe(false);
      
      // If there's a modal, try to dismiss it to continue the test
      if (finalModalVisible) {
        console.log('Unexpected modal found, trying to interact with it to continue test');
        
        // Try to fill the name and submit
        await page.fill('#modal-recommender-name', 'New Guide Tester').catch(() => {});
        await page.click('.submit-with-name').catch(() => {});
        
        // Alternative: try to close the modal
        await page.click('.modal-backdrop').catch(() => {});
      }
      
      // 11. Verify we're on the trip page for Chicago
      console.log('Verifying we are on trip page');
      await page.waitForURL('**/trip/**', { timeout: 5000 });
      
      // Check the page title contains Chicago
      const pageTitle = await page.locator('h1.page-title').textContent();
      console.log('Trip page title:', pageTitle);
      expect(pageTitle).toContain('Chicago');
      
      // 12. Verify recommendation cards match our input
      console.log('Checking recommendation cards');
      const cards = await page.locator('.recommendation-card').all();
      expect(cards.length).toBeGreaterThanOrEqual(2);
      
      // Get the text content of each card and check against our recommendations
      let foundWrigley = false;
      let foundLouMalnatis = false;
      
      for (const card of cards) {
        const cardText = await card.textContent();
        if (cardText.includes('Wrigley Field') && cardText.includes('Cubs')) {
          foundWrigley = true;
        }
        if (cardText.includes('Lou Malnatis') && cardText.includes('deep dish pizza')) {
          foundLouMalnatis = true;
        }
      }
      
      expect(foundWrigley).toBe(true);
      expect(foundLouMalnatis).toBe(true);
      
      console.log('Test completed successfully');
    } catch (error) {
      console.error('New user guide creation test failed:', error.message);
      await page.screenshot({ path: 'new-user-guide-failure.png' });
      throw error;
    }
  });
}); 