# Destination Model and Autosuggest Implementation Plan

## Phase 1: Create Destination Model

- [x] **Step 1.1: Create basic Destination model**
  - Add Destination model to `app/database/models.py`
  - Include core fields (id, name, display_name, country, etc.)
  - Add relationship to Trip model (but don't modify Trip yet)
  - Add get_or_create method similar to Activity model

- [x] **Step 1.2: Create migration for Destination table**
  - Create migration file to add the Destination table
  - Test that migration can be applied and rolled back
  - Verify Destination table is created correctly

- [x] **Step 1.3: Add destination_id to Trip model**
  - Update Trip model to include destination_id foreign key (nullable)
  - Create migration file for this change
  - Keep existing destination fields for now
  - Test that existing trips still display properly

## Phase 2: Backend API for Destination Search

- [x] **Step 2.1: Create separate database search endpoint**
  - Implement `/api/destinations/database/` endpoint
  - Add route to search Destination model
  - Return formatted JSON response
  - Create test directory structure at `tests/unit/destinations/`
  - Add unit test for API response format
  - Add E2E test in `e2e_tests/tests/api/test_destinations_api.spec.js` to verify endpoint functionality
  - Add documentation

- [x] **Step 2.2: Create Google Places API endpoint**
  - Implement `/api/destinations/google-places/` endpoint
  - Create helper service to search Google Places API
  - Normalize results to match our Destination model format
  - Add unit tests for Google Places response normalization
  - Add E2E test with request interception to test integration without calling external API
  - Set up environment variable to toggle between real and mock API in tests
  - Run all tests to ensure they pass

- [x] **Step 2.3: Create OpenStreetMap API endpoint** (Future enhancement)
  - Implement `/api/destinations/openstreetmap/` endpoint for additional data source
  - Create helper function to search OpenStreetMap Nominatim
  - Normalize results to match our format
  - Add unit tests for OpenStreetMap response normalization
  - Extend E2E tests to cover the OpenStreetMap integration
  - Run all tests to ensure they pass

## Phase 3: Frontend Client-Side Integration

- [ ] **Step 3.1: Implement client-side API integration**
  - Create destination-search.js client library
  - Implement parallel requests to multiple data sources
  - Add result caching mechanism
  - Implement deduplication and sorting of combined results
  - Add error handling and fallback options
  - Test with slow network conditions
  
- [ ] **Step 3.2: Add autocomplete UI component**
  - Create destination-autocomplete.js component
  - Implement debounced input handling
  - Add results rendering logic
  - Style with destination-autocomplete.css
  - Implement keyboard and mouse navigation

- [ ] **Step 3.3: Create demonstration page**
  - Implement destination-search-demo.html
  - Show how client-side integration works
  - Add documentation and examples
  - Include API endpoint testing interface

## Phase 4: Destination Storage and Integration

- [ ] **Step 4.1: Update Trip creation to use Destinations**
  - Modify trip creation logic to find or create Destination
  - Store destination_id in Trip model
  - Keep updating legacy fields for backward compatibility
  - Test that new trips are created correctly

- [ ] **Step 4.2: Create data migration for existing trips**
  - Create migration to populate Destination table from existing trips
  - Link existing trips to new Destination records
  - Test that all trips have a destination

- [ ] **Step 4.3: Update Trip display to use Destination model**
  - Modify trip display templates to use new Destination relationship
  - Ensure backward compatibility for trips without destination_id
  - Test that all trips display correctly

## Phase 5: Cleanup and Optimization

- [ ] **Step 5.1: Add frontend fuzzy matching**
  - Implement client-side fuzzy matching for better UX
  - Test with partial and misspelled inputs

- [ ] **Step 5.2: Optimize API performance**
  - Add appropriate caching headers
  - Implement request batching for multiple searches
  - Test with slow network conditions

- [ ] **Step 5.3: Add permanent storage of external destinations**
  - Save destinations from external APIs to database
  - Test that repeated searches use database records

- [ ] **Step 5.4: Prepare for destination field deprecation**
  - Create migration to populate any missing destination_id values
  - Verify all trips have valid destination relationships
  - No field removal yet, just preparation
  - Run full e2e test suite

## Phase 6: Final Integration and Testing

- [ ] **Step 6.1: Comprehensive testing**
  - Write specific tests for Destination model
  - Test autosuggest feature thoroughly
  - Verify all existing functionality still works

- [ ] **Step 6.2: Documentation update**
  - Update documentation for new features
  - Add code comments as needed
  - Document API endpoints

- [ ] **Step 6.3: Final code cleanup**
  - Remove any temporary code
  - Finalize naming conventions
  - Ensure code follows project standards 