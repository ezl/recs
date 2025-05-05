import pytest
from flask import url_for
from app.database.models import Destination
from unittest.mock import patch

def test_database_search_endpoint_with_no_query(client):
    """Test database search endpoint validation when no query is provided"""
    response = client.get('/api/destinations/database/')
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Query must be at least 2 characters'
    assert data['results'] == []

def test_database_search_endpoint_with_short_query(client):
    """Test database search endpoint validation when query is too short"""
    response = client.get('/api/destinations/database/?query=a')
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Query must be at least 2 characters'
    assert data['results'] == []

def test_database_search_endpoint_with_no_results(client, app):
    """Test database search endpoint when no results match the query"""
    with app.app_context():
        # Ensure we have a clean database state for this test
        # Make a query that shouldn't match anything
        response = client.get('/api/destinations/database/?query=xyznonexistentplace')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['results']) == 0

def test_database_search_endpoint_with_results(client, app, db):
    """Test database search endpoint returns correct results"""
    with app.app_context():
        # Create test destinations
        destinations = [
            Destination(name='Paris', display_name='Paris, France', country='France', type='city'),
            Destination(name='London', display_name='London, UK', country='United Kingdom', type='city'),
            Destination(name='New York', display_name='New York, USA', country='United States', type='city')
        ]
        
        for dest in destinations:
            db.session.add(dest)
        db.session.commit()
        
        # Test searching for Paris
        response = client.get('/api/destinations/database/?query=Paris')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['results']) == 1
        assert data['results'][0]['name'] == 'Paris'
        assert data['results'][0]['country'] == 'France'
        assert data['results'][0]['source'] == 'database'
        
        # Test searching for partial name (case insensitive)
        response = client.get('/api/destinations/database/?query=lon')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['results']) == 1
        assert data['results'][0]['name'] == 'London'
        
        # Test searching by country
        response = client.get('/api/destinations/database/?query=United')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['results']) == 2  # Should find both UK and US
        
        # Clean up the test data
        for dest in destinations:
            db.session.delete(dest)
        db.session.commit()

def test_google_places_search_endpoint_with_no_query(client):
    """Test Google Places search endpoint validation when no query is provided"""
    response = client.get('/api/destinations/google-places/')
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Query must be at least 2 characters'
    assert data['results'] == []

def test_google_places_search_endpoint_with_short_query(client):
    """Test Google Places search endpoint validation when query is too short"""
    response = client.get('/api/destinations/google-places/?query=a')
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Query must be at least 2 characters'
    assert data['results'] == []

def test_google_places_search_endpoint_mock_mode(client):
    """Test Google Places search endpoint in mock mode"""
    response = client.get('/api/destinations/google-places/?query=Paris&mock=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 1
    
    # Verify mock data format
    mock_result = data['results'][0]
    assert mock_result['name'] == 'Mock Paris City'
    assert mock_result['country'] == 'Mock Country'
    assert mock_result['source'] == 'google_places'
    assert mock_result['google_place_id'] == 'mock_place_id_123'
    assert mock_result['latitude'] == 12.345
    assert mock_result['longitude'] == 67.890

@patch('app.services.google_places_service.GooglePlacesService.search_destinations')
def test_google_places_search_endpoint_with_service_mock(mock_search, client):
    """Test Google Places search endpoint with mocked service response"""
    # Set up the mock
    mock_search.return_value = [
        {
            'id': None,
            'name': 'Berlin',
            'display_name': 'Berlin, Germany',
            'country': 'Germany',
            'type': 'city',
            'latitude': 52.520008,
            'longitude': 13.404954,
            'google_place_id': 'ChIJAVkDPzdOqEcRcDteW0YgIQQ',
            'source': 'google_places'
        }
    ]
    
    response = client.get('/api/destinations/google-places/?query=Berlin')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 1
    
    # Verify we got the mock data
    result = data['results'][0]
    assert result['name'] == 'Berlin'
    assert result['country'] == 'Germany'
    assert result['source'] == 'google_places'
    
    # Verify the mock was called with correct arguments
    mock_search.assert_called_once_with('Berlin')

def test_openstreetmap_search_endpoint_with_no_query(client):
    """Test OpenStreetMap search endpoint validation when no query is provided"""
    response = client.get('/api/destinations/openstreetmap/')
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Query must be at least 2 characters'
    assert data['results'] == []

def test_openstreetmap_search_endpoint_with_short_query(client):
    """Test OpenStreetMap search endpoint validation when query is too short"""
    response = client.get('/api/destinations/openstreetmap/?query=a')
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == 'Query must be at least 2 characters'
    assert data['results'] == []

def test_openstreetmap_search_endpoint_mock_mode(client):
    """Test OpenStreetMap search endpoint in mock mode"""
    response = client.get('/api/destinations/openstreetmap/?query=Rome&mock=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 1
    
    # Verify mock data format
    mock_result = data['results'][0]
    assert mock_result['name'] == 'Mock OSM Rome'
    assert mock_result['country'] == 'Mock OSM Country'
    assert mock_result['source'] == 'openstreetmap'
    assert mock_result['osm_id'] == '12345678'
    assert mock_result['latitude'] == 34.567
    assert mock_result['longitude'] == 89.012

@patch('app.services.openstreetmap_service.OpenStreetMapService.search_destinations')
def test_openstreetmap_search_endpoint_with_service_mock(mock_search, client):
    """Test OpenStreetMap search endpoint with mocked service response"""
    # Set up the mock
    mock_search.return_value = [
        {
            'id': None,
            'name': 'Tokyo',
            'display_name': 'Tokyo, Japan',
            'country': 'Japan',
            'type': 'city',
            'latitude': 35.6762,
            'longitude': 139.6503,
            'osm_id': '123456789',
            'source': 'openstreetmap'
        }
    ]
    
    response = client.get('/api/destinations/openstreetmap/?query=Tokyo')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 1
    
    # Verify we got the mock data
    result = data['results'][0]
    assert result['name'] == 'Tokyo'
    assert result['country'] == 'Japan'
    assert result['source'] == 'openstreetmap'
    
    # Verify the mock was called with correct arguments
    mock_search.assert_called_once_with('Tokyo') 