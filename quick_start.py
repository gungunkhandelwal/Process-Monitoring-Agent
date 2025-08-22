import os
import sys
import subprocess
from pathlib import Path

def print_header():
    print("=" * 50)
    print("   PROCESS MONITOR DASHBOARD - QUICK START ")
    print("=" * 50)
    print()

# Check requirements of project
def check_dependencies():
    print("Checking dependencies...")
    req_file = Path("requirements.txt")
    if req_file.exists():
        print("Installing dependencies from requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
            print("✅ All requirements installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install requirements from requirements.txt")
            return False
    else:
        print("requirements.txt not found, installing core packages...")
        required = ['django', 'djangorestframework', 'psutil', 'requests']
        missing = []
        for pkg in required:
            try:
                __import__(pkg.replace('-', '_'))
                print(f"✅ {pkg}")
            except ImportError:
                print(f"❌ {pkg}")
                missing.append(pkg)
        if missing:
            print(f"Installing: {', '.join(missing)}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
                print("✅ All packages installed")
            except subprocess.CalledProcessError:
                return False
    return True

def setup_django():
    print("\nSetting up Django project...")
    django_dir = Path("cyethack")
    if not django_dir.exists():
        print("❌ Django project directory not found")
        return False
    os.chdir(django_dir)
    try:
        subprocess.check_call([sys.executable, "manage.py", "makemigrations"])
        subprocess.check_call([sys.executable, "manage.py", "migrate"])
        print("✅ Database migrations completed")
    except subprocess.CalledProcessError:
        print("❌ Database migrations failed")
        os.chdir("..")
        return False
    # Create API key
    print("Creating API key for agent...")
    try:
        result = subprocess.run(
            [sys.executable, "manage.py", "create_api_key", "--name", "Windows Agent"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ API key created successfully")
            for line in result.stdout.split('\n'):
                if line.startswith('API Key:'):
                    api_key = line.split(':')[1].strip()
                    print(f"   API Key: {api_key}")
                    update_agent_config(api_key)
                    break
        else:
            print("❌ Failed to create API key")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
    os.chdir("..")
    return True

def update_agent_config(api_key):
    config_file = Path("agent/config.json")
    if config_file.exists():
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            config['api_key'] = api_key
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Agent configuration updated with API key")
        except Exception as e:
            print(f"❌ Failed to update agent config: {e}")

def start_django_server():
    print("\nStarting Django server...")
    print("The server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print()
    django_dir = Path("cyethack")
    os.chdir(django_dir)
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
    os.chdir("..")

def main():
    print_header()
    if not check_dependencies():
        sys.exit(1)
    if not setup_django():
        print("❌ Django setup failed")
        sys.exit(1)
    print("\n" + "=" * 40)
    print("✅ SETUP COMPLETE!")
    print("=" * 40)
    print("Next steps:")
    print("1. Start the Django server (this script will do this now)")
    response = input("Start Django server now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        start_django_server()
    else:
        print("\nTo start the server manually:")
        print("cd cyethack")
        print("python manage.py runserver")

if __name__ == "__main__":
    main()