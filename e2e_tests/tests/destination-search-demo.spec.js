const { test, expect } = require('@playwright/test');

/**
 * End-to-end tests for the destination search demo page and documentation
 */
test.describe('Destination Search Demo', () => {
  
  test('demo page loads with all sections visible', async ({ page }) => {
    // Add debug logging to track test progress
    console.log('Starting test: demo page loads with all sections visible');
    
    // Navigate to the demo page with explicit wait for the page to load
    console.log('Navigating to /destination-search-demo');
    await page.goto('/destination-search-demo', { waitUntil: 'networkidle' });
    
    // Debug: Log current URL and page content
    console.log('Current URL:', page.url());
    const pageContent = await page.content();
    console.log('Page content length:', pageContent.length);
    console.log('Page title:', await page.title());
    
    // Check if we got redirected or received an error page
    if (page.url().includes('error') || pageContent.includes('404 Not Found') || pageContent.includes('Error')) {
      console.log('Error detected in page - may have been redirected to error page');
    }
    
    // Check the page title
    await expect(page).toHaveTitle('Destination Search Demo', {timeout: 10000});
    
    // Check that all major sections are visible
    await expect(page.locator('h1:has-text("Destination Search API Documentation & Demo")')).toBeVisible();
    
    // Verify Live Demo section
    await expect(page.locator('h2:has-text("Live Demo")')).toBeVisible();
    await expect(page.locator('#demoQuery')).toBeVisible();
    await expect(page.locator('#demoSearchBtn')).toBeVisible();
    
    // Verify API Documentation section
    await expect(page.locator('h2:has-text("API Documentation")')).toBeVisible();
    await expect(page.locator('h3:has-text("Getting Started")')).toBeVisible();
    await expect(page.locator('h3:has-text("API Reference")')).toBeVisible();
    
    // Verify API Explorer section
    await expect(page.locator('h2:has-text("API Explorer")')).toBeVisible();
    await expect(page.locator('#explorerQuery')).toBeVisible();
    await expect(page.locator('#explorerEndpoint')).toBeVisible();
    await expect(page.locator('#explorerSearchBtn')).toBeVisible();
    
    // Verify Implementation Examples section
    await expect(page.locator('h2:has-text("Implementation Examples")')).toBeVisible();
    await expect(page.locator('h3:has-text("Search with Autocomplete")')).toBeVisible();
  });
  
  test('API Explorer tabs switch content correctly', async ({ page }) => {
    // Navigate to the demo page
    await page.goto('/destination-search-demo', { waitUntil: 'networkidle' });
    
    // Initial state should show the database content
    await expect(page.locator('#database-content')).toHaveClass(/active/);
    await expect(page.locator('#google-content')).not.toHaveClass(/active/);
    await expect(page.locator('#openstreetmap-content')).not.toHaveClass(/active/);
    
    // Click the Google Places tab
    await page.locator('.code-tab[data-target="google"]').click();
    
    // Now Google content should be visible and others hidden
    await expect(page.locator('#database-content')).not.toHaveClass(/active/);
    await expect(page.locator('#google-content')).toHaveClass(/active/);
    await expect(page.locator('#openstreetmap-content')).not.toHaveClass(/active/);
    
    // Click the OpenStreetMap tab
    await page.locator('.code-tab[data-target="openstreetmap"]').click();
    
    // Now OpenStreetMap content should be visible and others hidden
    await expect(page.locator('#database-content')).not.toHaveClass(/active/);
    await expect(page.locator('#google-content')).not.toHaveClass(/active/);
    await expect(page.locator('#openstreetmap-content')).toHaveClass(/active/);
  });
  
  test('live demo search works with mock data', async ({ page }) => {
    // Setup route interception for database endpoint
    await page.route('/api/destinations/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          results: [
            {
              id: 1,
              name: 'Demo City',
              display_name: 'Demo City, Demo Country',
              country: 'Demo Country',
              type: 'city',
              latitude: 12.345,
              longitude: 67.890,
              source: 'database'
            }
          ]
        })
      });
    });
    
    // Navigate to the demo page
    await page.goto('/destination-search-demo', { waitUntil: 'networkidle' });
    
    // Enter search query
    await page.locator('#demoQuery').fill('Demo');
    
    // Click search button
    await page.locator('#demoSearchBtn').click();
    
    // Wait for results to appear
    await page.waitForFunction(() => {
      return document.querySelector('#demoResults').textContent.includes('Demo City');
    }, { timeout: 5000 });
    
    // Verify the result content
    const resultContent = await page.locator('#demoResults').textContent();
    expect(resultContent).toContain('Demo City');
    expect(resultContent).toContain('Demo Country');
    
    // Verify stats are displayed
    const statsContent = await page.locator('#resultStats').textContent();
    expect(statsContent).toContain('Found 1 results');
  });
  
  test('API Explorer executes search correctly', async ({ page }) => {
    // Setup route interception for all API endpoints
    await page.route('/api/destinations/**', async route => {
      const url = route.request().url();
      
      // Create a response that includes the endpoint in the result for verification
      let endpoint = 'unknown';
      if (url.includes('database')) endpoint = 'database';
      else if (url.includes('google-places')) endpoint = 'google-places';
      else if (url.includes('openstreetmap')) endpoint = 'openstreetmap';
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          endpoint: endpoint,
          results: [
            {
              id: endpoint === 'database' ? 1 : null,
              name: 'Explorer Test',
              display_name: 'Explorer Test, Test Country',
              country: 'Test Country',
              type: 'city',
              latitude: 12.345,
              longitude: 67.890,
              source: endpoint === 'database' ? 'database' : 
                     endpoint === 'google-places' ? 'google_places' : 'openstreetmap'
            }
          ]
        })
      });
    });
    
    // Navigate to the demo page
    await page.goto('/destination-search-demo', { waitUntil: 'networkidle' });
    
    // Enter search query
    await page.locator('#explorerQuery').fill('test');
    
    // Select database endpoint
    await page.locator('#explorerEndpoint').selectOption('database');
    
    // Click search button
    await page.locator('#explorerSearchBtn').click();
    
    // Wait for results to appear
    await page.waitForFunction(() => {
      return document.querySelector('#explorerResults').textContent.includes('Explorer Test');
    }, { timeout: 5000 });
    
    // Verify the result content includes database endpoint information
    const resultContent = await page.locator('#explorerResults').textContent();
    expect(resultContent).toContain('database');
    
    // Switch to Google Places endpoint
    await page.locator('#explorerEndpoint').selectOption('google');
    
    // Click search button again
    await page.locator('#explorerSearchBtn').click();
    
    // Wait for new results
    await page.waitForFunction(() => {
      return document.querySelector('#explorerResults').textContent.includes('google-places');
    }, { timeout: 5000 });
    
    // Verify the result now includes Google Places endpoint information
    const newResultContent = await page.locator('#explorerResults').textContent();
    expect(newResultContent).toContain('google-places');
  });
}); 