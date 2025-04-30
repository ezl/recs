/**
 * Recommendation map component for the trip page
 * Handles map initialization, markers, and info windows
 */

// Map initialization function (called by Google Maps API after loading)
function initMap() {
  // This will be called when Google Maps API is loaded
  if (window.setupMap && typeof window.setupMap === 'function') {
    console.log('Setting up map...');
    window.setupMap();
  } else {
    console.warn('setupMap function not found when Google Maps API loaded');
  }
}

function initRecommendationMap() {
  // Map setup function - will be called when the Google Maps API is loaded
  window.mapMarkers = [];
  window.infoWindows = [];
  
  window.setupMap = function() {
    const recommendationsMap = document.getElementById('recommendations-map');
    if (!recommendationsMap) {
      return;
    }
    
    const cards = document.querySelectorAll('.recommendation-card');
    
    // Extract location data
    const locations = [];
    const missingLocations = [];
    
    cards.forEach(card => {
      const lat = parseFloat(card.dataset.lat);
      const lng = parseFloat(card.dataset.lng);
      const name = card.dataset.name;
      
      // Only add locations with valid coordinates
      if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
        locations.push({
          lat,
          lng,
          name,
          activityId: card.dataset.activityId,
          category: card.dataset.category,
          placeId: card.dataset.placeId,
          element: card
        });
      } else {
        // Track missing locations
        missingLocations.push(name);
      }
    });
    
    // Show missing coordinates message if needed
    const missingCoordinatesMessage = document.getElementById('missing-coordinates-message');
    const missingCoordinatesList = document.getElementById('missing-coordinates-list');
    
    if (missingLocations.length > 0) {
      // Clear previous list
      missingCoordinatesList.innerHTML = '';
      
      // Add each missing location to the list
      missingLocations.forEach(name => {
        const listItem = document.createElement('li');
        listItem.textContent = name;
        missingCoordinatesList.appendChild(listItem);
      });
      
      // Show the message
      missingCoordinatesMessage.classList.remove('hidden');
    } else {
      // Hide the message if no missing locations
      missingCoordinatesMessage.classList.add('hidden');
    }
    
    if (locations.length === 0) {
      // If no valid locations, show message in map container
      recommendationsMap.innerHTML = '<div class="flex h-full items-center justify-center"><p class="text-gray-500">No location data available for these recommendations</p></div>';
      return;
    }
    
    // Calculate average center point if multiple locations
    let centerLat = 0;
    let centerLng = 0;
    
    locations.forEach(loc => {
      centerLat += loc.lat;
      centerLng += loc.lng;
    });
    
    centerLat /= locations.length;
    centerLng /= locations.length;
    
    // Create the map
    window.map = new google.maps.Map(recommendationsMap, {
      center: { lat: centerLat, lng: centerLng },
      zoom: 12,
      mapTypeControl: true,
      fullscreenControl: true
    });
    
    // Create info window for marker click events
    const infoWindow = new google.maps.InfoWindow();
    
    // Create markers for each location
    locations.forEach(location => {
      const marker = new google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: window.map,
        title: location.name,
        activityId: location.activityId,
        animation: google.maps.Animation.DROP
      });
      
      // Store marker reference for filtering
      window.mapMarkers.push(marker);
      
      // Add click event to marker
      marker.addListener('click', () => {
        // Scroll to corresponding card in the card view
        const card = location.element;
        if (card) {
          // Update info panel
          const infoPanel = document.getElementById('map-info-panel');
          const infoTitle = document.getElementById('map-info-title');
          const infoCategory = document.getElementById('map-info-category');
          const infoContent = document.getElementById('map-info-content');
          
          // Set info panel content
          infoTitle.textContent = location.name;
          
          // Add category badge if available
          if (location.category) {
            infoCategory.innerHTML = `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">${location.category}</span>`;
          } else {
            infoCategory.innerHTML = '';
          }
          
          // Add recommendation descriptions
          const descriptions = Array.from(card.querySelectorAll('.text-gray-600')).map(el => el.textContent);
          if (descriptions.length > 0) {
            infoContent.textContent = descriptions[0]; // Show first description
          } else {
            infoContent.textContent = 'No description available';
          }
          
          // Show the info panel
          infoPanel.classList.remove('hidden');
        }
        
        // Open Google Maps info window
        infoWindow.setContent(`
          <div class="p-2">
            <h3 class="font-semibold">${location.name}</h3>
            ${location.category ? `<p class="text-sm text-gray-600">${location.category}</p>` : ''}
            ${location.placeId ? `<a href="https://www.google.com/maps/place/?q=place_id:${location.placeId}" target="_blank" class="text-blue-600 text-sm hover:underline">View on Google Maps</a>` : ''}
          </div>
        `);
        infoWindow.open(window.map, marker);
      });
    });
    
    // Center map function
    window.centerMap = function() {
      if (window.map && locations.length > 0) {
        // Find visible markers based on active filters
        const visibleMarkers = window.mapMarkers.filter(marker => marker.getVisible());
        
        if (visibleMarkers.length > 0) {
          const bounds = new google.maps.LatLngBounds();
          visibleMarkers.forEach(marker => {
            bounds.extend(marker.getPosition());
          });
          window.map.fitBounds(bounds);
          
          // Adjust zoom level if there's only one marker
          if (visibleMarkers.length === 1) {
            window.map.setZoom(15);
          }
        }
      }
    };
    
    // Initial centering
    window.centerMap();
  };
} 