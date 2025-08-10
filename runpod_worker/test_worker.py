#!/usr/bin/env python3
"""
Test script for CharForgex RunPod Worker
Validates worker functionality and performance
"""

import requests
import json
import base64
import os
import sys
import time
from typing import Dict, Any

def print_step(step: str):
    print(f"\n🔄 {step}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️ {message}")

def test_health_check(endpoint_url: str, api_key: str) -> bool:
    """Test worker health check"""
    print_step("Testing Health Check")
    
    try:
        response = requests.post(
            endpoint_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'input': {
                    'operation': 'health_check'
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'healthy':
                print_success("Health check passed")
                
                # Display system info if available
                if 'gpu_info' in result:
                    gpu_info = result['gpu_info']
                    print_info(f"GPU: {gpu_info.get('gpu_name', 'Unknown')}")
                    if 'memory_total' in gpu_info:
                        memory_gb = gpu_info['memory_total'] / (1024**3)
                        print_info(f"GPU Memory: {memory_gb:.1f}GB")
                
                if 'storage_info' in result:
                    storage = result['storage_info']
                    if 'free_gb' in storage:
                        print_info(f"Storage: {storage['free_gb']:.1f}GB free / {storage['total_gb']:.1f}GB total")
                
                return True
            else:
                print_error(f"Health check failed: {result}")
                return False
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Health check timed out (worker may be cold starting)")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False

def test_list_characters(endpoint_url: str, api_key: str) -> Dict[str, Any]:
    """Test listing characters"""
    print_step("Testing Character Listing")
    
    try:
        response = requests.post(
            endpoint_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'input': {
                    'operation': 'list_characters'
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'completed':
                characters = result.get('characters', [])
                print_success(f"Found {len(characters)} trained characters")
                
                for char in characters[:3]:  # Show first 3
                    name = char.get('name', 'Unknown')
                    size_mb = char.get('total_size_mb', 0)
                    print_info(f"  - {name} ({size_mb:.1f}MB)")
                
                if len(characters) > 3:
                    print_info(f"  ... and {len(characters) - 3} more")
                
                return result
            else:
                print_error(f"Character listing failed: {result}")
                return {}
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {}

def test_system_status(endpoint_url: str, api_key: str) -> bool:
    """Test system status endpoint"""
    print_step("Testing System Status")
    
    try:
        response = requests.post(
            endpoint_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'input': {
                    'operation': 'system_status'
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("System status retrieved")
            
            # Display detailed info
            if 'gpu_info' in result:
                gpu = result['gpu_info']
                print_info(f"GPU: {gpu.get('gpu_name', 'Unknown')}")
                print_info(f"CUDA Available: {gpu.get('cuda_available', False)}")
            
            if 'character_count' in result:
                print_info(f"Trained Characters: {result['character_count']}")
            
            if 'image_generator_loaded' in result:
                print_info(f"Image Generator: {'Loaded' if result['image_generator_loaded'] else 'Not loaded'}")
            
            return True
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False

def test_inference_with_dummy_character(endpoint_url: str, api_key: str, characters: list) -> bool:
    """Test inference if characters are available"""
    if not characters:
        print_info("No characters available for inference testing")
        return True
    
    print_step("Testing Image Generation")
    
    character_name = characters[0]['name']
    print_info(f"Using character: {character_name}")
    
    try:
        response = requests.post(
            endpoint_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'input': {
                    'operation': 'inference',
                    'character_name': character_name,
                    'prompt': f'portrait of {character_name}, detailed face',
                    'batch_size': 1,
                    'num_inference_steps': 20,  # Reduced for testing
                    'test_dim': 512  # Smaller for faster testing
                }
            },
            timeout=300  # 5 minutes
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'completed':
                num_images = result.get('num_images', 0)
                inference_time = result.get('inference_time_seconds', 0)
                print_success(f"Generated {num_images} images in {inference_time:.1f}s")
                return True
            else:
                print_error(f"Inference failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Inference timed out (this may be normal for cold starts)")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False

def main():
    """Main testing function"""
    if len(sys.argv) != 3:
        print("Usage: python test_worker.py <endpoint_url> <api_key>")
        print("Example: python test_worker.py https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync YOUR_API_KEY")
        sys.exit(1)
    
    endpoint_url = sys.argv[1]
    api_key = sys.argv[2]
    
    print("🧪 CharForgex RunPod Worker Test Suite")
    print("="*60)
    print(f"Endpoint: {endpoint_url}")
    print(f"API Key: {'*' * (len(api_key) - 8) + api_key[-8:]}")  # Mask API key
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health Check
    total_tests += 1
    if test_health_check(endpoint_url, api_key):
        tests_passed += 1
    
    # Test 2: System Status
    total_tests += 1
    if test_system_status(endpoint_url, api_key):
        tests_passed += 1
    
    # Test 3: List Characters
    total_tests += 1
    characters_result = test_list_characters(endpoint_url, api_key)
    if characters_result:
        tests_passed += 1
        
        # Test 4: Inference (if characters available)
        characters = characters_result.get('characters', [])
        if characters:
            total_tests += 1
            if test_inference_with_dummy_character(endpoint_url, api_key, characters):
                tests_passed += 1
    
    # Final summary
    print("\n" + "="*60)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print_success("All tests passed! Your RunPod worker is fully functional.")
        print("\n🎉 Ready for production use!")
        print("\n📖 Next steps:")
        print("- Use the GUI at your endpoint URL + :8000")
        print("- Try the Python client in client_example.py")
        print("- Train your first character and generate images")
    else:
        print_error("Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("- Verify your endpoint URL and API key")
        print("- Check RunPod console for worker logs")
        print("- Ensure your endpoint has proper GPU allocation")
        print("- Wait a few minutes if this is a cold start")

if __name__ == "__main__":
    main()
