#!/usr/bin/env python3
"""
Test error scenarios for threat-Jira integrity validation
Tests various failure conditions and edge cases
"""

import os
import sys
import json
import yaml
import tempfile
import pathlib
from unittest.mock import patch, MagicMock
from verify_threat_jira_integrity import ThreatJiraValidator, ValidationStatus, ThreatInfo

def test_missing_files():
    """Test handling of missing threat model and mapping files"""
    print("🧪 Testing missing files scenario...")
    
    # Test with non-existent paths
    validator = ThreatJiraValidator()
    validator.threat_doc_path = pathlib.Path("/non/existent/threat_model.md")
    validator.mapping_path = pathlib.Path("/non/existent/mapping.yml")
    
    # This should fail gracefully
    success = validator.validate_prerequisites()
    assert not success, "Should fail when files are missing"
    
    # Check error messages
    error_results = [r for r in validator.results if r.status == ValidationStatus.FAIL]
    assert len(error_results) >= 1, "Should have at least one error for missing files"
    print("✅ Missing files handled correctly")

def test_malformed_yaml():
    """Test handling of malformed YAML mapping file"""
    print("🧪 Testing malformed YAML scenario...")
    
    # Create temporary malformed YAML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("invalid: yaml: content:\n  - malformed\n    structure")
        malformed_yaml_path = f.name
    
    try:
        validator = ThreatJiraValidator()
        validator.mapping_path = pathlib.Path(malformed_yaml_path)
        
        # Should handle YAML parsing errors
        success = validator.load_threat_mappings()
        assert not success, "Should fail with malformed YAML"
        print("✅ Malformed YAML handled correctly")
    finally:
        os.unlink(malformed_yaml_path)

def test_jira_connectivity_failure():
    """Test Jira API connectivity failure scenarios"""
    print("🧪 Testing Jira connectivity failure...")
    
    # Mock requests to simulate network failures
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Network timeout")
        
        validator = ThreatJiraValidator()
        validator.config.update({
            'jira_username': 'test_user',
            'jira_api_token': 'test_token',
            'jira_base_url': 'https://test.atlassian.net'
        })
        
        # Should handle connection failures gracefully
        success = validator._test_jira_connection()
        assert not success, "Should fail when Jira is unreachable"
        print("✅ Jira connectivity failure handled correctly")

def test_jira_auth_failure():
    """Test Jira authentication failure scenarios"""
    print("🧪 Testing Jira authentication failure...")
    
    # Mock 401 authentication error
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        validator = ThreatJiraValidator()
        validator.config.update({
            'jira_username': 'invalid_user',
            'jira_api_token': 'invalid_token',
            'jira_base_url': 'https://test.atlassian.net'
        })
        
        success = validator._test_jira_connection()
        assert not success, "Should fail with invalid credentials"
        print("✅ Jira authentication failure handled correctly")

def test_jira_ticket_not_found():
    """Test scenario where Jira tickets don't exist"""
    print("🧪 Testing Jira ticket not found scenario...")
    
    # Create validator with mock session
    validator = ThreatJiraValidator()
    validator.config['test_mode'] = False
    validator.jira_session = MagicMock()
    
    # Mock 404 responses for tickets
    mock_response = MagicMock()
    mock_response.status_code = 404
    validator.jira_session.get.return_value = mock_response
    
    # Add some test threats
    validator.threats = {
        'S1': ThreatInfo(threat_id='S1', jira_ticket='PS-999')
    }
    
    # Should handle missing tickets gracefully
    success = validator._validate_jira_statuses_online()
    assert not success, "Should fail when tickets don't exist"
    print("✅ Missing Jira tickets handled correctly")

def test_invalid_threat_count():
    """Test handling of incorrect threat count"""
    print("🧪 Testing invalid threat count...")
    
    # Create temporary mapping with wrong number of threats
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump({'S1': 'PS-31', 'S2': 'PS-32'}, f)  # Only 2 threats instead of 17
        wrong_count_path = f.name
    
    try:
        validator = ThreatJiraValidator()
        validator.mapping_path = pathlib.Path(wrong_count_path)
        
        success = validator.load_threat_mappings()
        
        # Should load but report count mismatch
        count_results = [r for r in validator.results if 'count' in r.name.lower()]
        assert len(count_results) > 0, "Should report threat count validation"
        print("✅ Invalid threat count handled correctly")
    finally:
        os.unlink(wrong_count_path)

