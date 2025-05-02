// @ts-check
const { test, expect } = require('@playwright/test');
const { 
  createTrip, 
  submitRecommendations, 
  createTestUser, 
  generateUniqueEmail 
} = require('../utils/test-setup');

// Increase the test timeout for tests dealing with API/AI processing
test.setTimeout(30000);

/**
 * Test for new user trip creation flow
 */
test.describe('New User Trip Creation', () => {
  test('should create a trip for a new user and redirect to trip page', async ({ page }) => {
    try {
      // Generate unique email to ensure new user
      const uniqueEmail = generateUniqueEmail();
      console.log(`Testing with unique email: ${uniqueEmail}`);
      
      // Create trip with expectNewUser: true to verify direct navigation
      const shareLink = await createTrip(
        page, 
        'Paris', 
        'New Test User', 
        uniqueEmail, 
        { expectNewUser: true }
      );
      
      // Verify we're on the trip page
      expect(page.url()).toContain('/trip/');
      
      // Verify share link exists
      expect(shareLink).toBeTruthy();
      expect(shareLink).toContain('/add');
      
      // Verify some trip page elements
      const tripTitle = await page.locator('h1');
      await expect(tripTitle).toBeVisible();
      
      // Ensure share box is visible
      const shareBox = await page.locator('.share-box');
      await expect(shareBox).toBeVisible();
      
    } catch (error) {
      console.error('New user test failed:', error.message);
      await page.screenshot({ path: 'new-user-test-failure.png' });
      throw error;
    }
  });
});

/**
 * Test for returning user authentication flow
 */
test.describe('Returning User Authentication', () => {
  // Set up a test user before tests
  const userName = 'Returning Test User';
  const userEmail = 'returning-user@example.com';
  
  test('should authenticate returning user and redirect to trip page', async ({ page }) => {
    try {
      // Create the test user first (in the same context)
      console.log('Creating test user first...');
      
      // Ensure we start fresh
      await page.goto('/');
      await page.waitForTimeout(1000);
      
      await createTestUser(page, userName, userEmail);
      
      // Navigate back to homepage and clear any potential cookies/session
      await page.goto('/');
      await page.waitForTimeout(2000);
      
      console.log('Now testing returning user flow...');
      // Create trip with the same user info to trigger auth flow
      const shareLink = await createTrip(
        page, 
        'Rome', 
        userName, 
        userEmail, 
        { expectNewUser: false }
      );
      
      // At this point, we should have:
      // 1. Created a test user
      // 2. Created a trip as the returning user
      // 3. Gone through the auth flow
      // 4. Been redirected to the trip page
      
      // Verify we're on the trip page by examining content
      const tripTitle = await page.locator('h1').textContent();
      console.log(`Trip page title: ${tripTitle}`);
      expect(tripTitle).toContain('Rome');
      
      // Verify share link exists and has the expected format
      console.log(`Final share link: ${shareLink}`);
      expect(shareLink).toBeTruthy();
      expect(shareLink).toContain('/add');
      
      // Verify URL contains /trip/
      const finalUrl = page.url();
      console.log(`Final URL: ${finalUrl}`);
      expect(finalUrl).toContain('/trip/');
      
      // Ensure share box is visible
      const shareBox = await page.locator('.share-box');
      await expect(shareBox).toBeVisible();
      
    } catch (error) {
      console.error('Returning user test failed:', error.message);
      console.log(`Current URL at failure: ${page.url()}`);
      await page.screenshot({ path: 'returning-user-test-failure.png' });
      throw error;
    }
  });
});

/**
 * Test for recommendation submission process
 */
test.describe('Recommendation Submission', () => {
  // Share link that will be set in the setup
  let shareLink;
  
  // Setup - create a trip before the test
  test.beforeEach(async ({ page }) => {
    try {
      // Create a trip with a unique email
      const uniqueEmail = generateUniqueEmail();
      shareLink = await createTrip(page, 'Tokyo', 'Test Traveler', uniqueEmail);
      
      // Verify we got a share link
      expect(shareLink).toBeTruthy();
      
    } catch (error) {
      console.error('Setup failed:', error.message);
      await page.screenshot({ path: 'submission-setup-failure.png' });
      throw error;
    }
  });
  
  test('should process and submit recommendations', async ({ page }) => {
    try {
      // Define test recommendations
      const recommendations = 'You should visit Tokyo Tower and try sushi at Tsukiji Market. Also check out Shinjuku Gyoen for cherry blossoms in spring.';
      
      // Navigate to the share link
      await page.goto(shareLink);
      
      // Submit recommendations
      await submitRecommendations(page, shareLink, recommendations, 'Test Recommender');
      
      // Verify we're on the thank you page
      expect(page.url()).toContain('/thank-you');
      
      // Check for thank you page elements
      const pageTitle = await page.locator('h1').first();
      await expect(pageTitle).toBeVisible();
      const titleText = await pageTitle.textContent();
      expect(titleText.toLowerCase()).toContain('thank you');
      
      // If we can see recommendation cards, verify them
      if (await page.locator('.card').count() > 0) {
        // Look for any recommendation that was submitted
        const recommendationCards = await page.locator('.card').count();
        expect(recommendationCards).toBeGreaterThan(0);
      }
      
    } catch (error) {
      console.error('Recommendation submission test failed:', error.message);
      await page.screenshot({ path: 'submission-test-failure.png' });
      throw error;
    }
  });
}); 