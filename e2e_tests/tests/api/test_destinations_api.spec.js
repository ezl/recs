const { test, expect } = require('@playwright/test');

/**
 * End-to-end tests for the destinations API endpoints
 */
test.describe('Destinations API', () => {
  test('database search endpoint validates query parameter', async ({ request }) => {
    // Test with no query parameter
    const emptyResponse = await request.get('/api/destinations/database/');
    expect(emptyResponse.status()).toBe(400);
    const emptyData = await emptyResponse.json();
    expect(emptyData.status).toBe('error');
    expect(emptyData.message).toBe('Query must be at least 2 characters');
    expect(emptyData.results).toEqual([]);
    
    // Test with short query parameter
    const shortResponse = await request.get('/api/destinations/database/?query=a');
    expect(shortResponse.status()).toBe(400);
    const shortData = await shortResponse.json();
    expect(shortData.status).toBe('error');
    expect(shortData.message).toBe('Query must be at least 2 characters');
    expect(shortData.results).toEqual([]);
  });
  
  test('database search endpoint returns results in expected format', async ({ request }) => {
    // Use a query that should have some results in any environment
    // This assumes there is at least one destination in the database with "New" in the name
    // such as "New York" or similar
    const response = await request.get('/api/destinations/database/?query=New');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(Array.isArray(data.results)).toBe(true);
    
    // Check the structure of the first result if there are results
    if (data.results.length > 0) {
      const firstResult = data.results[0];
      expect(firstResult).toHaveProperty('id');
      expect(firstResult).toHaveProperty('name');
      expect(firstResult).toHaveProperty('display_name');
      expect(firstResult).toHaveProperty('country');
      expect(firstResult).toHaveProperty('source', 'database');
    }
  });
  
  test('database search works with special characters', async ({ request }) => {
    // Test with special characters that should be properly handled
    const response = await request.get('/api/destinations/database/?query=São Paulo');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    // We don't assert on the presence of results as it depends on the database content
  });
}); 