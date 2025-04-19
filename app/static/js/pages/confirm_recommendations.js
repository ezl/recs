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
        
        // Validate form - ensure at least one recommendation
        const recommendationItems = document.querySelectorAll('.recommendation-item');
        if (recommendationItems.length === 0) {
            alert('Please add at least one recommendation');
            return;
        }
        
        // Check if all recommendations have names/descriptions
        let isValid = true;
        recommendationItems.forEach(item => {
            const nameInputs = item.querySelectorAll('input[name="recommendations[]"]');
            const descriptionInputs = item.querySelectorAll('textarea[name="descriptions[]"]');
            
            if (nameInputs.length > 0 && !nameInputs[0].value.trim()) {
                isValid = false;
            }
            
            if (descriptionInputs.length > 0 && !descriptionInputs[0].value.trim()) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            alert('Please fill out all recommendation names and descriptions');
            return;
        }
        
        // Show name modal if needed
        if (!recommenderNameInput.value) {
            nameModal.classList.remove('hidden');
            modalRecommenderName.focus();
            return;
        }
        
        // Submit the form
        submitForm();
    });
    
    // Name modal handlers
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', function() {
            nameModal.classList.add('hidden');
        });
    }
    
    // Handle form submission from modal
    document.querySelectorAll('.submit-with-name').forEach(btn => {
        btn.addEventListener('click', function() {
            const nameValue = modalRecommenderName.value.trim();
            if (!nameValue) {
                alert('Please enter your name');
                modalRecommenderName.focus();
                return;
            }
            
            recommenderNameInput.value = nameValue;
            nameModal.classList.add('hidden');
            submitForm();
        });
    });

    modalRecommenderName.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const submitWithNameBtn = document.querySelector('.submit-with-name');
            if (submitWithNameBtn) {
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
            feather.replace();
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
            feather.replace();
        }
        
        // Hide flash message if no more removed items
        if (removedItems.length === 0 && clientFlashContainer) {
            clientFlashContainer.classList.add('hidden');
        }
    }
    
    function submitForm() {
        // Show loading state
        submitButton.disabled = true;
        submitButton.querySelector('span').textContent = 'Sending...';
        submitButton.querySelector('svg:not(#spinner)').classList.add('hidden');
        submitButton.querySelector('#spinner').classList.remove('hidden');
        
        // Submit the form
        form.submit();
    }
}); 