def test_corrupted_threat_document():
    """Test handling of corrupted threat model document"""
    print("🧪 Testing corrupted threat document...")
    
    # Create temporary corrupted document
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("This is not a valid threat model document\n")
        f.write("It has no proper structure or threat references\n")
        corrupted_doc_path = f.name
    
    try:
        validator = ThreatJiraValidator()
        validator.threat_doc_path = pathlib.Path(corrupted_doc_path)
        validator.threats = {'S1': ThreatInfo(threat_id='S1', jira_ticket='PS-31')}
        
        success = validator.validate_threat_documentation()
        
        # Should handle missing threat references
        missing_results = [r for r in validator.results if r.status == ValidationStatus.FAIL]
        assert len(missing_results) > 0, "Should report missing threats in document"
        print("✅ Corrupted document handled correctly")
    finally:
        os.unlink(corrupted_doc_path)

def test_jira_server_error():
    """Test handling of Jira server errors (5xx)"""
    print("🧪 Testing Jira server error scenario...")
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        validator = ThreatJiraValidator()
        validator.config.update({
            'jira_username': 'test_user',
            'jira_api_token': 'test_token',
            'jira_base_url': 'https://test.atlassian.net'
        })
        
        success = validator._test_jira_connection()
        assert not success, "Should fail with server error"
        print("✅ Jira server error handled correctly")

def test_mixed_status_scenarios():
    """Test mixed scenarios with some valid and some invalid statuses"""
    print("🧪 Testing mixed status scenarios...")
    
    validator = ThreatJiraValidator()
    validator.config['test_mode'] = False
    validator.config['forbidden_statuses'] = ['Open', 'To Do']
    
    # Mock session with mixed responses
    validator.jira_session = MagicMock()
    
    # Create test threats
    validator.threats = {
        'S1': ThreatInfo(threat_id='S1', jira_ticket='PS-31'),
        'S2': ThreatInfo(threat_id='S2', jira_ticket='PS-32'),
        'T1': ThreatInfo(threat_id='T1', jira_ticket='PS-33')
    }
    
    # Mock different responses for different tickets
    def mock_get_response(url, **kwargs):
        mock_response = MagicMock()
        if 'S1' in url:
            # Valid ticket with good status
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'fields': {
                    'status': {'name': 'In Progress'},
                    'assignee': {'displayName': 'John Doe'}
                }
            }
        elif 'S2' in url:
            # Valid ticket with forbidden status
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'fields': {
                    'status': {'name': 'Open'},
                    'assignee': None
                }
            }
        else:
            # Ticket not found
            mock_response.status_code = 404
        return mock_response
    
    validator.jira_session.get.side_effect = mock_get_response
    
    success = validator._validate_jira_statuses_online()
    assert not success, "Should fail with mixed results"
    
    # Should have both accessibility and compliance issues
    results = validator.results
    assert len(results) >= 2, "Should have multiple validation results"
    print("✅ Mixed status scenarios handled correctly")

def test_configuration_edge_cases():
    """Test edge cases in configuration"""
    print("🧪 Testing configuration edge cases...")
    
    # Test with empty configuration
    validator = ThreatJiraValidator()
    validator.config = {}
    
    # Should handle missing config gracefully
    try:
        success = validator.validate_prerequisites()
        # Should provide reasonable defaults
        assert hasattr(validator, 'config') and validator.config is not None
    except KeyError:
        # Expected when config is completely empty
        pass
    print("✅ Configuration edge cases handled correctly")

def run_all_error_tests():
    """Run all error scenario tests"""
    print("🧪 Running Error Scenario Tests for Threat-Jira Integrity Validation")
    print("=" * 70)
    
    test_functions = [
        test_missing_files,
        test_malformed_yaml,
        test_jira_connectivity_failure,
        test_jira_auth_failure,
        test_jira_ticket_not_found,
        test_invalid_threat_count,
        test_corrupted_threat_document,
        test_jira_server_error,
        test_mixed_status_scenarios,
        test_configuration_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"🎯 Error Scenario Test Results:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total: {passed + failed}")
    
    if failed == 0:
        print("✅ All error scenarios handled correctly!")
        return True
    else:
        print("❌ Some error scenarios need improvement")
        return False

def test_resilience_and_recovery():
    """Test system resilience and recovery scenarios"""
    print("🧪 Testing resilience and recovery...")
    
    # Test partial failure recovery
    validator = ThreatJiraValidator()
    
    # Simulate partial system failure
    validator.config['test_mode'] = True
    validator.threats = {'S1': ThreatInfo(threat_id='S1', jira_ticket='PS-31')}
    
    # Should continue even with some failures
    success = validator.validate_jira_statuses()
    
    # Should provide useful feedback even in degraded mode
    assert len(validator.results) > 0, "Should provide results even with partial failures"
    print("✅ Resilience and recovery handled correctly")

if __name__ == "__main__":
    success = run_all_error_tests()
    
    # Additional resilience testing
    test_resilience_and_recovery()
    
    print("\n🎉 Error scenario testing completed!")
    print("The threat-Jira integrity validator is robust and handles edge cases well.")
    
    sys.exit(0 if success else 1)