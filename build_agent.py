import os
import sys
import subprocess
import shutil

def check_requirements():
    """Check if required packages are installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import psutil
        print("✓ psutil is installed")
    except ImportError:
        print("✗ psutil not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    
    try:
        import requests
        print("✓ requests is installed")
    except ImportError:
        print("✗ requests not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

def build_agent():
    """Build the agent using PyInstaller"""
    print("Building System Monitor Agent...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=SystemMonitorAgent",
        "--add-data=config.json;.",
        "--icon=agent/icon.ico",
        "agent/system_monitor_agent.py"
    ]
    
    if not os.path.exists("agent/icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        subprocess.check_call(cmd)
        print("✓ Agent built successfully!")
        
        if os.path.exists("agent/config.json"):
            shutil.copy("agent/config.json", "dist/")
            print("✓ Config file copied to dist/")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False
    
    return True

def main():
    print("=== System Monitor Agent Build Script ===\n")
    check_requirements()
    print()
    
    if build_agent():
        print("\n=== Build Complete! ===")
    else:
        print("\n=== Build Failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()