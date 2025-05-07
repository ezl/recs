/**
 * Destination Autocomplete Component
 * 
 * Provides an autocomplete UI component for destination search
 * using the DestinationSearch library.
 * 
 * Features:
 * - Debounced input handling
 * - Keyboard navigation
 * - Mouse selection
 * - Customizable rendering
 * - Mobile-friendly
 */

class DestinationAutocomplete {
    /**
     * Create a new destination autocomplete instance
     * @param {HTMLElement|string} inputElement - Input element or selector
     * @param {Object} options - Configuration options
     */
    constructor(inputElement, options = {}) {
        // Default configuration
        this.config = {
            minChars: 2,              // Minimum characters to trigger search
            debounceTime: 300,        // Debounce time in milliseconds
            maxResults: 8,            // Maximum number of results to show
            sources: ['database', 'google', 'openstreetmap'], // Data sources to search
            placeholder: 'Search for a destination...', // Input placeholder
            width: '100%',            // Width of the autocomplete
            position: 'below',        // Position of dropdown (below or above)
            mobileBreakpoint: 768,    // Mobile breakpoint in px
            clearOnSelect: true,      // Clear input on selection
            onSelect: null,           // Callback when item is selected
            ...options
        };

        // Initialize DOM elements
        this.inputElement = typeof inputElement === 'string' 
            ? document.querySelector(inputElement) 
            : inputElement;
            
        if (!this.inputElement) {
            throw new Error('Input element not found');
        }
        
        // Set initial state
        this.state = {
            loading: false,
            results: [],
            selectedIndex: -1,
            isOpen: false,
            query: ''
        };

        // Set up debounce timer reference
        this.debounceTimer = null;
        
        // Create container and dropdown
        this._setupDomElements();
        
        // Bind event handlers
        this._bindEvents();
    }

    /**
     * Set up DOM elements for the autocomplete
     * @private
     */
    _setupDomElements() {
        // Create container wrapper
        this.container = document.createElement('div');
        this.container.className = 'destination-autocomplete-container';
        
        // Move the input element into the container
        const originalParent = this.inputElement.parentNode;
        originalParent.insertBefore(this.container, this.inputElement);
        this.container.appendChild(this.inputElement);
        
        // Set input attributes
        this.inputElement.setAttribute('autocomplete', 'off');
        this.inputElement.setAttribute('placeholder', this.config.placeholder);
        this.inputElement.className += ' destination-autocomplete-input';
        
        // Create dropdown menu
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'destination-autocomplete-dropdown';
        this.dropdown.classList.add('hidden');
        
        // Create loader element
        this.loader = document.createElement('div');
        this.loader.className = 'destination-autocomplete-loader';
        this.loader.classList.add('hidden');
        
        // Append dropdown and loader to container
        this.container.appendChild(this.dropdown);
        this.container.appendChild(this.loader);
    }

    /**
     * Bind event handlers
     * @private
     */
    _bindEvents() {
        // Input events
        this.inputElement.addEventListener('input', this._handleInput.bind(this));
        this.inputElement.addEventListener('focus', this._handleFocus.bind(this));
        this.inputElement.addEventListener('blur', this._handleBlur.bind(this));
        this.inputElement.addEventListener('keydown', this._handleKeydown.bind(this));
        
        // Dropdown events
        this.dropdown.addEventListener('mousedown', this._handleDropdownMousedown.bind(this));
        
        // Click outside to close
        document.addEventListener('click', this._handleDocumentClick.bind(this));
        
        // Window resize for mobile handling
        window.addEventListener('resize', this._handleResize.bind(this));
    }

    /**
     * Handle input changes with debounce
     * @param {Event} event - Input event
     * @private
     */
    _handleInput(event) {
        const query = event.target.value.trim();
        this.state.query = query;
        
        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Hide dropdown if query is too short
        if (query.length < this.config.minChars) {
            this._hideDropdown();
            this._setLoading(false);
            return;
        }
        
        // Show loader
        this._setLoading(true);
        
        // Debounce search
        this.debounceTimer = setTimeout(() => {
            this._performSearch(query);
        }, this.config.debounceTime);
    }

