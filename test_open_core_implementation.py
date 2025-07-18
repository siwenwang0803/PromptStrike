#!/usr/bin/env python3
"""
Test RedForge Open-Core Implementation
Comprehensive testing of all new features
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Check OpenAI API key for testing
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Please set OPENAI_API_KEY environment variable for testing")
    sys.exit(1)

def run_command(cmd, expect_success=True, timeout=60):
    """Run a command and return result"""
    print(f"📋 Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        if expect_success and result.returncode != 0:
            print(f"❌ Command failed: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after {timeout}s")
        return False, "Timeout"
    except Exception as e:
        print(f"💥 Command error: {e}")
        return False, str(e)

def test_cli_installation():
    """Test if CLI is properly installed"""
    print("\n" + "="*60)
    print("🔧 Testing CLI Installation")
    print("="*60)
    
    # Test if redforge command exists
    success, output = run_command("python3 -m redforge.cli --help")
    if success:
        print("✅ CLI is accessible via python -m redforge.cli")
    else:
        print("❌ CLI not accessible")
        return False
    
    # Test version
    success, output = run_command("python3 -m redforge.cli version")
    if success:
        print(f"✅ CLI version: {output.strip()}")
    else:
        print("⚠️  Version command not available")
    
    return True

def test_offline_mode():
    """Test offline mode (free tier)"""
    print("\n" + "="*60)
    print("🔓 Testing Offline Mode (Free Tier)")
    print("="*60)
    
    # Create temp directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test offline scan
        cmd = f"python3 -m redforge.cli scan gpt-3.5-turbo --offline --output {temp_dir}"
        success, output = run_command(cmd, timeout=120)
        
        if success:
            print("✅ Offline scan completed successfully")
            
            # Check if report was generated
            report_files = list(Path(temp_dir).glob("*.json"))
            if report_files:
                print(f"✅ Report generated: {report_files[0].name}")
                
                # Check report content
                with open(report_files[0], 'r') as f:
                    report = json.load(f)
                
                if "watermark" in report:
                    print("✅ Watermark present in free report")
                else:
                    print("⚠️  Watermark missing in free report")
                
                if "tier" in report and report["tier"] == "free":
                    print("✅ Tier correctly set to 'free'")
                else:
                    print("⚠️  Tier not set correctly")
                    
            else:
                print("❌ No report file generated")
                return False
        else:
            print(f"❌ Offline scan failed: {output}")
            return False
    
    return True

def test_cloud_mode_without_key():
    """Test cloud mode behavior without API key"""
    print("\n" + "="*60)
    print("🔑 Testing Cloud Mode (No API Key)")
    print("="*60)
    
    # Remove any existing API key
    if "REDFORGE_API_KEY" in os.environ:
        del os.environ["REDFORGE_API_KEY"]
    
    # Test cloud scan without key
    cmd = "python3 -m redforge.cli scan gpt-3.5-turbo"
    success, output = run_command(cmd, expect_success=False)
    
    if not success and "API key required" in output:
        print("✅ Correctly requires API key for cloud mode")
    else:
        print("❌ Should require API key for cloud mode")
        return False
    
    return True

def test_status_command():
    """Test status command"""
    print("\n" + "="*60)
    print("📊 Testing Status Command")
    print("="*60)
    
    success, output = run_command("python3 -m redforge.cli status")
    if success:
        print("✅ Status command works")
        print(f"Status output:\n{output}")
    else:
        print(f"❌ Status command failed: {output}")
        return False
    
    return True

def test_signup_command():
    """Test signup command"""
    print("\n" + "="*60)
    print("📝 Testing Signup Command")
    print("="*60)
    
    test_email = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}@redforge.ai"
    cmd = f"python3 -m redforge.cli signup {test_email} --name 'Test User'"
    
    success, output = run_command(cmd)
    if success:
        print("✅ Signup command works")
        print(f"Signup output:\n{output}")
    else:
        print(f"❌ Signup command failed: {output}")
        return False
    
    return True

def test_list_attacks_command():
    """Test list-attacks command"""
    print("\n" + "="*60)
    print("📋 Testing List Attacks Command")
    print("="*60)
    
    success, output = run_command("python3 -m redforge.cli list-attacks")
    if success:
        print("✅ List attacks command works")
        print(f"First 10 lines:\n" + "\n".join(output.split("\n")[:10]))
    else:
        print(f"❌ List attacks command failed: {output}")
        return False
    
    return True

def test_cloud_client_import():
    """Test cloud client import"""
    print("\n" + "="*60)
    print("🌐 Testing Cloud Client Import")
    print("="*60)
    
    try:
        from redforge.cloud_client import CloudClient, run_offline_scan, show_upgrade_message
        print("✅ Cloud client imports successfully")
        
        # Test CloudClient initialization
        client = CloudClient()
        print("✅ CloudClient can be instantiated")
        
        # Test offline scan function exists
        print("✅ run_offline_scan function available")
        
        # Test upgrade message
        print("✅ show_upgrade_message function available")
        
    except ImportError as e:
        print(f"❌ Cloud client import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Cloud client error: {e}")
        return False
    
    return True

def test_legacy_local_mode():
    """Test legacy local mode still works"""
    print("\n" + "="*60)
    print("🏠 Testing Legacy Local Mode")
    print("="*60)
    
    # Test dry run (should work without cloud key)
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = f"python3 -m redforge.cli scan gpt-3.5-turbo --dry-run --output {temp_dir}"
        success, output = run_command(cmd, timeout=60)
        
        if success:
            print("✅ Legacy dry-run mode works")
            
            # Check if report was generated
            report_files = list(Path(temp_dir).glob("*.json"))
            if report_files:
                print(f"✅ Dry-run report generated: {report_files[0].name}")
            else:
                print("⚠️  No dry-run report generated")
                
        else:
            print(f"❌ Legacy dry-run failed: {output}")
            return False
    
    return True

def test_help_messages():
    """Test help messages show new options"""
    print("\n" + "="*60)
    print("❓ Testing Help Messages")
    print("="*60)
    
    # Test main help
    success, output = run_command("python3 -m redforge.cli --help")
    if success:
        if "status" in output and "signup" in output:
            print("✅ New commands appear in main help")
        else:
            print("⚠️  New commands missing from main help")
    else:
        print("❌ Main help failed")
        return False
    
    # Test scan help
    success, output = run_command("python3 -m redforge.cli scan --help")
    if success:
        if "--cloud-api-key" in output and "--offline" in output:
            print("✅ New scan options appear in scan help")
        else:
            print("⚠️  New scan options missing from scan help")
    else:
        print("❌ Scan help failed")
        return False
    
    return True

def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("🚨 Testing Error Handling")
    print("="*60)
    
    # Test invalid target
    success, output = run_command("python3 -m redforge.cli scan invalid-model --offline", expect_success=False)
    if not success:
        print("✅ Correctly handles invalid target")
    else:
        print("⚠️  Should handle invalid target better")
    
    # Test invalid cloud key format
    cmd = "python3 -m redforge.cli scan gpt-3.5-turbo --cloud-api-key invalid-key"
    success, output = run_command(cmd, expect_success=False)
    if not success:
        print("✅ Correctly handles invalid cloud key")
    else:
        print("⚠️  Should handle invalid cloud key better")
    
    return True

def test_file_permissions():
    """Test file permissions and directories"""
    print("\n" + "="*60)
    print("📁 Testing File Permissions")
    print("="*60)
    
    # Test if .redforge directory can be created
    try:
        config_dir = Path.home() / ".redforge"
        config_dir.mkdir(exist_ok=True)
        print("✅ Can create .redforge directory")
        
        # Test if config file can be written
        config_file = config_dir / "test_config.json"
        config_file.write_text('{"test": true}')
        print("✅ Can write to .redforge directory")
        
        # Clean up
        config_file.unlink()
        
    except Exception as e:
        print(f"❌ File permission error: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🔥 RedForge Open-Core Implementation Test Suite")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print("=" * 60)
    
    tests = [
        ("CLI Installation", test_cli_installation),
        ("Offline Mode", test_offline_mode),
        ("Cloud Mode (No Key)", test_cloud_mode_without_key),
        ("Status Command", test_status_command),
        ("Signup Command", test_signup_command),
        ("List Attacks Command", test_list_attacks_command),
        ("Cloud Client Import", test_cloud_client_import),
        ("Legacy Local Mode", test_legacy_local_mode),
        ("Help Messages", test_help_messages),
        ("Error Handling", test_error_handling),
        ("File Permissions", test_file_permissions),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Open-Core implementation is working correctly!")
        print("🚀 Ready for Product Hunt launch!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review and fix before launch.")
    
    print(f"\n⏰ Completed at: {datetime.now()}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)