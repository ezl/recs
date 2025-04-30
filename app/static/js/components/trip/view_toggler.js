/**
 * View toggler component for the trip page
 * Handles switching between card view and map view
 */
function initViewToggler() {
  // View toggle variables
  const cardViewBtn = document.getElementById('card-view-btn');
  const mapViewBtn = document.getElementById('map-view-btn');
  const cardView = document.getElementById('card-view');
  const mapView = document.getElementById('map-view');
  
  // Toggle view functions
  cardViewBtn.addEventListener('click', function() {
    // Show card view, hide map view
    cardView.classList.remove('hidden');
    mapView.classList.add('hidden');
    
    // Update button styles
    cardViewBtn.classList.remove('bg-white', 'text-gray-600');
    cardViewBtn.classList.add('bg-blue-100', 'text-blue-800');
    mapViewBtn.classList.remove('bg-blue-100', 'text-blue-800');
    mapViewBtn.classList.add('bg-white', 'text-gray-600');
  });
  
  mapViewBtn.addEventListener('click', function() {
    // Show map view, hide card view
    mapView.classList.remove('hidden');
    cardView.classList.add('hidden');
    
    // Update button styles
    mapViewBtn.classList.remove('bg-white', 'text-gray-600');
    mapViewBtn.classList.add('bg-blue-100', 'text-blue-800');
    cardViewBtn.classList.remove('bg-blue-100', 'text-blue-800');
    cardViewBtn.classList.add('bg-white', 'text-gray-600');
    
    // Trigger map resize event to ensure proper rendering
    if (window.google && window.google.maps && window.map) {
      google.maps.event.trigger(window.map, 'resize');
      centerMap();
    }
  });
  
  // Toggle filter section visibility
  const toggleFiltersBtn = document.getElementById('toggle-filters');
  const filterSection = document.getElementById('filter-section');
  
  toggleFiltersBtn.addEventListener('click', function() {
    filterSection.classList.toggle('hidden');
  });
} 