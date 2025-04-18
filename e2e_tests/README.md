# Recs E2E Testing Suite

This directory contains end-to-end tests for the Recs application using Playwright.

## Prerequisites

- Node.js (v14 or later)
- npm or yarn
- Python environment with Recs application dependencies installed

## Setup

1. Install npm dependencies:

```bash
cd e2e_tests
npm install
```

2. Install TypeScript definitions (to fix linting errors):

```bash
npm install --save-dev @types/node typescript
```

3. Install Playwright browsers:

```bash
npx playwright install
```

## Running Tests

Run all tests:

```bash
npm test
```

Run with browser UI visible:

```bash
npm run test:headed
```

Run with the Playwright UI:

```bash
npm run test:ui
```

Run a specific test file:

```bash
npx playwright test tests/trip-creation.spec.js
```

## Test Descriptions

The test suite covers the following scenarios:

1. **Trip Creation and Sharing Flow** (`trip-creation.spec.js`)
   - Creating a new trip
   - Generating a shareable link
   - Creating trips with unique slugs

2. **Recommendation Submission Process** (`recommendation-submission.spec.js`)
   - Submitting text recommendations
   - Processing and confirming recommendations
   - Handling empty submissions

3. **Audio Recording and Transcription** (`audio-recommendation.spec.js`)
   - Toggling between text and audio input modes
   - Processing mock audio transcriptions
   - Testing UI elements for audio recording

4. **Recommendation Removal and Undo** (`recommendation-removal.spec.js`)
   - Removing recommendations
   - Undoing removed recommendations
   - Submitting after removing recommendations
   - Handling removal of all recommendations

## Test Reports

After running tests, a report is generated in the `playwright-report` directory. You can view it by opening `playwright-report/index.html` in your browser.

## CI Integration

These tests can be integrated into a CI pipeline. The configuration is set up to run in CI environments by setting the `CI` environment variable. 