    /**
     * Perform search using DestinationSearch library
     * @param {string} query - The search query
     * @private
     */
    async _performSearch(query) {
        if (!query || query.length < this.config.minChars) {
            this._setLoading(false);
            return;
        }
        
        try {
            // Call DestinationSearch library
            const results = await DestinationSearch.search(query, {
                sources: this.config.sources,
                limit: this.config.maxResults
            });
            
            // Update state and render results
            this.state.results = results;
            this.state.selectedIndex = -1;
            
            if (results.length > 0) {
                this._renderDropdown();
                this._showDropdown();
            } else {
                this._hideDropdown();
            }
        } catch (error) {
            console.error('Error searching destinations:', error);
            this._hideDropdown();
        } finally {
            this._setLoading(false);
        }
    }

    /**
     * Render the dropdown with results
     * @private
     */
    _renderDropdown() {
        if (!this.state.results.length) {
            this.dropdown.innerHTML = '';
            return;
        }
        
        const fragment = document.createDocumentFragment();
        
        this.state.results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'destination-autocomplete-item';
            item.setAttribute('data-index', index);
            
            if (index === this.state.selectedIndex) {
                item.className += ' selected';
            }
            
            item.style.padding = '8px 12px';
            item.style.cursor = 'pointer';
            item.style.overflow = 'hidden';
            item.style.textOverflow = 'ellipsis';
            item.style.whiteSpace = 'nowrap';
            
            // Highlight on hover
            item.style.transition = 'background-color 0.2s';
            
            // Hover styling handled in CSS class
            
            item.innerHTML = this._renderResultItem(result);
            fragment.appendChild(item);
        });
        
        this.dropdown.innerHTML = '';
        this.dropdown.appendChild(fragment);
    }

    /**
     * Render an individual result item
     * @param {Object} result - The destination result
     * @returns {string} HTML for the result item
     * @private
     */
    _renderResultItem(result) {
        return `
            <div class="destination-item-content">
                <div class="destination-item-name">${result.display_name || result.name}</div>
                <div class="destination-item-details">
                    ${result.type ? `<span class="destination-item-type">${result.type}</span>` : ''}
                    <span class="destination-item-source">${result.source}</span>
                </div>
            </div>
        `;
    }

    /**
     * Show the dropdown
     * @private
     */
    _showDropdown() {
        if (this.state.results.length === 0) return;
        this.dropdown.classList.remove('hidden');
        this.state.isOpen = true;
        // Position dropdown based on config
        if (this.config.position === 'above') {
            this.dropdown.classList.add('position-above');
            this.dropdown.classList.remove('position-below');
        } else {
            this.dropdown.classList.add('position-below');
            this.dropdown.classList.remove('position-above');
        }
    }

    /**
     * Hide the dropdown
     * @private
     */
    _hideDropdown() {
        this.dropdown.classList.add('hidden');
        this.state.isOpen = false;
    }

    /**
     * Handle dropdown mousedown event
     * @param {Event} event - Mousedown event
     * @private
     */
    _handleDropdownMousedown(event) {
        event.preventDefault();
        
        const item = event.target.closest('.destination-autocomplete-item');
        if (!item) return;
        
        const index = parseInt(item.getAttribute('data-index'), 10);
        this._selectItem(index);
    }

    /**
     * Handle input focus event
     * @private
     */
    _handleFocus() {
        if (this.state.results.length > 0) {
            this._showDropdown();
        }
    }

    /**
     * Handle input blur event
     * @private
     */
    _handleBlur() {
        // Delayed hide to allow for dropdown click to register
        setTimeout(() => {
            if (this.state.isOpen) {
                this._hideDropdown();
            }
        }, 150);
    }

    /**
     * Handle document click event
     * @param {Event} event - Click event
     * @private
     */
    _handleDocumentClick(event) {
        if (!this.container.contains(event.target) && this.state.isOpen) {
            this._hideDropdown();
        }
    }

    /**
     * Handle keydown event for keyboard navigation
     * @param {KeyboardEvent} event - Keydown event
     * @private
     */
    _handleKeydown(event) {
        // Only handle keys if dropdown is open or Enter on filled input
        if (!this.state.isOpen && 
            !(event.key === 'Enter' && this.inputElement.value.trim().length >= this.config.minChars)) {
            return;
        }
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this._moveSelection(1);
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this._moveSelection(-1);
                break;
                
            case 'Enter':
                event.preventDefault();
                if (this.state.selectedIndex >= 0) {
                    this._selectItem(this.state.selectedIndex);
                } else if (this.inputElement.value.trim().length >= this.config.minChars) {
                    // If no selection but valid query, trigger search and select first result
                    this._performSearch(this.inputElement.value.trim()).then(() => {
                        if (this.state.results.length > 0) {
                            this._selectItem(0);
                        }
                    });
                }
                break;
                
            case 'Escape':
                event.preventDefault();
                this._hideDropdown();
                break;
                
            case 'Tab':
                this._hideDropdown();
                break;
        }
    }

    /**
     * Move the selection up or down
     * @param {number} direction - Direction to move (1 for down, -1 for up)
     * @private
     */
    _moveSelection(direction) {
        if (!this.state.results.length) return;
        
        let newIndex = this.state.selectedIndex + direction;
        
        // Loop to the other end if out of bounds
        if (newIndex < 0) {
            newIndex = this.state.results.length - 1;
        } else if (newIndex >= this.state.results.length) {
            newIndex = 0;
        }
        
        this.state.selectedIndex = newIndex;
        this._renderDropdown();
        
        // Scroll into view if needed
        const selectedItem = this.dropdown.querySelector(`.destination-autocomplete-item[data-index="${newIndex}"]`);
        if (selectedItem) {
            if (selectedItem.offsetTop < this.dropdown.scrollTop) {
                this.dropdown.scrollTop = selectedItem.offsetTop;
            } else if (selectedItem.offsetTop + selectedItem.offsetHeight > this.dropdown.scrollTop + this.dropdown.offsetHeight) {
                this.dropdown.scrollTop = selectedItem.offsetTop + selectedItem.offsetHeight - this.dropdown.offsetHeight;
            }
        }
    }

    /**
     * Select an item by index
     * @param {number} index - Index of the item to select
     * @private
     */
    _selectItem(index) {
        const result = this.state.results[index];
        if (!result) return;
        
        // Fill input with selected value
        this.inputElement.value = result.display_name || result.name;
        
        // Hide dropdown
        this._hideDropdown();
        
        // Clear if configured
        if (this.config.clearOnSelect) {
            setTimeout(() => {
                this.inputElement.value = '';
            }, 100);
        }
        
        // Call onSelect callback if provided
        if (typeof this.config.onSelect === 'function') {
            this.config.onSelect(result);
        }
        
        // Trigger change event on input
        const event = new Event('change', { bubbles: true });
        this.inputElement.dispatchEvent(event);
    }

    /**
     * Handle window resize event
     * @private
     */
    _handleResize() {
        const isMobile = window.innerWidth < this.config.mobileBreakpoint;
        
        if (isMobile) {
            // Mobile optimizations
            this.dropdown.style.maxHeight = '70vh';
            this.dropdown.style.width = '100%';
        } else {
            // Desktop view
            this.dropdown.style.maxHeight = '300px';
            this.dropdown.style.width = '100%';
        }
    }

    /**
     * Set loading state
     * @param {boolean} isLoading - Whether the component is loading
     * @private
     */
    _setLoading(isLoading) {
        this.state.loading = isLoading;
        if (isLoading) {
            this.loader.classList.remove('hidden');
        } else {
            this.loader.classList.add('hidden');
        }
    }

    /**
     * Manually set search sources
     * @param {Array} sources - Array of source names
     * @public
     */
    setSources(sources) {
        if (Array.isArray(sources)) {
            this.config.sources = sources;
        }
    }

    /**
     * Clear the input and results
     * @public
     */
    clear() {
        this.inputElement.value = '';
        this.state.results = [];
        this.state.selectedIndex = -1;
        this._hideDropdown();
    }

    /**
     * Destroy the autocomplete instance
     * @public
     */
    destroy() {
        // Remove event listeners
        this.inputElement.removeEventListener('input', this._handleInput);
        this.inputElement.removeEventListener('focus', this._handleFocus);
        this.inputElement.removeEventListener('blur', this._handleBlur);
        this.inputElement.removeEventListener('keydown', this._handleKeydown);
        this.dropdown.removeEventListener('mousedown', this._handleDropdownMousedown);
        document.removeEventListener('click', this._handleDocumentClick);
        window.removeEventListener('resize', this._handleResize);
        
        // Restore DOM
        const originalParent = this.container.parentNode;
        originalParent.insertBefore(this.inputElement, this.container);
        originalParent.removeChild(this.container);
        
        // Clear references
        this.container = null;
        this.dropdown = null;
        this.loader = null;
    }
}

// Check if we're in a CommonJS environment
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = DestinationAutocomplete;
} 