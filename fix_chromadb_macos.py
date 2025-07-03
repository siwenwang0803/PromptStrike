#!/usr/bin/env python3
"""
Fix ChromaDB installation on macOS
The issue: chroma-hnswlib fails to build due to -march=native flag
Solution: Install with proper environment variables
"""

import os
import subprocess
import sys

def fix_chromadb_install():
    """Fix ChromaDB installation on macOS"""
    
    print("🔧 Fixing ChromaDB installation for macOS...")
    
    # Set environment variables to avoid -march=native
    env = os.environ.copy()
    env['CFLAGS'] = '-std=c++11 -O3'
    env['CXXFLAGS'] = '-std=c++11 -O3'
    
    # For Apple Silicon Macs, we might need to specify arch
    import platform
    if platform.machine() == 'arm64':
        env['ARCHFLAGS'] = '-arch arm64'
    else:
        env['ARCHFLAGS'] = '-arch x86_64'
    
    # Try installing with no-binary to force compilation with our flags
    commands = [
        # First, try installing the specific version we need
        ['pip', 'install', '--no-binary', 'chroma-hnswlib', 'chroma-hnswlib==0.7.3'],
        
        # Then install ChromaDB
        ['pip', 'install', 'chromadb>=0.4.18'],
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Success: {cmd[-1]}")
            else:
                print(f"❌ Failed: {result.stderr}")
                
                # Alternative: try with pre-built wheel
                if 'chroma-hnswlib' in cmd[-1]:
                    print("Trying alternative installation method...")
                    # Install from a specific wheel URL if available
                    alt_cmd = ['pip', 'install', '--only-binary', ':all:', 'chroma-hnswlib']
                    subprocess.run(alt_cmd, env=env)
                    
        except Exception as e:
            print(f"Error: {e}")
    
    # Verify installation
    try:
        import chromadb
        print(f"\n✅ ChromaDB successfully installed! Version: {chromadb.__version__}")
        return True
    except ImportError:
        print("\n❌ ChromaDB installation failed")
        return False

if __name__ == "__main__":
    success = fix_chromadb_install()
    sys.exit(0 if success else 1)