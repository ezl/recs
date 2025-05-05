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
  
  test('google places search endpoint validates query parameter', async ({ request }) => {
    // Test with no query parameter
    const emptyResponse = await request.get('/api/destinations/google-places/');
    expect(emptyResponse.status()).toBe(400);
    const emptyData = await emptyResponse.json();
    expect(emptyData.status).toBe('error');
    expect(emptyData.message).toBe('Query must be at least 2 characters');
    expect(emptyData.results).toEqual([]);
    
    // Test with short query parameter
    const shortResponse = await request.get('/api/destinations/google-places/?query=a');
    expect(shortResponse.status()).toBe(400);
    const shortData = await shortResponse.json();
    expect(shortData.status).toBe('error');
    expect(shortData.message).toBe('Query must be at least 2 characters');
    expect(shortData.results).toEqual([]);
  });
  
  test('google places search endpoint works in mock mode', async ({ request }) => {
    // Test with mock mode enabled to avoid actual API calls
    const response = await request.get('/api/destinations/google-places/?query=Paris&mock=true');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(Array.isArray(data.results)).toBe(true);
    expect(data.results.length).toBe(1);
    
    // Check the structure of the mock result
    const mockResult = data.results[0];
    expect(mockResult).toHaveProperty('name', 'Mock Paris City');
    expect(mockResult).toHaveProperty('display_name', 'Mock Paris City, Mock Country');
    expect(mockResult).toHaveProperty('country', 'Mock Country');
    expect(mockResult).toHaveProperty('type', 'city');
    expect(mockResult).toHaveProperty('latitude', 12.345);
    expect(mockResult).toHaveProperty('longitude', 67.890);
    expect(mockResult).toHaveProperty('google_place_id', 'mock_place_id_123');
    expect(mockResult).toHaveProperty('source', 'google_places');
  });
  
  test('google places search endpoint returns results with correct structure', async ({ request }) => {
    // Skip if environment variable for mock only is set
    const skipRealApi = process.env.USE_MOCK_API_ONLY === 'true';
    test.skip(skipRealApi, 'Skipping real API call as USE_MOCK_API_ONLY is set to true');
    
    if (!skipRealApi) {
      // Use a common city name that should return results in any environment
      const response = await request.get('/api/destinations/google-places/?query=London');
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      expect(data.status).toBe('success');
      expect(Array.isArray(data.results)).toBe(true);
      
      // Only check structure if we have results (might not have in CI without API key)
      if (data.results.length > 0) {
        const firstResult = data.results[0];
        expect(firstResult).toHaveProperty('name');
        expect(firstResult).toHaveProperty('display_name');
        expect(firstResult).toHaveProperty('country');
        expect(firstResult).toHaveProperty('type');
        expect(firstResult).toHaveProperty('source', 'google_places');
        expect(firstResult).toHaveProperty('google_place_id');
      }
    }
  });
  
  test('openstreetmap search endpoint validates query parameter', async ({ request }) => {
    // Test with no query parameter
    const emptyResponse = await request.get('/api/destinations/openstreetmap/');
    expect(emptyResponse.status()).toBe(400);
    const emptyData = await emptyResponse.json();
    expect(emptyData.status).toBe('error');
    expect(emptyData.message).toBe('Query must be at least 2 characters');
    expect(emptyData.results).toEqual([]);
    
    // Test with short query parameter
    const shortResponse = await request.get('/api/destinations/openstreetmap/?query=a');
    expect(shortResponse.status()).toBe(400);
    const shortData = await shortResponse.json();
    expect(shortData.status).toBe('error');
    expect(shortData.message).toBe('Query must be at least 2 characters');
    expect(shortData.results).toEqual([]);
  });
  
  test('openstreetmap search endpoint works in mock mode', async ({ request }) => {
    // Test with mock mode enabled to avoid actual API calls
    const response = await request.get('/api/destinations/openstreetmap/?query=Rome&mock=true');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(Array.isArray(data.results)).toBe(true);
    expect(data.results.length).toBe(1);
    
    // Check the structure of the mock result
    const mockResult = data.results[0];
    expect(mockResult).toHaveProperty('name', 'Mock OSM Rome');
    expect(mockResult).toHaveProperty('display_name', 'Mock OSM Rome, Mock OSM Country');
    expect(mockResult).toHaveProperty('country', 'Mock OSM Country');
    expect(mockResult).toHaveProperty('type', 'city');
    expect(mockResult).toHaveProperty('latitude', 34.567);
    expect(mockResult).toHaveProperty('longitude', 89.012);
    expect(mockResult).toHaveProperty('osm_id', '12345678');
    expect(mockResult).toHaveProperty('source', 'openstreetmap');
  });
  
  test('openstreetmap search endpoint returns results with correct structure', async ({ request }) => {
    // Skip if environment variable for mock only is set
    const skipRealApi = process.env.USE_MOCK_API_ONLY === 'true';
    test.skip(skipRealApi, 'Skipping real API call as USE_MOCK_API_ONLY is set to true');
    
    if (!skipRealApi) {
      // Use a common city name that should return results in any environment
      const response = await request.get('/api/destinations/openstreetmap/?query=Barcelona');
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      expect(data.status).toBe('success');
      expect(Array.isArray(data.results)).toBe(true);
      
      // Only check structure if we have results
      if (data.results.length > 0) {
        const firstResult = data.results[0];
        expect(firstResult).toHaveProperty('name');
        expect(firstResult).toHaveProperty('display_name');
        expect(firstResult).toHaveProperty('country');
        expect(firstResult).toHaveProperty('type');
        expect(firstResult).toHaveProperty('source', 'openstreetmap');
        expect(firstResult).toHaveProperty('osm_id');
      }
    }
  });
}); 