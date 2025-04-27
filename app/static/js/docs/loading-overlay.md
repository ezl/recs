# Loading Overlay Component

This document explains how to use the loading overlay component in the Recs application.

## Overview

The loading overlay is a full-screen component that provides feedback to users during operations that may take some time to complete, such as:
- Form submissions
- API calls
- Page transitions
- Data processing

The overlay has a semi-transparent white background with a centered content box that includes:
- A loading spinner
- A customizable title (default: "Loading...")
- A customizable subtitle (default: "Please wait for awesomeness.")

## Usage

### 1. JavaScript API

The loading overlay can be controlled directly via JavaScript functions:

```javascript
// Show the loading overlay with default messages
showLoadingOverlay();

// Show with custom messages
showLoadingOverlay("Creating Trip", "Please wait while we set up your adventure...");

// Hide the overlay when operation is complete
hideLoadingOverlay();
```

#### Parameters

- `title` (string, optional): The main heading text. Defaults to "Loading...".
- `subtitle` (string, optional): The descriptive text below the heading. Defaults to "Please wait for awesomeness."

### 2. Automatic Form Handling

Forms can automatically show the loading overlay when submitted by adding data attributes:

```html
<form action="/submit" method="post" 
      data-show-loading="true" 
      data-loading-title="Submitting Form" 
      data-loading-subtitle="Processing your information...">
  <!-- Form fields -->
  <button type="submit">Submit</button>
</form>
```

#### Form Attributes

- `data-show-loading="true"`: Enables the loading overlay for this form
- `data-loading-title="..."`: (Optional) Sets custom title text
- `data-loading-subtitle="..."`: (Optional) Sets custom subtitle text

### 3. Common Use Cases

#### Page Transitions

```javascript
// Show loading before redirecting
showLoadingOverlay("Redirecting", "Taking you to your trip page...");
window.location.href = "/trip/123";
```

#### API Calls

```javascript
// Show loading before API call
showLoadingOverlay("Saving Recommendations", "Storing your great ideas...");

fetch('/api/recommendations', {
  method: 'POST',
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => {
  // Hide loading after successful response
  hideLoadingOverlay();
  // Update UI
})
.catch(error => {
  // Hide loading on error
  hideLoadingOverlay();
  // Show error message
});
```

#### Form Submission with Validation

```javascript
document.querySelector('#my-form').addEventListener('submit', function(e) {
  // Prevent default submission
  e.preventDefault();
  
  // Validate form
  if (!validateForm()) {
    // Don't show loading if validation fails
    return false;
  }
  
  // Show loading overlay
  showLoadingOverlay("Validating Information", "Please wait...");
  
  // Submit form
  this.submit();
});
```

## Implementation Details

- The loading overlay is included in `base.html` so it's available on all pages
- The JavaScript utilities are in `app/static/js/utils/loading.js`
- Automatic form handling is initialized in `main.js`
- The overlay uses Tailwind CSS classes for styling
- While active, the overlay prevents scrolling of the page content 