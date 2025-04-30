/**
 * Recommendation filter component for the trip page
 * Handles filtering recommendations by contributor and category
 */
function initRecommendationFilter() {
  // Keep track of active filters
  const activeFilters = {
    contributor: new Set(),
    category: new Set()
  };

  // Initially set all filters as active
  document.querySelectorAll('[data-filter-type]').forEach(pill => {
    const filterType = pill.dataset.filterType;
    const filterValue = pill.dataset.filterValue;
    activeFilters[filterType].add(filterValue);
  });
  
  // Toggle filter pills
  document.querySelectorAll('[data-filter-type]').forEach(pill => {
    pill.addEventListener('click', function() {
      const filterType = this.dataset.filterType;
      const filterValue = this.dataset.filterValue;
      
      // Toggle pill appearance
      if (this.classList.contains('active')) {
        // Deactivate
        this.classList.remove('bg-blue-100', 'text-blue-800', 'border-blue-200', 'active');
        this.classList.add('bg-gray-100', 'text-gray-700', 'border-gray-200');
        activeFilters[filterType].delete(filterValue);
      } else {
        // Activate
        this.classList.remove('bg-gray-100', 'text-gray-700', 'border-gray-200');
        this.classList.add('bg-blue-100', 'text-blue-800', 'border-blue-200', 'active');
        activeFilters[filterType].add(filterValue);
      }
      
      // Apply filters to cards and map markers
      applyFilters();
    });
  });
  
  // Function to apply filters to recommendation cards and map markers
  function applyFilters() {
    const cards = document.querySelectorAll('.recommendation-card');
    const markers = window.mapMarkers || [];
    
    cards.forEach(card => {
      const cardCategory = card.dataset.category;
      const cardContributors = card.dataset.contributors.split(',');
      
      // Check if no filters are active for a type (show all)
      const noCategoryFilters = activeFilters.category.size === 0;
      const noContributorFilters = activeFilters.contributor.size === 0;
      
      // Check if card should be visible based on category filter
      const categoryMatch = 
        noCategoryFilters || 
        (cardCategory && activeFilters.category.has(cardCategory));
      
      // Check if card should be visible based on contributor filter
      const contributorMatch = 
        noContributorFilters || 
        cardContributors.some(id => activeFilters.contributor.has(id));
      
      // Show/hide card based on filter matches
      if (categoryMatch && contributorMatch) {
        card.classList.remove('hidden');
      } else {
        card.classList.add('hidden');
      }
      
      // Find and update corresponding map marker visibility
      if (window.map && markers.length > 0) {
        const activityId = card.dataset.activityId;
        const marker = markers.find(m => m.activityId === activityId);
        if (marker) {
          marker.setVisible(categoryMatch && contributorMatch);
        }
      }
    });
    
    // Update map bounds after filtering
    if (window.centerMap) {
      window.centerMap();
    }
  }

  // Toggle search input visibility
  const toggleSearchBtn = document.getElementById('toggle-search');
  const searchInputContainer = document.getElementById('search-input-container');
  const searchInput = document.getElementById('search-input');
  
  toggleSearchBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    searchInputContainer.classList.toggle('hidden');
    if (!searchInputContainer.classList.contains('hidden')) {
      searchInput.focus();
    }
  });
  
  // Close search when clicking outside
  document.addEventListener('click', function(e) {
    if (!searchInputContainer.contains(e.target) && e.target !== toggleSearchBtn) {
      searchInputContainer.classList.add('hidden');
    }
  });
  
  // Search functionality
  searchInput.addEventListener('input', function() {
    const searchTerm = this.value.trim().toLowerCase();
    
    // Remove all highlights first regardless of search term length
    document.querySelectorAll('.recommendation-card').forEach(card => {
      removeHighlights(card);
    });
    
    // If search term is empty, show all cards and stop
    if (searchTerm === '') {
      document.querySelectorAll('.recommendation-card').forEach(card => {
        card.classList.remove('search-hidden');
      });
      return;
    }
    
    // Only filter if searchTerm has 3 or more characters
    if (searchTerm.length >= 3) {
      searchCards(searchTerm);
    } else {
      // Show all cards if search term is too short
      document.querySelectorAll('.recommendation-card').forEach(card => {
        card.classList.remove('search-hidden');
      });
    }
  });
  
  function searchCards(searchTerm) {
    const cards = document.querySelectorAll('.recommendation-card');
    
    cards.forEach(card => {
      // Get all searchable content from the card
      const cardTitle = card.querySelector('h3').textContent.toLowerCase();
      const categoryElem = card.querySelector('.badge');
      const category = categoryElem ? categoryElem.textContent.toLowerCase() : '';
      
      // Get all recommendation texts
      const recommendationTexts = Array.from(card.querySelectorAll('.text-gray-600')).map(el => el.textContent.toLowerCase());
      
      // Get all contributor names - look in both structures
      // For multiple recommenders, names are in .text-sm.font-medium
      const contributorNamesMultiple = Array.from(card.querySelectorAll('.text-sm.font-medium')).map(el => el.textContent.toLowerCase());
      
      // For single recommender, name is in .text-gray-500.text-sm.mb-2
      const singleRecommenderElem = card.querySelector('.text-gray-500.text-sm.mb-2');
      const singleRecommenderText = singleRecommenderElem ? singleRecommenderElem.textContent.toLowerCase() : '';
      
      // Combine all possible sources of contributor names
      const allTexts = [
        cardTitle,
        category,
        ...recommendationTexts,
        ...contributorNamesMultiple,
        singleRecommenderText
      ].filter(Boolean); // Remove empty strings
      
      // Check if any text contains the search term
      const hasMatch = allTexts.some(text => text.includes(searchTerm));
      
      // If any match, show the card and highlight the matched text
      if (hasMatch) {
        card.classList.remove('search-hidden');
        
        // Highlight matches
        removeHighlights(card);
        highlightMatches(card, searchTerm);
      } else {
        card.classList.add('search-hidden');
        removeHighlights(card);
      }
    });
  }
  
  function highlightMatches(card, searchTerm) {
    const elementsToSearch = [
      ...card.querySelectorAll('h3'), // Title
      ...card.querySelectorAll('.badge'), // Category
      ...card.querySelectorAll('.text-gray-600'), // Recommendation texts
      ...card.querySelectorAll('.text-sm.font-medium'), // Contributor names (multiple)
      ...card.querySelectorAll('.text-gray-500.text-sm.mb-2') // "Recommended by" text (single)
    ];
    
    elementsToSearch.forEach(element => {
      const originalText = element.textContent;
      const lowerText = originalText.toLowerCase();
      
      // Simple case-insensitive match for highlighting
      if (lowerText.includes(searchTerm.toLowerCase())) {
        let newHtml = '';
        let lastIndex = 0;
        let index = lowerText.indexOf(searchTerm.toLowerCase());
        
        // Find all occurrences of the search term
        while (index !== -1) {
          // Add the text before the match
          newHtml += originalText.substring(lastIndex, index);
          
          // Add the highlighted match
          const match = originalText.substring(index, index + searchTerm.length);
          newHtml += `<mark class="bg-yellow-300 px-0.5 rounded">${match}</mark>`;
          
          // Move to the next match
          lastIndex = index + searchTerm.length;
          index = lowerText.indexOf(searchTerm.toLowerCase(), lastIndex);
        }
        
        // Add the remaining text
        newHtml += originalText.substring(lastIndex);
        
        element.innerHTML = newHtml;
      }
    });
  }
  
  function removeHighlights(card) {
    // Get all mark elements within the card
    const highlightedElements = card.querySelectorAll('mark');
    
    highlightedElements.forEach(el => {
      // Replace the mark with its text content
      const textNode = document.createTextNode(el.textContent);
      if (el.parentNode) {
        el.parentNode.replaceChild(textNode, el);
      }
    });
    
    // Clean up any potential empty elements created during the process
    card.normalize();
  }
} 