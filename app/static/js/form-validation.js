/**
 * Form Validation Utilities
 * Provides consistent form validation behavior across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all forms with the data-validate attribute
    const forms = document.querySelectorAll('form[data-validate]');
    console.log('Form validation script loaded. Found forms:', forms.length);
    
    forms.forEach(form => {
        console.log('Processing form:', form.id || 'unnamed form');
        
        // Find submit button: first look inside the form, then for buttons targeting this form via form attribute
        const formId = form.id;
        let submitButton = form.querySelector('button[type="submit"]');
        
        // If no button found inside the form, look for external buttons that reference this form
        if (!submitButton && formId) {
            submitButton = document.querySelector(`button[form="${formId}"][type="submit"]`);
            console.log(`Looking for external button for form #${formId}:`, submitButton ? 'found' : 'not found');
        }
        
        // Skip if no submit button found
        if (!submitButton) {
            console.log('No submit button found for form. Skipping validation.');
            return;
        }
        
        console.log('Found submit button:', submitButton);
        
        // Set initial state to disabled
        validateForm(form, submitButton);
        
        // Add listeners to all required inputs
        const requiredInputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        console.log('Required inputs:', requiredInputs.length);
        
        requiredInputs.forEach(input => {
            // Add input and change event listeners
            ['input', 'change'].forEach(eventType => {
                input.addEventListener(eventType, () => validateForm(form, submitButton));
            });
        });
        
        // Handle custom validation rules
        const minLengthInputs = form.querySelectorAll('[data-min-length]');
        console.log('Min length inputs:', minLengthInputs.length);
        
        minLengthInputs.forEach(input => {
            ['input', 'change'].forEach(eventType => {
                input.addEventListener(eventType, () => validateForm(form, submitButton));
            });
        });
    });
    
    // Function to validate the form and update button state
    function validateForm(form, submitButton) {
        console.log('Validating form:', form.id || 'unnamed form');
        
        // Check if all required fields have values
        const requiredInputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;
        
        // Validate all required fields
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                console.log('Invalid required field:', input.name || input.id || 'unnamed input');
            }
        });
        
        // Check inputs with min-length requirements
        const minLengthInputs = form.querySelectorAll('[data-min-length]');
        minLengthInputs.forEach(input => {
            const minLength = parseInt(input.dataset.minLength, 10);
            if (input.value.trim().length < minLength) {
                isValid = false;
                console.log(`Input doesn't meet min length (${minLength}):`, input.name || input.id || 'unnamed input', 'Current length:', input.value.trim().length);
            }
        });
        
        console.log('Form validation result:', isValid ? 'valid' : 'invalid');
        
        // Update button state
        updateButtonState(submitButton, isValid);
    }
    
    // Function to update button state based on validation
    function updateButtonState(button, isValid) {
        if (isValid) {
            button.disabled = false;
            button.classList.remove('btn-disabled');
        } else {
            button.disabled = true;
            button.classList.add('btn-disabled');
        }
    }
}); 