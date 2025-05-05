import pytest
from flask import url_for
from app.database.models import Destination

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