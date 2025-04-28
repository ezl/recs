// @ts-check
const { test, expect } = require('@playwright/test');

test.setTimeout(20000);

test('should create Paris trip with Eiffel Tower recommendation', async ({ page }) => {
  // Create the trip
  await page.goto('/');
  await page.fill('#destination', 'Paris');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/user-info');
  await page.fill('#name', 'Test User');
  await page.fill('#email', 'test@example.com');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/trip/**');
  
  // Get the share link
  const shareLink = await page.locator('.share-box input[type="text"]').inputValue();
  
  // Navigate to the share link
  await page.goto(shareLink);
  
  // Fill out the recommendation form
  await page.fill('#name', 'Test User');
  await page.fill('#place', 'Eiffel Tower');
  await page.fill('#category', 'Landmark');
  await page.fill('#description', 'Iconic Parisian landmark offering stunning views of the city.');
  
  // Submit the form
  await page.click('button[type="submit"]');
  
  // Wait for the success message
  await page.waitForSelector('.success-message');
  
  // Verify the recommendation on the trip page
  await page.goto(shareLink.replace('/add', ''));
  
  // Wait for recommendations to load
  await page.waitForSelector('.recommendation-group');
  
  // Verify the recommendation group
  const group = page.locator('.recommendation-group', { hasText: 'Eiffel Tower' });
  await expect(group).toBeVisible();
  
  // Verify the recommendation text
  const recommendation = group.locator('.recommendation', { hasText: 'Iconic Parisian landmark' });
  await expect(recommendation).toBeVisible();
}); 