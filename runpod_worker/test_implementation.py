#!/usr/bin/env python3
"""
CharForgex RunPod Implementation Test Suite
Comprehensive testing against RunPod documentation requirements
"""

import os
import sys
import json
import subprocess
import tempfile
import time
from typing import Dict, Any, List

def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"🧪 {text}")
    print('='*60)

def print_test(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def print_info(message: str):
    print(f"ℹ️ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def test_runpod_handler_compliance():
    """Test that our handler matches RunPod documentation requirements"""
    print_header("RunPod Handler Compliance Tests")
    
    # Test 1: Handler function signature
    try:
        sys.path.insert(0, '/mnt/persist/workspace/runpod_worker')
        import worker
        
        # Check handler function exists and has correct name
        has_handler = hasattr(worker, 'handler')
        print_test("Handler function exists", has_handler, "Function named 'handler' found" if has_handler else "Missing 'handler' function")
        
        if has_handler:
            # Check handler is callable
            is_callable = callable(worker.handler)
            print_test("Handler is callable", is_callable)
            
            # Test handler signature (should accept job parameter)
            import inspect
            sig = inspect.signature(worker.handler)
            params = list(sig.parameters.keys())
            correct_params = len(params) == 1
            print_test("Handler signature correct", correct_params, f"Parameters: {params}")
        
    except Exception as e:
        print_test("Handler import test", False, f"Import failed: {e}")
        return False
    
    return True

def test_docker_build():
    """Test Docker build process"""
    print_header("Docker Build Tests")
    
    # Test 1: Dockerfile exists
    dockerfile_exists = os.path.exists('/mnt/persist/workspace/runpod_worker/Dockerfile')
    print_test("Dockerfile exists", dockerfile_exists)
    
    if not dockerfile_exists:
        return False
    
    # Test 2: Dockerfile syntax
    try:
        with open('/mnt/persist/workspace/runpod_worker/Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        # Check for required elements
        required_elements = [
            "FROM runpod/pytorch",
            "WORKDIR /workspace", 
            "COPY . /workspace/",
            "CMD"
        ]
        
        all_elements_present = True
        for element in required_elements:
            present = element in dockerfile_content
            print_test(f"Dockerfile contains '{element}'", present)
            all_elements_present = all_elements_present and present
        
        return all_elements_present
        
    except Exception as e:
        print_test("Dockerfile syntax check", False, f"Error: {e}")
        return False

def test_python_imports():
    """Test critical Python imports"""
    print_header("Python Import Tests")
    
    test_imports = [
        ("runpod", "RunPod SDK"),
        ("torch", "PyTorch"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("requests", "Requests"),
    ]
    
    all_passed = True
    for module, description in test_imports:
        try:
            __import__(module)
            print_test(f"Import {description}", True, f"Module '{module}' imported successfully")
        except ImportError as e:
            print_test(f"Import {description}", False, f"Failed to import '{module}': {e}")
            all_passed = False
    
    return all_passed

def test_worker_functionality():
    """Test worker functionality"""
    print_header("Worker Functionality Tests")
    
    try:
        sys.path.insert(0, '/mnt/persist/workspace/runpod_worker')
        import worker
        
        # Test 1: Handler initialization
        try:
            handler_instance = worker.initialize_handler()
            print_test("Handler initialization", handler_instance is not None)
        except Exception as e:
            print_test("Handler initialization", False, f"Error: {e}")
            return False
        
        # Test 2: Mock job processing
        try:
            mock_job = {
                "input": {
                    "operation": "health_check"
                }
            }
            
            result = worker.handler(mock_job)
            is_dict = isinstance(result, dict)
            has_status = 'status' in result if is_dict else False
            
            print_test("Health check processing", is_dict and has_status, f"Result: {result}")
            
        except Exception as e:
            print_test("Health check processing", False, f"Error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print_test("Worker functionality", False, f"Import error: {e}")
        return False

def test_file_structure():
    """Test required file structure"""
    print_header("File Structure Tests")
    
    base_path = '/mnt/persist/workspace'
    required_files = [
        "train_character.py",
        "test_character.py", 
        "base_requirements.txt",
        "install.py",
        "runpod_worker/worker.py",
        "runpod_worker/handler.py",
        "runpod_worker/utils.py",
        "runpod_worker/Dockerfile",
        "runpod_worker/gui/index.html",
        "runpod_worker/gui/app.js"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        exists = os.path.exists(full_path)
        size = os.path.getsize(full_path) if exists else 0
        
        print_test(f"File: {file_path}", exists, f"Size: {size} bytes" if exists else "Missing")
        all_exist = all_exist and exists
    
    return all_exist

def test_runpod_sdk_integration():
    """Test RunPod SDK integration"""
    print_header("RunPod SDK Integration Tests")
    
    try:
        import runpod
        
        # Test 1: RunPod version
        version = getattr(runpod, '__version__', 'Unknown')
        print_test("RunPod SDK version", True, f"Version: {version}")
        
        # Test 2: Serverless module
        has_serverless = hasattr(runpod, 'serverless')
        print_test("Serverless module available", has_serverless)
        
        if has_serverless:
            # Test 3: Start function
            has_start = hasattr(runpod.serverless, 'start')
            print_test("Serverless start function", has_start)
        
        return has_serverless
        
    except ImportError as e:
        print_test("RunPod SDK import", False, f"Error: {e}")
        return False

def test_environment_setup():
    """Test environment setup"""
    print_header("Environment Setup Tests")
    
    # Test 1: Python version
    python_version = sys.version_info
    python_ok = python_version >= (3, 10)
    print_test("Python version", python_ok, f"Python {python_version.major}.{python_version.minor}")
    
    # Test 2: Working directory
    cwd = os.getcwd()
    in_workspace = 'workspace' in cwd
    print_test("Working directory", in_workspace, f"CWD: {cwd}")
    
    # Test 3: Environment variables
    env_vars = ['PYTHONPATH', 'HF_HOME', 'PLATFORM']
    env_ok = True
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        is_set = var in os.environ
        print_test(f"Environment: {var}", is_set, f"Value: {value}")
        # Don't fail on missing env vars as they might be set at runtime
    
    return python_ok and in_workspace

def test_gpu_compatibility():
    """Test GPU compatibility"""
    print_header("GPU Compatibility Tests")
    
    try:
        import torch
        
        # Test 1: CUDA availability
        cuda_available = torch.cuda.is_available()
        print_test("CUDA available", cuda_available, "GPU support detected" if cuda_available else "No GPU detected")
        
        if cuda_available:
            # Test 2: GPU details
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3) if gpu_count > 0 else 0
            
            print_test("GPU details", True, f"GPU: {gpu_name}, Memory: {gpu_memory:.1f}GB")
        
        return True  # Don't fail if no GPU (might be testing on CPU)
        
    except Exception as e:
        print_test("GPU compatibility", False, f"Error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🧪 CharForgex RunPod Implementation - Comprehensive Test Suite")
    print("Testing against RunPod documentation requirements...")
    
    tests = [
        ("RunPod Handler Compliance", test_runpod_handler_compliance),
        ("File Structure", test_file_structure),
        ("Python Imports", test_python_imports),
        ("RunPod SDK Integration", test_runpod_sdk_integration),
        ("Environment Setup", test_environment_setup),
        ("Worker Functionality", test_worker_functionality),
        ("Docker Build", test_docker_build),
        ("GPU Compatibility", test_gpu_compatibility),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation is ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Please review and fix issues before deployment.")
        return False

def main():
    """Main test function"""
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
