/**
 * Confirm Recommendations Page
 * Handles recommendation editing, validation, and submission
 */

document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const form = document.getElementById('recommendations-form');
    const submitButton = document.getElementById('submit-button');
    const addButton = document.getElementById('add-recommendation-button');
    const recommendationsContainer = document.getElementById('recommendations-container');
    const newRecommendationTemplate = document.getElementById('new-recommendation-template');
    const nameModal = document.getElementById('name-modal');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    const modalRecommenderName = document.getElementById('modal-recommender-name');
    const recommenderNameInput = document.getElementById('recommender_name');
    
    // Removed item tracking
    let removedItems = [];
    let lastRemovedItem = null;
    const clientFlashContainer = document.getElementById('client-flash-container');
    const undoButton = document.getElementById('undo-button');
    
    // Counter for new recommendation items
    let newItemCounter = 1000; // Start high to avoid conflicts with server-rendered items
    
    // Form validation and submission
    submitButton.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Clear any existing error messages
        clearValidationErrors();
        
        // Validate form - ensure at least one recommendation exists
        const recommendationItems = document.querySelectorAll('.recommendation-item');
        if (recommendationItems.length === 0) {
            alert('Please add at least one recommendation');
            return;
        }
        
        // Check for partially filled recommendations (description without name)
        let hasPartiallyFilledItems = false;
        
        recommendationItems.forEach(item => {
            const nameInput = item.querySelector('input[name="recommendations[]"]');
            const descriptionInput = item.querySelector('textarea[name="descriptions[]"]');
            
            if (nameInput && descriptionInput) {
                // Check if description is filled but name is empty
                if (!nameInput.value.trim() && descriptionInput.value.trim()) {
                    hasPartiallyFilledItems = true;
                    
                    // Create a yellow warning flash message
                    const warningDiv = document.createElement('div');
                    warningDiv.className = 'bg-yellow-100 text-yellow-800 border border-yellow-300 rounded-lg p-4 my-3 flex items-center validation-error';
                    warningDiv.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5 mr-3 text-yellow-500">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                        </svg>
                        <div class="flex-1">Please provide a name for this recommendation</div>
                        <button type="button" class="p-1.5 ml-3 rounded-full hover:bg-white/20" onclick="this.parentElement.remove()">
                            <span class="sr-only">Dismiss</span>
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-4 w-4">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                            </svg>
                        </button>
                    `;
                    
                    // Insert flash message after the recommendation item
                    if (item.nextElementSibling) {
                        item.parentNode.insertBefore(warningDiv, item.nextElementSibling);
                    } else {
                        item.parentNode.appendChild(warningDiv);
                    }
                    
                    // Highlight the field in red
                    nameInput.classList.add('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');
                }
            }
        });
        
        if (hasPartiallyFilledItems) {
            // Scroll to the first error
            const firstError = document.querySelector('.validation-error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return; // Prevent showing name modal and form submission
        }
        
        // Show name modal if needed - only if there are no validation errors
        if (!recommenderNameInput.value) {
            nameModal.classList.remove('hidden');
            modalRecommenderName.focus();
            return;
        }
        
        // Submit the form - empty recommendations will be filtered out in submitForm()
        submitForm();
    });
    
    // Name modal handlers
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', function() {
            nameModal.classList.add('hidden');
        });
    }
    
    // Initial state: Disable submit button if name field is empty
    const submitWithNameBtns = document.querySelectorAll('.submit-with-name');
    
    // Setup validation on load
    if (modalRecommenderName && submitWithNameBtns.length > 0) {
        // Initial state check
        updateSubmitButtonState();
        
        // Add input event listener to validate in real-time
        modalRecommenderName.addEventListener('input', updateSubmitButtonState);
    }
    
    // Function to update submit button state based on name field
    function updateSubmitButtonState() {
        const nameValue = modalRecommenderName.value.trim();
        const isValid = nameValue.length > 0;
        
        submitWithNameBtns.forEach(btn => {
            btn.disabled = !isValid;
            // Add visual feedback with opacity
            if (isValid) {
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                btn.classList.add('opacity-50', 'cursor-not-allowed');
            }
        });
    }
    
    // Handle form submission from modal
    submitWithNameBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const nameValue = modalRecommenderName.value.trim();
            if (nameValue) {
                recommenderNameInput.value = nameValue;
                nameModal.classList.add('hidden');
                submitForm();
            }
            // No else needed as the button should be disabled
        });
    });

    modalRecommenderName.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const submitWithNameBtn = document.querySelector('.submit-with-name');
            if (submitWithNameBtn && !submitWithNameBtn.disabled) {
                submitWithNameBtn.click();
            }
        }
    });
    
    // Add recommendation button handler
    addButton.addEventListener('click', addNewRecommendation);
    
    // Remove recommendation handler - use event delegation
    recommendationsContainer.addEventListener('click', function(e) {
        if (e.target.closest('.remove-recommendation')) {
            const button = e.target.closest('.remove-recommendation');
            const item = button.closest('.recommendation-item');
            removeRecommendation(item);
        }
    });
    
    // Add input validation handler via event delegation
    recommendationsContainer.addEventListener('input', function(e) {
        if (e.target.matches('input[name="recommendations[]"]')) {
            const item = e.target.closest('.recommendation-item');
            if (item) {
                // Clear any error messages for this item
                const nextSibling = item.nextElementSibling;
                if (nextSibling && nextSibling.classList.contains('validation-error')) {
                    nextSibling.remove();
                }
                
                // Remove red border
                e.target.classList.remove('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');
            }
        }
    });
    
    // Undo button handler
    if (undoButton) {
        undoButton.addEventListener('click', function() {
            undoRemove();
        });
    }
    
    // Functions
    function addNewRecommendation() {
        if (!newRecommendationTemplate) {
            console.error('New recommendation template not found');
            return;
        }
        
        // Clone the template content
        const newItem = document.importNode(newRecommendationTemplate.content, true);
        
        // Set a unique ID for the new item
        const itemId = `new-recommendation-${newItemCounter++}`;
        newItem.querySelector('.recommendation-item').id = itemId;
        
        // Add the new item to the container
        recommendationsContainer.appendChild(newItem);
        
        // Focus the first input of the new item
        const firstInput = document.getElementById(itemId).querySelector('input');
        if (firstInput) {
            firstInput.focus();
        }
        
        // Initialize Feather icons in the new item
        if (typeof feather !== 'undefined') {
            // No longer needed since we're using inline SVG
        }
    }
    
    function removeRecommendation(item) {
        // Store item data for potential undo
        lastRemovedItem = {
            element: item,
            html: item.outerHTML,
            index: Array.from(recommendationsContainer.children).indexOf(item)
        };
        removedItems.push(lastRemovedItem);
        
        // Remove the item from DOM
        item.remove();
        
        // Show flash message
        if (clientFlashContainer) {
            clientFlashContainer.classList.remove('hidden');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                if (!clientFlashContainer.classList.contains('hidden')) {
                    clientFlashContainer.classList.add('hidden');
                }
            }, 5000);
        }
    }
    
    function undoRemove() {
        if (removedItems.length === 0) return;
        
        // Get the last removed item
        const itemToRestore = removedItems.pop();
        
        // Create element from HTML
        const tempContainer = document.createElement('div');
        tempContainer.innerHTML = itemToRestore.html;
        const restoredItem = tempContainer.firstElementChild;
        
        // Insert at the original position or append at the end
        if (itemToRestore.index >= 0 && itemToRestore.index < recommendationsContainer.children.length) {
            recommendationsContainer.insertBefore(restoredItem, recommendationsContainer.children[itemToRestore.index]);
        } else {
            recommendationsContainer.appendChild(restoredItem);
        }
        
        // Initialize Feather icons in the restored item
        if (typeof feather !== 'undefined') {
            // No longer needed since we're using inline SVG
        }
        
        // Hide flash message if no more removed items
        if (removedItems.length === 0 && clientFlashContainer) {
            clientFlashContainer.classList.add('hidden');
        }
    }
    
    function submitForm() {
        // Remove recommendations with empty name and description
        const recommendationItems = document.querySelectorAll('.recommendation-item');
        
        recommendationItems.forEach(item => {
            const nameInput = item.querySelector('input[name="recommendations[]"]');
            const descriptionInput = item.querySelector('textarea[name="descriptions[]"]');
            
            // Check if both name and description are empty
            if (nameInput && descriptionInput && 
                !nameInput.value.trim() && 
                !descriptionInput.value.trim()) {
                // Remove this empty recommendation
                item.remove();
            }
        });
        
        // Check if there are any remaining items
        const remainingItems = document.querySelectorAll('.recommendation-item');
        if (remainingItems.length === 0) {
            alert('Please add at least one recommendation');
            return;
        }
        
        // Show loading state
        submitButton.disabled = true;
        submitButton.querySelector('span').textContent = 'Sending...';
        submitButton.querySelector('svg:not(#spinner)').classList.add('hidden');
        submitButton.querySelector('#spinner').classList.remove('hidden');
        
        // Submit the form
        form.submit();
    }
    
    // Helper function to clear validation errors
    function clearValidationErrors() {
        // Remove all error messages
        document.querySelectorAll('.validation-error').forEach(el => el.remove());
        
        // Remove red borders from inputs
        document.querySelectorAll('input.border-red-500').forEach(input => {
            input.classList.remove('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');
        });
    }
}); 