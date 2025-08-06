#!/usr/bin/env python3
"""
Test script for optional authentication functionality.
This script tests the key features of the optional authentication system.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_boolean_parsing():
    """Test the boolean environment variable parsing."""
    print("🧪 Testing boolean environment variable parsing...")
    
    # Import the function
    from app.core.config import _parse_bool_env
    
    # Test cases
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("YES", True),
        ("on", True),
        ("ON", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("NO", False),
        ("off", False),
        ("OFF", False),
        ("invalid", False),
        ("", False),
        ("  true  ", True),  # Test whitespace handling
    ]
    
    for value, expected in test_cases:
        # Set environment variable
        os.environ["TEST_BOOL"] = value
        result = _parse_bool_env("TEST_BOOL")
        
        if result == expected:
            print(f"  ✅ '{value}' -> {result} (expected {expected})")
        else:
            print(f"  ❌ '{value}' -> {result} (expected {expected})")
            return False
    
    # Clean up
    if "TEST_BOOL" in os.environ:
        del os.environ["TEST_BOOL"]
    
    print("  ✅ All boolean parsing tests passed!")
    return True

def test_config_endpoint_response():
    """Test the auth config endpoint response format."""
    print("\n🧪 Testing auth config endpoint response format...")
    
    try:
        from app.api.auth import get_auth_config
        from app.core.config import settings
        
        # Mock the settings for testing
        original_enable_auth = getattr(settings, 'ENABLE_AUTH', False)
        original_allow_registration = getattr(settings, 'ALLOW_REGISTRATION', False)
        
        # Test with auth disabled
        settings.ENABLE_AUTH = False
        settings.ALLOW_REGISTRATION = False
        
        import asyncio
        response = asyncio.run(get_auth_config())
        
        expected = {
            "auth_enabled": False,
            "registration_enabled": False
        }
        
        if response == expected:
            print("  ✅ Auth disabled response correct")
        else:
            print(f"  ❌ Auth disabled response incorrect: {response}")
            return False
        
        # Test with auth enabled
        settings.ENABLE_AUTH = True
        settings.ALLOW_REGISTRATION = True
        
        response = asyncio.run(get_auth_config())
        
        expected = {
            "auth_enabled": True,
            "registration_enabled": True
        }
        
        if response == expected:
            print("  ✅ Auth enabled response correct")
        else:
            print(f"  ❌ Auth enabled response incorrect: {response}")
            return False
        
        # Restore original settings
        settings.ENABLE_AUTH = original_enable_auth
        settings.ALLOW_REGISTRATION = original_allow_registration
        
        print("  ✅ All config endpoint tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Config endpoint test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable configuration."""
    print("\n🧪 Testing environment variable configuration...")
    
    # Test default values
    original_env = {}
    env_vars = ["ENABLE_AUTH", "ALLOW_REGISTRATION", "DEFAULT_USER_ID"]
    
    # Save original environment
    for var in env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # Reload settings to get defaults
        import importlib
        from app.core import config
        importlib.reload(config)
        
        settings = config.settings
        
        # Test defaults
        if not settings.ENABLE_AUTH:
            print("  ✅ ENABLE_AUTH defaults to False")
        else:
            print("  ❌ ENABLE_AUTH should default to False")
            return False
        
        if not settings.ALLOW_REGISTRATION:
            print("  ✅ ALLOW_REGISTRATION defaults to False")
        else:
            print("  ❌ ALLOW_REGISTRATION should default to False")
            return False
        
        if settings.DEFAULT_USER_ID == 1:
            print("  ✅ DEFAULT_USER_ID defaults to 1")
        else:
            print("  ❌ DEFAULT_USER_ID should default to 1")
            return False
        
        # Test setting environment variables
        os.environ["ENABLE_AUTH"] = "true"
        os.environ["ALLOW_REGISTRATION"] = "yes"
        os.environ["DEFAULT_USER_ID"] = "42"
        
        # Reload settings
        importlib.reload(config)
        settings = config.settings
        
        if settings.ENABLE_AUTH:
            print("  ✅ ENABLE_AUTH=true works")
        else:
            print("  ❌ ENABLE_AUTH=true not working")
            return False
        
        if settings.ALLOW_REGISTRATION:
            print("  ✅ ALLOW_REGISTRATION=yes works")
        else:
            print("  ❌ ALLOW_REGISTRATION=yes not working")
            return False
        
        if settings.DEFAULT_USER_ID == 42:
            print("  ✅ DEFAULT_USER_ID=42 works")
        else:
            print("  ❌ DEFAULT_USER_ID=42 not working")
            return False
        
        print("  ✅ All environment variable tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Environment variable test failed: {e}")
        return False
    
    finally:
        # Restore original environment
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
        for var, value in original_env.items():
            os.environ[var] = value

def main():
    """Run all tests."""
    print("🚀 Testing Optional Authentication System")
    print("=" * 50)
    
    tests = [
        test_boolean_parsing,
        test_config_endpoint_response,
        test_environment_variables,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Optional authentication is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
