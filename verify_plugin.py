#!/usr/bin/env python3
"""
Verification script for Green-Ampt Parameter Generator QGIS Plugin

This script checks:
1. Plugin directory structure
2. Required files
3. Metadata validity
4. green-ampt-estimation availability
5. Python dependencies
"""

import os
import sys
from pathlib import Path

def check_plugin_structure():
    """Check if plugin directory structure is correct"""
    print("Checking plugin structure...")
    
    required_files = [
        "green_ampt_plugin/__init__.py",
        "green_ampt_plugin/green_ampt_plugin.py",
        "green_ampt_plugin/metadata.txt",
        "green_ampt_plugin/icon.png",
        "green_ampt_plugin/processing/__init__.py",
        "green_ampt_plugin/processing/green_ampt_provider.py",
        "green_ampt_plugin/processing/green_ampt_algorithm.py",
        "green_ampt_plugin/processing/algorithms/__init__.py",
        "green_ampt_plugin/processing/algorithms/green_ampt_ssurgo.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = Path(file_path)
        if not full_path.exists():
            missing_files.append(file_path)
            print(f"  ✗ Missing: {file_path}")
        else:
            print(f"  ✓ Found: {file_path}")
    
    if missing_files:
        print(f"\n⚠ Warning: {len(missing_files)} required files are missing!")
        return False
    else:
        print("\n✓ All required files present")
        return True

def check_metadata():
    """Check metadata.txt validity"""
    print("\nChecking metadata.txt...")
    
    metadata_path = Path("green_ampt_plugin/metadata.txt")
    if not metadata_path.exists():
        print("  ✗ metadata.txt not found")
        return False
    
    required_keys = [
        "name", "qgisMinimumVersion", "description", "version",
        "author", "email", "about", "tracker", "repository"
    ]
    
    with open(metadata_path, 'r') as f:
        content = f.read()
    
    missing_keys = []
    for key in required_keys:
        if f"{key}=" not in content:
            missing_keys.append(key)
            print(f"  ✗ Missing key: {key}")
        else:
            print(f"  ✓ Found key: {key}")
    
    if missing_keys:
        print(f"\n⚠ Warning: {len(missing_keys)} required metadata keys are missing!")
        return False
    else:
        print("\n✓ Metadata is valid")
        return True

def check_green_ampt_estimation():
    """Check if green-ampt-estimation is available"""
    print("\nChecking green-ampt-estimation...")
    
    green_ampt_path = Path("green-ampt-estimation")
    if not green_ampt_path.exists():
        print("  ✗ green-ampt-estimation directory not found")
        print("  → Run: git submodule update --init --recursive")
        return False
    
    required_modules = [
        "green-ampt-estimation/green_ampt_tool/__init__.py",
        "green-ampt-estimation/green_ampt_tool/config.py",
        "green-ampt-estimation/green_ampt_tool/workflow.py",
        "green-ampt-estimation/green_ampt_tool/parameters.py",
    ]
    
    missing_modules = []
    for module_path in required_modules:
        full_path = Path(module_path)
        if not full_path.exists():
            missing_modules.append(module_path)
            print(f"  ✗ Missing: {module_path}")
        else:
            print(f"  ✓ Found: {module_path}")
    
    if missing_modules:
        print(f"\n⚠ Warning: {len(missing_modules)} required modules are missing!")
        return False
    else:
        print("\n✓ green-ampt-estimation is available")
        return True

def check_dependencies():
    """Check Python dependencies"""
    print("\nChecking Python dependencies...")
    
    # Map pip package names to import names
    required_packages = {
        "geopandas": "geopandas",
        "rasterio": "rasterio",
        "pandas": "pandas",
        "numpy": "numpy",
        "requests": "requests",
        "pyyaml": "yaml",
    }
    
    missing_packages = []
    for pip_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✓ {pip_name} is installed")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"  ✗ {pip_name} is NOT installed")
    
    if missing_packages:
        print(f"\n⚠ Warning: {len(missing_packages)} required packages are missing!")
        print("\nTo install missing packages:")
        print("  pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✓ All required packages are installed")
        return True

def main():
    """Run all checks"""
    print("=" * 60)
    print("Green-Ampt Plugin Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Plugin Structure", check_plugin_structure),
        ("Metadata", check_metadata),
        ("Green-Ampt Estimation", check_green_ampt_estimation),
        ("Dependencies", check_dependencies),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error during {name} check: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All checks passed! Plugin is ready to use.")
        return 0
    else:
        print("⚠ Some checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
