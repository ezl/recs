// @ts-check
const { test, expect } = require('@playwright/test');
const { createTrip, submitRecommendations } = require('../utils/test-setup');

/**
 * Tests the grouping functionality when multiple people submit the same recommendation:
 * 1. Creates a trip to Chicago
 * 2. Has 3 different users create similar recommendations
 * 3. Verifies that recommendations are properly grouped
 */
test.describe('Recommendation Grouping Functionality', () => {
  let shareLink;

  // Setup - create a trip before the test
  test.beforeEach(async ({ page }) => {
    try {
      // Create a new trip to Chicago
      shareLink = await createTrip(page, 'Chicago', 'Test Organizer', 'organizer@example.com');
      console.log(`Created trip with share link: ${shareLink}`);
    } catch (error) {
      console.error('Setup failed:', error.message);
      await page.screenshot({ path: 'grouping-setup-failure.png' });
      throw error;
    }
  });

  test('should group identical recommendations from multiple users', async ({ browser, page }) => {
    // Set timeout for this specific test
    test.setTimeout(60000);
    
    try {
      // User 1: Andrew's recommendations
      const andrewRecommendations = [
        "Wrigley Field - a great place to watch a cubs game",
        "Pequod's Pizza - the best pizza in chicago",
        "Chicago Board of Trade - an iconic building in downtown chicago"
      ].join('\n\n');
      
      // Create a fresh context for Andrew
      const andrewContext = await browser.newContext();
      const andrewPage = await andrewContext.newPage();
      await submitRecommendations(andrewPage, shareLink, andrewRecommendations, 'Andrew');
      console.log('Submitted recommendations from Andrew');
      await andrewContext.close();
      // User 2: Betty's recommendations
      const bettyRecommendations = [
        "Pequods - they're known for their pizza but i love their calamari!",
        "Wrigley Field - an amazing experience on a Friday afternoon if you can go to a home game"
      ].join('\n\n');
      
      // Create a fresh context for Betty
      const bettyContext = await browser.newContext();
      const bettyPage = await bettyContext.newPage();
      await submitRecommendations(bettyPage, shareLink, bettyRecommendations, 'Betty');
      console.log('Submitted recommendations from Betty');
      await bettyContext.close();
      // User 3: Charlie's recommendations
      const charlieRecommendations = "Wrigley field - Go cubs!";
      
      // Create a fresh context for Charlie
      const charlieContext = await browser.newContext();
      const charliePage = await charlieContext.newPage();
      await submitRecommendations(charliePage, shareLink, charlieRecommendations, 'Charlie');
      console.log('Submitted recommendations from Charlie');
      await charlieContext.close();
      // Navigate to the trip page to see all recommendations
      // Extract the trip URL from the share link (remove the /add part)
      const tripUrl = shareLink.replace('/add', '');
      await page.goto(tripUrl);
      console.log(`Navigated to trip page: ${tripUrl}`);
      
      // Wait for the recommendation cards to load
      await page.waitForSelector('.card', { timeout: 10000 });
      
      // Take a screenshot of the grouped recommendations
      await page.screenshot({ path: 'grouping-test-result.png' });
      
      // Verify there are exactly 3 recommendation cards
      const recommendationCards = await page.locator('.card').count();
      console.log(`Found ${recommendationCards} recommendation cards`);
      expect(recommendationCards).toBe(3);
      
      // Find the Wrigley Field card (case insensitive search)
      const wrigleyFieldCard = page.locator('.card', { 
        hasText: /wrigley field/i 
      });
      
      // Verify the Wrigley Field card exists
      await expect(wrigleyFieldCard).toBeVisible();
      
      // Verify the Wrigley Field card has notes from all three users
      const wrigleyCardContent = await wrigleyFieldCard.textContent();
      console.log(`Wrigley Field card content: ${wrigleyCardContent}`);
      
      // Check if all three names are present in the card
      expect(wrigleyCardContent).toContain('Andrew');
      expect(wrigleyCardContent).toContain('Betty');
      expect(wrigleyCardContent).toContain('Charlie');
      
      console.log('Test passed: Wrigley Field card contains all three users');
    } catch (error) {
      console.error('Grouping test failed:', error.message);
      await page.locator('#card-view').screenshot({ path: 'grouping-test-failure.png' });
      throw error;
    }
  });
}); 