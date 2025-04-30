# Flask Starter App

A modern web application starter template using Flask, Tailwind CSS, and SQLAlchemy.

## Features

- **Flask Backend**: Python-based web framework with Jinja2 templates
- **Tailwind CSS 4**: Via CDN for easy styling
- **SQLAlchemy ORM**: For database operations with SQLite in development
- **Environment Configuration**: Development, testing, and production setups
- **Modular Structure**: Well-organized code for scalability

## End-to-End Testing

This project includes an automated E2E test suite built with Playwright. The tests run against a dedicated test server on port 5001 with a fresh test database.

To run the tests:
```bash
# Navigate to the e2e_tests directory
cd e2e_tests

# Install test dependencies
npm install

# Run tests (headless mode)
npm test

# Run tests with visible browser
npm run test:headed

# Run tests with Playwright UI for debugging
npm run test:ui
```

For more details, see the documentation in the `e2e_tests` directory.

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ (optional, for front-end dependencies)
- npm

### Installation

1. Clone this repository
   ```
   git clone <repository-url>
   cd flask-starter-app
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies
   ```
   pip install -r requirements.txt
   ```

4. Install npm dependencies
   ```
   npm install
   ```

5. Set up SQLAlchemy and initialize the database
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the application
   ```
   python run.py
   ```

## CSS and Styling

This project uses Tailwind CSS with a build process for optimal performance and custom component support.

### CSS Structure

- Source CSS files are in `app/static/css/src/`
- `main.css` is the entry point that imports Tailwind and defines custom components
- Custom components and utilities use Tailwind's `@apply` directive
- Compiled CSS is output to `app/static/css/tailwind.css`

### How to Modify CSS

1. Edit the files in `app/static/css/src/` directory
2. Custom components should be added in the `@layer components {}` section
3. Custom utilities should be added in the `@layer utilities {}` section
4. Build the CSS after making changes (see below)

### Building CSS

CSS is automatically built when you run the Flask application in development mode.

**To manually rebuild CSS:**

```bash
# Using npm script
npm run build-tailwind

# OR using direct path
./node_modules/.bin/tailwindcss -i app/static/css/src/main.css -o app/static/css/tailwind.css
```

**To watch for CSS changes:**

```bash
./node_modules/.bin/tailwindcss -i app/static/css/src/main.css -o app/static/css/tailwind.css --watch
```

### Adding Tailwind Plugins

1. Install the plugin via npm:
   ```bash
   npm install -D @tailwindcss/forms
   ```

2. Add it to `tailwind.config.js`:
   ```javascript
   plugins: [
     require('@tailwindcss/forms'),
     // other plugins...
   ]
   ```

3. Rebuild CSS to apply changes.

## Project Structure

```
├── app/
│   ├── __init__.py       # Flask app initialization
│   ├── routes.py         # Route definitions
│   ├── templates/        # Jinja2 templates
│   ├── static/           # Static files (CSS, JS)
│   └── database/         # Database models and operations
├── config.py             # Configuration for different environments
├── migrations/           # Database migrations
└── run.py                # Application entry point
```

## Configuration

The app uses different configuration classes for different environments:

- `DevConfig`: Development environment (default)
- `TestConfig`: Testing environment
- `ProdConfig`: Production environment

Set the `FLASK_ENV` environment variable to switch between configurations.

## Database

This starter uses SQLAlchemy ORM with SQLite for local development. The database configuration can be found in `config.py`.

For production, you can modify the database connection URI in the environment variables or config file.

## Database Schema Management

### Schema Verification

This project includes a database schema verification tool that checks if the actual database schema matches the expected schema based on SQLAlchemy models. This helps identify missing tables or columns.

To run the verification:
```bash
# Report any schema issues without fixing them
python verify_db_schema.py

# Automatically fix schema issues
python verify_db_schema.py --fix
```

This tool is useful for:
- Testing before deployment to ensure all migrations have been properly applied
- Identifying differences between development and production databases
- Fixing schema issues when migrations fail

### Schema Issues

If you encounter database errors like these:
```
sqlalchemy.exc.ProgrammingError: column activities.google_place_id does not exist
sqlalchemy.exc.ProgrammingError: column activities.place_data does not exist
```

You can fix these issues using one of the following methods:

1. Run the fix script:
   ```
   python fix_missing_column.py
   ```
   
2. Run the schema verification with fix option:
   ```
   python verify_db_schema.py --fix
   ```
   
3. Run Alembic migrations:
   ```
   flask db upgrade
   ```

For detailed instructions on fixing these issues in production, see the `PRODUCTION_FIX.md` file.

## Known Issues and Troubleshooting

### Missing Database Columns

If you encounter an error like this in production:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column activities.google_place_id does not exist
```

