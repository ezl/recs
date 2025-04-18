import os
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

app = create_app()

if __name__ == '__main__':
    # Always build Tailwind CSS before starting the server
    build_tailwind()
    
    app.run(debug=True, port=5001) 