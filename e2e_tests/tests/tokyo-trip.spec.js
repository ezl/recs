// @ts-check
const { test, expect } = require('@playwright/test');

test.setTimeout(20000);

test('should create Tokyo trip with multiple recommendations', async ({ page }) => {
  // Create the trip
  await page.goto('/');
  await page.fill('#destination', 'Tokyo');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/user-info');
  console.log('Navigated to user-info page');
  
  await page.fill('#name', 'Test User');
  await page.fill('#email', 'test@example.com');
  
  // Start waiting for navigation before clicking
  const navigationPromise = page.waitForURL('**/trip/**');
  await page.click('button[type="submit"]');
  // Now wait for the navigation to complete
  await navigationPromise;
  console.log('Final URL after wait:', page.url());
  
  // Get the share link
  const shareLink = await page.locator('.share-box input[type="text"]').inputValue();
  console.log('Share link:', shareLink);
  
  // Create recommendations as different users
  const recommendations = [
    {
      user: 'Alpha',
      place: 'Asakusa',
      category: 'Historic district',
      description: 'Explore the traditional charm of Asakusa, featuring ancient temples, street food vendors, and a glimpse of old-school Tokyo vibes.'
    },
    {
      user: 'Charlie',
      place: 'Asakusa',
      category: 'Historic area',
      description: 'Old-school Tokyo vibes, visit Sensoji Temple and grab some street snacks.'
    },
    {
      user: 'Alpha',
      place: 'TeamLab Planets',
      category: 'Interactive art exhibition',
      description: 'An immersive experience where visitors can walk through interactive art installations resembling a dream.'
    },
    {
      user: 'Charlie',
      place: 'TeamLab Planets',
      category: 'Art Museum',
      description: 'Wild immersive art experience, feels like another world.'
    },
    {
      user: 'Bravo',
      place: 'Ramen Street',
      category: 'Restaurant',
      description: 'Don\'t miss Ramen Street at Tokyo Station for a must-try culinary experience in Tokyo.'
    },
    {
      user: 'Charlie',
      place: 'Ramen Street (Tokyo Station)',
      category: 'Food',
      description: 'A whole underground row of famous ramen shops, easy and delicious.'
    },
    {
      user: 'Alpha',
      place: 'Shibuya Scramble Crossing',
      category: 'Famous landmark',
      description: 'Experience the iconic and bustling Shibuya Scramble Crossing, and explore the charming streets of Shibuya.'
    },
    {
      user: 'Alpha',
      place: 'Tsukiji Market',
      category: 'Market',
      description: 'Experience the lively atmosphere of Tsukiji Market, known for its fresh seafood and sushi breakfast offerings.'
    },
    {
      user: 'Bravo',
      place: 'Nakameguro',
      category: 'Neighborhood',
      description: 'Nakameguro offers a peaceful morning by the river with opportunities to enjoy coffee and a leisurely walk.'
    },
    {
      user: 'Charlie',
      place: 'Nakameguro',
      category: 'Neighborhood',
      description: 'Chill riverside neighborhood, great for coffee shops and boutique shopping.'
    }
  ];

  // Submit each recommendation
  for (const rec of recommendations) {
    // Navigate to the share link
    await page.goto(shareLink);
    console.log('Navigated to share link:', shareLink);
    
    // Wait for the form to be visible
    console.log('Waiting for form elements...');
    await page.waitForSelector('#text-recommendations', { state: 'visible' });
    console.log('Text area is visible');
    
    // Fill out the recommendation form
    console.log('Filling form for:', rec.place);
    const recommendation = `${rec.place} - ${rec.category}\n${rec.description}`;
    
    // Fill in the recommendation text area
    await page.waitForSelector('#text-recommendations', { state: 'visible' });
    await page.fill('#text-recommendations', recommendation);
    console.log('Filled recommendation text:', recommendation);
    
    // Wait for the submit button to be enabled
    await page.waitForSelector('#submit-button:not([disabled])', { timeout: 1000 });
    await expect(page.locator('#submit-button')).toBeEnabled();
    console.log('Submit button is enabled');
    
    // Click submit button
    await page.click('#submit-button');
    console.log('Clicked submit button');
    
    // Wait for recommendations to be processed
    await page.waitForURL('**/trip/**/process');
    console.log('On process page');

    // On the process page, fill in recommender name
    await page.waitForSelector('#recommender_name', { state: 'visible' });
    await page.fill('#recommender_name', 'Test User');
    console.log('Filled recommender name');

    // Submit the final form and wait for thank you page
    await Promise.all([
      page.waitForURL('**/trip/**/thank-you'),
      page.click('#submit-button')
    ]);
    console.log('Successfully submitted recommendation');
  }

  // Verify the recommendations on the trip page
  await page.goto(shareLink.replace('/add', ''));
  
  // Wait for recommendations to load
  await page.waitForSelector('.recommendation-group');
  
  // Verify the number of recommendation groups
  const groups = await page.locator('.recommendation-group').count();
  expect(groups).toBe(7); // 7 unique activities
  
  // Verify the content of each group
  for (const rec of recommendations) {
    const group = page.locator('.recommendation-group', { hasText: rec.place });
    await expect(group).toBeVisible();
    
    // Verify the recommendation text
    const recommendation = group.locator('.recommendation', { hasText: rec.description });
    await expect(recommendation).toBeVisible();
  }
}); 