<!-- source: tests/test_cli.py idx:0 lines:766 -->

```py
"""
Comprehensive test suite for RedForge CLI
Reference: cid-roadmap-v1 Sprint S-1

Tests cover:
- CLI commands and interfaces
- Core modules and functionality
- Data models and validation
- Attack pack system
- Configuration management
- Report generation
- Error handling and edge cases
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typer.testing import CliRunner

# Import CLI and core modules
from redforge.cli import app
from redforge.core.attacks import AttackPackLoader, AttackDefinition
from redforge.core.scanner import LLMScanner
from redforge.core.report import ReportGenerator
from redforge.utils.config import Config, load_config
from redforge.models.scan_result import (
    AttackResult, ScanResult, ScanMetadata, ComplianceReport,
    SeverityLevel, AttackCategory
)


# Test fixtures
runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return Config(
        target_endpoint="https://api.example.com/v1/chat/completions",
        target_model="test-model",
        api_key="test-api-key",
        max_requests=10,
        timeout_seconds=5
    )


@pytest.fixture
def sample_attack_result():
    """Sample attack result for testing"""
    return AttackResult(
        attack_id="TEST-001",
        category=AttackCategory.PROMPT_INJECTION,
        severity=SeverityLevel.HIGH,
        description="Test prompt injection",
        prompt_used="Test prompt",
        response_received="Test response",
        is_vulnerable=True,
        confidence_score=0.85,
        risk_score=7.5,
        evidence={"test": "evidence"},
        attack_vector="test_injection",
        response_time_ms=1500,
        tokens_used=50,
        cost_usd=0.01,
        nist_controls=["GV-1.1", "MP-2.3"],
        eu_ai_act_refs=["Art.15"],
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_scan_result(sample_attack_result):
    """Sample complete scan result for testing"""
    return ScanResult(
        scan_id="test-scan-123",
        target="test-target",
        attack_pack="test-pack",
        start_time=datetime.now(),
        end_time=datetime.now(),
        results=[sample_attack_result],
        metadata=ScanMetadata(
            max_requests=10,
            timeout_seconds=30,
            attack_pack_version="1.0.0",
            total_attacks=1,
            successful_attacks=1,
            failed_attacks=0,
            vulnerabilities_found=1,
            total_duration_seconds=5.0,
            avg_response_time_ms=1500,
            cli_version="0.1.0",
            python_version="3.11.0",
            platform="linux"
        ),
        compliance=ComplianceReport(
            nist_rmf_controls_tested=["GV-1.1"],
            eu_ai_act_risk_category="high",
            audit_hash="test-hash"
        ),
        overall_risk_score=7.5,
        security_posture="fair",
        immediate_actions=["Fix prompt injection"],
        recommended_controls=["Add input validation"]
    )


# ================================
# CLI Command Tests
# ================================

class TestCLICommands:
    """Test CLI command functionality"""
    
    def test_cli_help(self):
        """Test that CLI help command works"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "RedForge CLI" in result.stdout
        assert "Developer-first LLM red-team platform" in result.stdout

    def test_version_command(self):
        """Test version command"""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout
        assert "RedForge CLI" in result.stdout

    def test_doctor_command(self):
        """Test doctor health check command"""
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "Health Check" in result.stdout
        assert "Python Version" in result.stdout

    def test_list_attacks_command(self):
        """Test list-attacks command"""
        result = runner.invoke(app, ["list-attacks"])
        assert result.exit_code == 0
        assert "owasp-llm-top10" in result.stdout.lower()

    def test_list_attacks_with_pack_filter(self):
        """Test list-attacks with pack filter"""
        result = runner.invoke(app, ["list-attacks", "--pack", "owasp-llm-top10"])
        assert result.exit_code == 0

    def test_scan_help(self):
        """Test scan command help"""
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
        assert "target" in result.stdout.lower()
        assert "attack-pack" in result.stdout.lower()

    def test_scan_dry_run(self):
        """Test scan with dry-run mode"""
        result = runner.invoke(app, [
            "scan", "test-target",
            "--dry-run",
            "--max-requests", "3"
        ])
        # Should succeed even without API key in dry-run
        assert result.exit_code == 0 or "API key" in result.stdout

    def test_scan_invalid_target(self):
        """Test scan with invalid parameters"""
        result = runner.invoke(app, [
            "scan", "",  # Empty target
            "--max-requests", "0"  # Invalid max requests
        ])
        assert result.exit_code != 0


# ================================
# Attack Pack System Tests
# ================================

class TestAttackPackSystem:
    """Test attack pack loading and management"""
    
    def test_attack_pack_loader_initialization(self):
        """Test AttackPackLoader initialization"""
        loader = AttackPackLoader()
        assert loader is not None

    def test_list_available_packs(self):
        """Test listing available attack packs"""
        loader = AttackPackLoader()
        packs = loader.list_packs()
        assert isinstance(packs, list)
        assert "owasp-llm-top10" in packs

    def test_load_owasp_pack(self):
        """Test loading OWASP LLM Top 10 pack"""
        loader = AttackPackLoader()
        attacks = loader.load_pack("owasp-llm-top10")
        
        assert len(attacks) > 0
        assert len(attacks) >= 20  # Should have at least 20 attacks
        
        # Check for specific OWASP categories
        attack_ids = [attack.id for attack in attacks]
        assert any("LLM01" in attack_id for attack_id in attack_ids)
        assert any("LLM06" in attack_id for attack_id in attack_ids)
        assert any("LLM10" in attack_id for attack_id in attack_ids)

    def test_attack_definition_structure(self):
        """Test AttackDefinition data structure"""
        loader = AttackPackLoader()
        attacks = loader.load_pack("owasp-llm-top10")
        
        for attack in attacks[:3]:  # Test first 3 attacks
            assert isinstance(attack, AttackDefinition)
            assert attack.id
            assert attack.category in AttackCategory
            assert attack.severity in SeverityLevel
            assert attack.description
            assert attack.payload
            assert attack.attack_vector
            assert isinstance(attack.nist_controls, list)
            assert isinstance(attack.eu_ai_act_refs, list)

    def test_attack_categories_coverage(self):
        """Test that all OWASP LLM categories are covered"""
        loader = AttackPackLoader()
        attacks = loader.load_pack("owasp-llm-top10")
        
        categories = {attack.category for attack in attacks}
        
        # Should cover major OWASP categories
        expected_categories = {
            AttackCategory.PROMPT_INJECTION,
            AttackCategory.SENSITIVE_INFO_DISCLOSURE,
            AttackCategory.INSECURE_OUTPUT,
            AttackCategory.MODEL_DOS
        }
        
        assert expected_categories.issubset(categories)

    def test_load_nonexistent_pack(self):
        """Test loading non-existent attack pack"""
        loader = AttackPackLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_pack("nonexistent-pack")


# ================================
# Configuration Management Tests
# ================================

class TestConfigurationManagement:
    """Test configuration loading and validation"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.target_model == "gpt-3.5-turbo"
        assert config.max_requests == 100
        assert config.timeout_seconds == 30
        assert config.default_attack_pack == "owasp-llm-top10"
        assert config.nist_rmf_enabled is True

    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = Config(max_requests=50, timeout_seconds=10)
        assert config.max_requests == 50
        
        # Invalid config should raise validation error
        with pytest.raises(ValueError):
            Config(max_requests=0)  # Should fail validation
        
        with pytest.raises(ValueError):
            Config(timeout_seconds=-1)  # Should fail validation

    def test_config_from_environment(self, monkeypatch):
        """Test loading config from environment variables"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("REDFORGE_MAX_REQUESTS", "50")
        monkeypatch.setenv("REDFORGE_TIMEOUT", "15")
        
        config = load_config()
        
        assert config.api_key == "test-key"
        assert config.max_requests == 50
        assert config.timeout_seconds == 15

    def test_config_from_yaml_file(self, temp_dir):
        """Test loading config from YAML file"""
        config_file = temp_dir / "test_config.yaml"
        config_data = {
            "target_model": "test-model",
            "max_requests": 25,
            "output_formats": ["json", "html"]
        }
        
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        assert config.target_model == "test-model"
        assert config.max_requests == 25
        assert "json" in config.output_formats
        assert "html" in config.output_formats


# ================================
# Data Model Tests
# ================================

class TestDataModels:
    """Test Pydantic data models"""
    
    def test_attack_result_creation(self, sample_attack_result):
        """Test AttackResult model creation and validation"""
        result = sample_attack_result
        
        assert result.attack_id == "TEST-001"
        assert result.category == AttackCategory.PROMPT_INJECTION
        assert result.severity == SeverityLevel.HIGH
        assert result.is_vulnerable is True
        assert 0.0 <= result.confidence_score <= 1.0
        assert 0.0 <= result.risk_score <= 10.0

    def test_attack_result_validation(self):
        """Test AttackResult validation rules"""
        # Test confidence score validation
        with pytest.raises(ValueError):
            AttackResult(
                attack_id="TEST",
                category=AttackCategory.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="Test",
                prompt_used="Test",
                response_received="Test",
                is_vulnerable=False,
                confidence_score=1.5,  # Invalid: > 1.0
                risk_score=5.0,
                evidence={},
                attack_vector="test",
                response_time_ms=100,
                nist_controls=[],
                eu_ai_act_refs=[],
                timestamp=datetime.now()
            )

    def test_scan_result_properties(self, sample_scan_result):
        """Test ScanResult computed properties"""
        scan = sample_scan_result
        
        assert scan.vulnerability_count == 1
        assert scan.duration_seconds > 0
        assert len(scan.critical_vulnerabilities) == 0  # Sample is HIGH, not CRITICAL

    def test_scan_result_serialization(self, sample_scan_result):
        """Test ScanResult JSON serialization"""
        scan = sample_scan_result
        
        # Should be able to export schema
        schema = scan.to_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_severity_and_category_enums(self):
        """Test enum values for severity and category"""
        # Test all severity levels
        severities = [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
            SeverityLevel.LOW,
            SeverityLevel.INFO
        ]
        assert len(severities) == 5
        
        # Test major attack categories
        categories = [
            AttackCategory.PROMPT_INJECTION,
            AttackCategory.SENSITIVE_INFO_DISCLOSURE,
            AttackCategory.INSECURE_OUTPUT,
            AttackCategory.MODEL_DOS
        ]
        assert len(categories) == 4


# ================================
# Scanner Module Tests
# ================================

class TestScannerModule:
    """Test LLM scanner functionality"""
    
    def test_scanner_initialization(self, sample_config):
        """Test LLMScanner initialization"""
        scanner = LLMScanner(
            target="https://api.example.com/test",
            config=sample_config,
            max_requests=10,
            timeout=5
        )
        
        assert scanner.target == "https://api.example.com/test"
        assert scanner.max_requests == 10
        assert scanner.timeout == 5
        assert scanner.requests_made == 0

    def test_api_format_detection(self, sample_config):
        """Test API format detection"""
        # OpenAI detection
        scanner_openai = LLMScanner(
            target="https://api.openai.com/v1/chat/completions",
            config=sample_config
        )
        assert scanner_openai._detect_api_format() == "openai"
        
        # Anthropic detection
        scanner_anthropic = LLMScanner(
            target="https://api.anthropic.com/v1/messages",
            config=sample_config
        )
        assert scanner_anthropic._detect_api_format() == "anthropic"
        
        # Generic detection
        scanner_generic = LLMScanner(
            target="https://api.example.com/llm",
            config=sample_config
        )
        assert scanner_generic._detect_api_format() == "generic"

    def test_payload_creation(self, sample_config):
        """Test API payload creation for different formats"""
        scanner = LLMScanner(
            target="https://api.openai.com/test",
            config=sample_config
        )
        
        # OpenAI payload
        openai_payload = scanner._create_openai_payload("test prompt")
        assert openai_payload["model"]
        assert openai_payload["messages"][0]["content"] == "test prompt"
        
        # Anthropic payload
        anthropic_payload = scanner._create_anthropic_payload("test prompt")
        assert anthropic_payload["model"]
        assert anthropic_payload["messages"][0]["content"] == "test prompt"

    @pytest.mark.asyncio
    async def test_scanner_mock_request(self, sample_config):
        """Test scanner with mocked HTTP requests"""
        scanner = LLMScanner(
            target="https://api.example.com/test",
            config=sample_config
        )
        
        # Mock HTTP response
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 50}
        }
        
        with patch.object(scanner, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                **mock_response,
                "_redforge_meta": {"response_time_ms": 1000, "status_code": 200}
            }
            
            # Create test attack
            attack = AttackDefinition(
                id="TEST-001",
                category=AttackCategory.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="Test attack",
                payload="test prompt",
                attack_vector="test",
                nist_controls=[],
                eu_ai_act_refs=[],
                references=[]
            )
            
            result = await scanner.run_attack(attack)
            
            assert result.attack_id == "TEST-001"
            assert result.response_received == "Test response"
            assert result.tokens_used == 50


# ================================
# Report Generation Tests
# ================================

class TestReportGeneration:
    """Test report generation functionality"""
    
    def test_report_generator_initialization(self, temp_dir):
        """Test ReportGenerator initialization"""
        generator = ReportGenerator(temp_dir)
        assert generator.output_dir == temp_dir
        assert temp_dir.exists()

    def test_json_report_generation(self, temp_dir, sample_scan_result):
        """Test JSON report generation"""
        generator = ReportGenerator(temp_dir)
        
        json_path = generator.generate_json(sample_scan_result)
        
        assert json_path.exists()
        assert json_path.suffix == ".json"
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert data["scan_id"] == sample_scan_result.scan_id
        assert data["target"] == sample_scan_result.target
        assert data["overall_risk_score"] == sample_scan_result.overall_risk_score
        assert len(data["results"]) == len(sample_scan_result.results)

    def test_html_report_generation(self, temp_dir, sample_scan_result):
        """Test HTML report generation"""
        generator = ReportGenerator(temp_dir)
        
        html_path = generator.generate_html(sample_scan_result)
        
        assert html_path.exists()
        assert html_path.suffix == ".html"
        
        # Verify HTML content contains key elements
        with open(html_path, 'r') as f:
            content = f.read()
        
        assert "RedForge Security Report" in content
        assert sample_scan_result.target in content
        assert str(sample_scan_result.overall_risk_score) in content

    def test_pdf_report_generation(self, temp_dir, sample_scan_result):
        """Test PDF report generation (text-based MVP)"""
        generator = ReportGenerator(temp_dir)
        
        pdf_path = generator.generate_pdf(sample_scan_result)
        
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        
        # Verify content (text-based for now)
        with open(pdf_path, 'r') as f:
            content = f.read()
        
        assert "REDFORGE SECURITY SCAN REPORT" in content
        assert sample_scan_result.target in content

    def test_vulnerability_grouping(self, temp_dir):
        """Test vulnerability grouping by severity"""
        generator = ReportGenerator(temp_dir)
        
        # Create mixed severity results
        results = [
            AttackResult(
                attack_id=f"TEST-{i}",
                category=AttackCategory.PROMPT_INJECTION,
                severity=severity,
                description=f"Test {severity.value}",
                prompt_used="test",
                response_received="test",
                is_vulnerable=True,
                confidence_score=0.8,
                risk_score=5.0,
                evidence={},
                attack_vector="test",
                response_time_ms=100,
                nist_controls=[],
                eu_ai_act_refs=[],
                timestamp=datetime.now()
            )
            for i, severity in enumerate([
                SeverityLevel.CRITICAL,
                SeverityLevel.HIGH,
                SeverityLevel.MEDIUM
            ])
        ]
        
        grouped = generator._group_by_severity(results)
        
        assert len(grouped["critical"]) == 1
        assert len(grouped["high"]) == 1
        assert len(grouped["medium"]) == 1
        assert len(grouped["low"]) == 0


# ================================
# Integration Tests
# ================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_full_cli_workflow_dry_run(self):
        """Test complete CLI workflow in dry-run mode"""
        result = runner.invoke(app, [
            "scan", "test-target",
            "--dry-run",
            "--max-requests", "5",
            "--attack-pack", "owasp-llm-top10",
            "--format", "json"
        ])
        
        # Should complete successfully in dry-run
        assert result.exit_code == 0

    def test_attack_pack_to_cli_integration(self):
        """Test integration between attack pack loading and CLI"""
        # First, verify attack pack loads correctly
        loader = AttackPackLoader()
        attacks = loader.load_pack("owasp-llm-top10")
        assert len(attacks) > 0
        
        # Then verify CLI can list them
        result = runner.invoke(app, ["list-attacks"])
        assert result.exit_code == 0
        
        # Check that some attack IDs appear in output
        for attack in attacks[:3]:
            # Attack IDs might be formatted differently in CLI output
            assert attack.category.value in result.stdout.lower()

    def test_config_to_scanner_integration(self, sample_config):
        """Test integration between config and scanner"""
        scanner = LLMScanner(
            target="https://api.example.com",
            config=sample_config,
            max_requests=sample_config.max_requests,
            timeout=sample_config.timeout_seconds
        )
        
        assert scanner.max_requests == sample_config.max_requests
        assert scanner.timeout == sample_config.timeout_seconds
        assert scanner.api_key == sample_config.api_key


# ================================
# Error Handling Tests
# ================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_api_key_handling(self):
        """Test handling of missing API key"""
        result = runner.invoke(app, [
            "scan", "gpt-4",
            "--max-requests", "1"
        ])
        
        # Should either succeed (if API key present) or fail gracefully
        if result.exit_code != 0:
            assert "API key" in result.stdout or "authentication" in result.stdout.lower()

    def test_invalid_target_handling(self):
        """Test handling of invalid target URLs"""
        result = runner.invoke(app, [
            "scan", "invalid-url-format",
            "--max-requests", "1",
            "--dry-run"
        ])
        
        # Should handle gracefully
        assert result.exit_code in [0, 1]  # Either succeeds or fails gracefully

    def test_network_error_simulation(self, sample_config):
        """Test handling of network errors"""
        scanner = LLMScanner(
            target="https://nonexistent.example.com",
            config=sample_config
        )
        
        # Network errors should be handled gracefully
        # (This test might need modification based on actual error handling)

    def test_malformed_config_handling(self, temp_dir):
        """Test handling of malformed configuration files"""
        config_file = temp_dir / "bad_config.yaml"
        
        # Create malformed YAML
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        # Should handle gracefully or provide clear error
        try:
            config = load_config(config_file)
            # If it loads, should have default values
            assert config.max_requests > 0
        except Exception as e:
            # If it fails, should be a clear error
            assert "yaml" in str(e).lower() or "config" in str(e).lower()


# ================================
# Performance Tests
# ================================

class TestPerformance:
    """Basic performance and resource usage tests"""
    
    def test_attack_pack_loading_performance(self):
        """Test attack pack loading performance"""
        import time
        
        loader = AttackPackLoader()
        
        start_time = time.time()
        attacks = loader.load_pack("owasp-llm-top10")
        end_time = time.time()
        
        # Should load quickly (under 1 second)
        assert end_time - start_time < 1.0
        assert len(attacks) > 0

    def test_config_loading_performance(self):
        """Test configuration loading performance"""
        import time
        
        start_time = time.time()
        config = Config()
        end_time = time.time()
        
        # Should be nearly instantaneous
        assert end_time - start_time < 0.1

    def test_cli_startup_performance(self):
        """Test CLI startup performance"""
        import time
        
        start_time = time.time()
        result = runner.invoke(app, ["--help"])
        end_time = time.time()
        
        # CLI should start quickly
        assert result.exit_code == 0
        assert end_time - start_time < 3.0  # Allow 3 seconds for import overhead


# ================================
# Test Runner Configuration
# ================================

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
```