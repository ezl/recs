# JavaScript Utilities

This directory contains reusable JavaScript utilities for the Recs application.

## Available Utilities

### Loading Overlay (loading.js)

Functions to control the global loading overlay component.

```javascript
// Show loading overlay with default or custom messages
showLoadingOverlay(title, subtitle);

// Hide loading overlay
hideLoadingOverlay();
```

#### Parameters:
- `title` (string, optional): Main heading text. Default: "Loading..."
- `subtitle` (string, optional): Secondary text. Default: "Please wait for awesomeness."

#### Example:
```javascript
// Show with default messages
showLoadingOverlay();

// Show with custom messages
showLoadingOverlay("Saving Data", "Your information is being processed...");

// Hide when operation completes
hideLoadingOverlay();
```

For detailed documentation, see `app/static/js/docs/loading-overlay.md` 