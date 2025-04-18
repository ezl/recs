// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Trip Creation and Sharing Flow', () => {
  test('should create a new trip and generate a shareable link', async ({ page }) => {
    // Go to the homepage
    await page.goto('/');
    
    // Fill out the trip creation form
    await page.fill('#name', 'Test User');
    await page.fill('#destination', 'Paris');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for navigation to the trip detail page
    await page.waitForURL(/\/trip\/*/);
    
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
  
  test('should create trip with a unique slug', async ({ page }) => {
    // Create first trip
    await page.goto('/');
    await page.fill('#name', 'Duplicate User');
    await page.fill('#destination', 'Rome');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/trip\/*/);
    
    // Get the URL of the first trip
    const firstTripUrl = page.url();
    
    // Create second trip with same details
    await page.goto('/');
    await page.fill('#name', 'Duplicate User');
    await page.fill('#destination', 'Rome');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/trip\/*/);
    
    // Get the URL of the second trip
    const secondTripUrl = page.url();
    
    // Verify the URLs are different
    expect(firstTripUrl).not.toEqual(secondTripUrl);
    expect(secondTripUrl).toContain('/trip/rome');
  });
}); 