This indicates that the database schema is out of sync. To fix it:

1. Run the fix script:
   ```
   python fix_missing_column.py
   ```
   
2. Alternatively, run the Alembic migration:
   ```
   flask db upgrade
   ```

This issue can happen if the migration didn't run correctly during deployment. Always make sure to run migrations as part of your deployment process.

## License

[MIT License](LICENSE)

## Deployment to Render.com

This application is configured for deployment to Render.com, a modern cloud platform.

### Prerequisites for Deployment

1. Create a Render.com account at https://render.com
2. Have your application code in a Git repository (GitHub, GitLab, etc.)

### Deployment Steps

1. **Connect your repository to Render.com**
   - In the Render dashboard, click "New" and select "Web Service"
   - Connect your Git repository
   - Choose the branch you want to deploy

2. **Configure the Web Service**
   - Name: Choose a name for your service (e.g., "recommendation-app")
   - Environment: Select "Python"
   - Build Command: `./build.sh`
   - Start Command: `gunicorn run:app --workers=2 --threads=2 --timeout=120`

3. **Set Environment Variables**
   - FLASK_ENV: `production`
   - SECRET_KEY: [Generate a secure random key]
   - DATABASE_URL: [Your database connection string]
   - OPENAI_API_KEY: [Your OpenAI API key]
   - GOOGLE_MAPS_API_KEY: [Your Google Maps API key]

4. **Set up the Database**
   - In the Render dashboard, click "New" and select "PostgreSQL"
   - Name: Choose a name for your database (e.g., "recommendation-db")
   - After creation, copy the Internal Database URL
   - Add it as the DATABASE_URL in your web service environment variables

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Render.yaml Configuration

This repository includes a `render.yaml` file for Blueprint deployments, which allows you to deploy the entire stack (web service and database) in one go.

To use the Blueprint:
1. Fork this repository
2. In Render dashboard, click "New" and select "Blueprint"
3. Connect your forked repository
4. Render will detect the render.yaml file and set up all services

### Post-Deployment

After deployment, you should:
1. Run database migrations if necessary
2. Verify that all environment variables are correctly set
3. Monitor the application logs for any issues

## Deployment

### Database Migrations

When deploying to production, ensure that database migrations run properly:

1. The `build.sh` script now includes multiple fallback methods for running migrations:
   - First attempts to run Alembic migrations
   - If that fails, runs the `fix_missing_column.py` script
   - As a last resort, uses direct SQLAlchemy table creation

2. If you're experiencing database schema issues in production, you can manually run:
   ```
   flask db upgrade
   ```
   or
   ```
   python fix_missing_column.py
   ```

3. Make sure your environment variables are correctly set in production:
   - `DATABASE_URL` should point to your production database
   - `FLASK_APP` should be set to `run.py`

### Troubleshooting Deployment Issues

If you encounter the "activities.google_place_id does not exist" error in production:

1. SSH into your production server
2. Navigate to your application directory
3. Run `python fix_missing_column.py`
4. Restart your application server

For Render.com deployments, you can use the Web Shell to execute these commands directly in the production environment.

# Refactoring Proposals

This repository contains proposals for refactoring several large files in the codebase to improve maintainability and organization. Each proposal is in a separate file for clarity.

## Files to Refactor

1. [Trip HTML Template Refactoring](refactoring_trip_html.md) - Breaking up the large 694-line trip.html template into smaller, component-based files using a feature-based organization approach.

2. [Add Recommendation JS Refactoring](refactoring_add_recommendation_js.md) - Refactoring the 552-line add_recommendation.js file into modular components that each handle a specific responsibility.

3. [Database Models Refactoring](refactoring_models_py.md) - Converting the 375-line models.py file into a package with domain-specific model files.

## Implementation Guidelines

For implementing these refactoring proposals:

1. Create a dedicated branch for each refactoring task
2. Implement changes incrementally, testing after each significant change
3. Ensure all tests pass before and after refactoring
4. Have another team member review the changes before merging
5. Document any issues or challenges encountered during refactoring

These refactorings are designed to:
- Improve code organization
- Make the codebase more maintainable
- Support collaborative development
- Make future changes easier
- Follow standard best practices for component organization