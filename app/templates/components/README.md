# Components

This directory contains reusable UI components for the Recs application.

## Available Components

### Loading Overlay

**File**: `loading_overlay.html`

A full-screen overlay that provides user feedback during loading operations.

#### Usage
To use the loading overlay in a template:

1. The overlay is already included in `base.html` and available on all pages
2. Control it via JavaScript:

```javascript
// Show the overlay
showLoadingOverlay("Processing", "Please wait...");

// Hide the overlay
hideLoadingOverlay();
```

3. For forms, add the `data-show-loading="true"` attribute:

```html
<form action="/submit" method="post" data-show-loading="true">
  <!-- Form fields -->
</form>
```

For detailed documentation, see `app/static/js/docs/loading-overlay.md`

### Other Components

[Other components documentation will be added here] 