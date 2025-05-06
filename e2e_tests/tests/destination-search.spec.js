const { test, expect } = require('@playwright/test');

/**
 * End-to-end tests for the destination search client library
 */
test.describe('Destination Search Library', () => {
  
  test('test page loads and displays correctly', async ({ page }) => {
    // Navigate to the test page with explicit wait for the page to load
    await page.goto('/destination-search-test', { waitUntil: 'networkidle' });
    
    // Check the page title
    await expect(page).toHaveTitle('Destination Search Test');
    
    // Check that all UI elements are visible
    await expect(page.locator('#searchQuery')).toBeVisible();
    await expect(page.locator('#searchSource')).toBeVisible();
    await expect(page.locator('#searchButton')).toBeVisible();
    await expect(page.locator('#clearCacheButton')).toBeVisible();
    
    // Check advanced section
    await expect(page.locator('#advancedQuery')).toBeVisible();
    await expect(page.locator('#advancedLimit')).toBeVisible();
    await expect(page.locator('#advancedTimeout')).toBeVisible();
    await expect(page.locator('#advancedButton')).toBeVisible();
  });
  
  test('single source search returns results', async ({ page }) => {
    console.log('Starting single source search test');
    
    // Setup route interception before navigation - EXACTLY match the endpoint used in client code
    await page.route('/api/destinations/database/?**', async route => {
      console.log('Intercepting route:', route.request().url());
      
      // Extract query from the URL to include in response
      const url = route.request().url();
      const query = new URL(url).searchParams.get('query') || 'Paris';
      console.log('Search query parameter:', query);
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: [
            {
              id: 1,
              name: query,
              display_name: `${query}, France`,
              country: 'France',
              type: 'city',
              latitude: 48.8566,
              longitude: 2.3522,
              source: 'database'
            }
          ]
        })
      });
      console.log('Route fulfilled with mock data');
    });
    
    // Navigate to the test page
    console.log('Navigating to test page');
    await page.goto('/destination-search-test', { waitUntil: 'networkidle' });
    console.log('Page loaded');
    
    // Enter search query
    await page.locator('#searchQuery').fill('Paris');
    console.log('Filled search query: Paris');
    
    // Select database source only
    await page.locator('#searchSource').selectOption('database');
    console.log('Selected database source');
    
    // Click search button
    console.log('Clicking search button');
    await page.locator('#searchButton').click();
    console.log('Search button clicked');
    
    // Wait for results to appear and stabilize
    console.log('Waiting for results to appear');
    await page.waitForFunction(() => {
      const content = document.querySelector('#searchResults').textContent;
      return content && content !== 'Searching...' && content !== 'Results will appear here...';
    }, { timeout: 10000 });
    console.log('Results appeared');
    
    // Get results content
    const resultText = await page.locator('#searchResults').textContent();
    console.log('Results text:', resultText);
    
    // Verify the results contain the expected data
    console.log('DEBUGGING - Result text before assertions:', resultText);
    try {
      expect(resultText).toContain('Paris');
      expect(resultText).toContain('France');
      expect(resultText).toContain('database');
      console.log('Assertions passed');
    } catch (error) {
      console.error('Test failed with content:', resultText);
      console.error('Error message:', error.message);
      throw error;
    }
  });
  
  test('multiple source search can combine results', async ({ page }) => {
    // Setup route interception for all endpoints - EXACTLY match the endpoints used in client code
    await page.route('/api/destinations/database/?**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: [
            {
              id: 1,
              name: 'Rome',
              display_name: 'Rome, Italy',
              country: 'Italy',
              type: 'city',
              latitude: 41.9028,
              longitude: 12.4964,
              source: 'database'
            }
          ]
        })
      });
    });
    
    await page.route('/api/destinations/google-places/?**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: [
            {
              id: null,
              name: 'Rome',
              display_name: 'Rome, Italy',
              country: 'Italy',
              type: 'city',
              latitude: 41.9028,
              longitude: 12.4964,
              google_place_id: 'ChIJu46S-ZZhLxMROG5lkwZ3D7k',
              source: 'google_places'
            },
            {
              id: null,
              name: 'Roman Forum',
              display_name: 'Roman Forum, Rome, Italy',
              country: 'Italy',
              type: 'place',
              latitude: 41.8925,
              longitude: 12.4853,
              google_place_id: 'ChIJjRnzUddgLxMRG2vu-_1CcxY',
              source: 'google_places'
            }
          ]
        })
      });
    });
    
    await page.route('/api/destinations/openstreetmap/?**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: [
            {
              id: null,
              name: 'Rome',
              display_name: 'Rome, Italy',
              country: 'Italy',
              type: 'city',
              latitude: 41.9028,
              longitude: 12.4964,
              osm_id: '41485',
              source: 'openstreetmap'
            },
            {
              id: null,
              name: 'Rome',
              display_name: 'Rome, Georgia, USA',
              country: 'United States',
              type: 'city',
              latitude: 34.2574,
              longitude: -85.1646,
              osm_id: '107125',
              source: 'openstreetmap'
            }
          ]
        })
      });
    });
    
    // Navigate to the test page
    await page.goto('/destination-search-test', { waitUntil: 'networkidle' });
    
    // Enter search query and select all sources
    await page.locator('#searchQuery').fill('Rome');
    await page.locator('#searchSource').selectOption('all');
    
    // Click search button
    await page.locator('#searchButton').click();
    
    // Wait for results to appear and stabilize
    await page.waitForFunction(() => {
      const content = document.querySelector('#searchResults').textContent;
      return content && content !== 'Searching...' && content !== 'Results will appear here...';
    }, { timeout: 10000 });
    
    // Safely parse the JSON results
    const resultText = await page.locator('#searchResults').textContent();
    let results;
    try {
      results = JSON.parse(resultText);
    } catch (e) {
      throw new Error(`Failed to parse JSON results: ${resultText}`);
    }
    
    // Check that we have at least 3 results
    expect(results.length).toBeGreaterThanOrEqual(3);
    
    // Check that Rome, Italy from database is included
    const romeItaly = results.find(r => r.name === 'Rome' && r.country === 'Italy');
    expect(romeItaly).toBeTruthy();
    expect(romeItaly.source).toBe('database'); // Should prioritize database source
    
    // Check that other unique results are included
    const romeUSA = results.find(r => r.name === 'Rome' && r.country === 'United States');
    expect(romeUSA).toBeTruthy();
    
    const romanForum = results.find(r => r.name === 'Roman Forum');
    expect(romanForum).toBeTruthy();
    
    // The total count should be less than the sum of all source results due to deduplication
    expect(results.length).toBeLessThan(5); // 1 + 2 + 2 = 5 total from all sources
  });
  
  test('advanced options control number of results', async ({ page }) => {
    // Setup route interception - use a broader pattern to catch all endpoints
    await page.route('/api/destinations/**', async route => {
      // Create 12 mock results
      const mockResults = Array(12).fill(0).map((_, i) => ({
        id: i + 1,
        name: `City ${i + 1}`,
        display_name: `City ${i + 1}, Country ${i + 1}`,
        country: `Country ${i + 1}`,
        type: 'city',
        latitude: 40 + i,
        longitude: 10 + i,
        source: 'database'
      }));
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: mockResults
        })
      });
    });
    
    // Navigate to the test page
    await page.goto('/destination-search-test', { waitUntil: 'networkidle' });
    
    // Set advanced query
    await page.locator('#advancedQuery').fill('test');
    
    // Set limit to 5
    await page.locator('#advancedLimit').clear();
    await page.locator('#advancedLimit').fill('5');
    
    // Click search button
    await page.locator('#advancedButton').click();
    
    // Wait for results to appear and stabilize
    await page.waitForFunction(() => {
      const content = document.querySelector('#advancedResults').textContent;
      return content && content !== 'Searching with custom options...' && content !== 'Results will appear here...';
    }, { timeout: 10000 });
    
    // Safely parse the JSON results
    const resultText = await page.locator('#advancedResults').textContent();
    let results;
    try {
      results = JSON.parse(resultText);
    } catch (e) {
      throw new Error(`Failed to parse JSON results: ${resultText}`);
    }
    
    // Verify exactly 5 results are returned (due to limit=5)
    expect(results.length).toBe(5);
  });
  
  test('cache clears when button is clicked', async ({ page }) => {
    test.setTimeout(15000); // Increase timeout for this test
    let callCount = 0;
    
    // Setup route interception to track API calls - EXACTLY match the endpoint used in client code
    await page.route('/api/destinations/database/?**', async route => {
      callCount++;
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: [
            {
              id: 1,
              name: 'Test City',
              display_name: 'Test City, Test Country',
              country: 'Test Country',
              type: 'city',
              latitude: 0,
              longitude: 0,
              source: 'database'
            }
          ]
        })
      });
    });
    
    // Navigate to the test page
    await page.goto('/destination-search-test', { waitUntil: 'networkidle' });
    
    // First search should make an API call
    await page.locator('#searchQuery').fill('test');
    await page.locator('#searchSource').selectOption('database');
    await page.locator('#searchButton').click();
    
    // Wait for results to appear
    await page.waitForFunction(() => {
      const content = document.querySelector('#searchResults').textContent;
      return content && content !== 'Searching...' && content !== 'Results will appear here...';
    }, { timeout: 10000 });
    
    // Second identical search should use cache (no new API call)
    await page.locator('#searchButton').click();
    await page.waitForTimeout(1000); // Brief wait to ensure cache is used
    
    // At this point, only 1 API call should have been made
    expect(callCount).toBe(1);
    
    // Clear cache and handle alert dialog
    page.on('dialog', dialog => dialog.accept());
    await page.locator('#clearCacheButton').click();
    
    // After clearing cache, another search should make a new API call
    await page.locator('#searchButton').click();
    
    // Wait for results to appear after the new API call
    await page.waitForFunction(() => {
      const content = document.querySelector('#searchResults').textContent;
      return content && content !== 'Searching...' && content !== 'Results will appear here...';
    }, { timeout: 10000 });
    
    // Now we should have 2 API calls
    expect(callCount).toBe(2);
  });
}); 