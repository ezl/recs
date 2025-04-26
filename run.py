import os
import sys
import subprocess
from app import create_app

def build_tailwind():
    """Build the Tailwind CSS file"""
    print("Building Tailwind CSS...")
    tailwind_path = os.path.join(os.getcwd(), 'node_modules', '.bin', 'tailwindcss')
    
    if not os.path.exists(tailwind_path):
        print("❌ Tailwind CSS executable not found at", tailwind_path)
        print("Installing tailwindcss package...")
        subprocess.run(["npm", "install", "tailwindcss@3", "--save-dev"], check=True)
    
    try:
        # Use the direct path to the executable
        result = subprocess.run(
            [
                tailwind_path, 
                "-i", "app/static/css/src/main.css", 
                "-o", "app/static/css/tailwind.css"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Tailwind CSS built successfully")
    except subprocess.CalledProcessError as e:
        print("❌ Tailwind CSS build failed:")
        print(e.stderr)

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Parse command line arguments
    port = 5000  # Default port
    
    # Check if port is specified in command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == '--port' and len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print(f"Invalid port number: {sys.argv[2]}")
                sys.exit(1)
    
    # Only build Tailwind when running the development server
    # In production, Tailwind is built during the build process
    if os.environ.get('FLASK_ENV') != 'production':
        build_tailwind()
    
    print(f"Starting server on port {port}")
    app.run(debug=True, port=port) 