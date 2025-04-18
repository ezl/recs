# Flask Starter App

A modern web application starter template using Flask, Tailwind CSS, and SQLAlchemy.

## Features

- **Flask Backend**: Python-based web framework with Jinja2 templates
- **Tailwind CSS 4**: Via CDN for easy styling
- **SQLAlchemy ORM**: For database operations with SQLite in development
- **Environment Configuration**: Development, testing, and production setups
- **Modular Structure**: Well-organized code for scalability

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

## License

[MIT License](LICENSE)