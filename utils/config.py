"""
Configuration management for PromptStrike CLI
Reference: cid-roadmap-v1 Sprint S-1
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator


class Config(BaseModel):
    """
    Configuration model for PromptStrike CLI
    """
    
    # Target configuration
    target_endpoint: Optional[str] = None
    target_model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    
    # Scan configuration
    max_requests: int = 100
    timeout_seconds: int = 30
    parallel_workers: int = 1
    rate_limit_rps: float = 5.0
    
    # Attack pack configuration
    default_attack_pack: str = "owasp-llm-top10"
    enabled_attack_packs: List[str] = Field(default_factory=lambda: ["owasp-llm-top10"])
    
    # Output configuration
    output_directory: str = "./reports"
    output_formats: List[str] = Field(default_factory=lambda: ["json"])
    retention_days: Optional[int] = 30
    
    # Compliance configuration
    nist_rmf_enabled: bool = True
    eu_ai_act_enabled: bool = True
    soc2_enabled: bool = False
    
    # Integration configuration
    slack_webhook: Optional[str] = None
    jira_project: Optional[str] = None
    splunk_hec: Optional[str] = None
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v:
            # Don't raise error here, let the scanner handle it
            pass
        return v
    
    @validator('max_requests')
    def validate_max_requests(cls, v):
        if v <= 0:
            raise ValueError('max_requests must be positive')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('timeout_seconds must be positive')
        return v
    
    @validator('parallel_workers')
    def validate_workers(cls, v):
        if v <= 0:
            raise ValueError('parallel_workers must be positive')
        return v
    
    @validator('rate_limit_rps')
    def validate_rate_limit(cls, v):
        if v <= 0:
            raise ValueError('rate_limit_rps must be positive')
        return v
    
    @validator('output_formats')
    def validate_output_formats(cls, v):
        valid_formats = {'json', 'pdf', 'html', 'csv'}
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f'Invalid output format: {fmt}. Valid: {valid_formats}')
        return v


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file or environment variables
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Config object with loaded settings
    """
    config_data = {}
    
    # Load from file if provided
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f) or {}
            config_data.update(file_config)
    
    # Override with environment variables
    env_config = _load_from_environment()
    config_data.update(env_config)
    
    return Config(**config_data)


def _load_from_environment() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    env_config = {}
    
    # Map environment variables to config fields
    env_mappings = {
        'PROMPTSTRIKE_TARGET': 'target_endpoint',
        'PROMPTSTRIKE_MODEL': 'target_model',
        'OPENAI_API_KEY': 'api_key',
        'PROMPTSTRIKE_MAX_REQUESTS': ('max_requests', int),
        'PROMPTSTRIKE_TIMEOUT': ('timeout_seconds', int),
        'PROMPTSTRIKE_WORKERS': ('parallel_workers', int),
        'PROMPTSTRIKE_RATE_LIMIT': ('rate_limit_rps', float),
        'PROMPTSTRIKE_ATTACK_PACK': 'default_attack_pack',
        'PROMPTSTRIKE_OUTPUT_DIR': 'output_directory',
        'PROMPTSTRIKE_OUTPUT_FORMATS': ('output_formats', lambda x: x.split(',')),
        'PROMPTSTRIKE_RETENTION_DAYS': ('retention_days', int),
        'PROMPTSTRIKE_NIST_ENABLED': ('nist_rmf_enabled', lambda x: x.lower() == 'true'),
        'PROMPTSTRIKE_EU_AI_ACT_ENABLED': ('eu_ai_act_enabled', lambda x: x.lower() == 'true'),
        'PROMPTSTRIKE_SOC2_ENABLED': ('soc2_enabled', lambda x: x.lower() == 'true'),
        'PROMPTSTRIKE_SLACK_WEBHOOK': 'slack_webhook',
        'PROMPTSTRIKE_JIRA_PROJECT': 'jira_project',
        'PROMPTSTRIKE_SPLUNK_HEC': 'splunk_hec',
    }
    
    for env_var, config_field in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            if isinstance(config_field, tuple):
                field_name, converter = config_field
                try:
                    env_config[field_name] = converter(value)
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass
            else:
                env_config[config_field] = value
    
    return env_config


def create_default_config_file(output_path: Path) -> None:
    """Create a default configuration file"""
    default_config = {
        'target': {
            'endpoint': 'https://api.openai.com/v1/chat/completions',
            'model': 'gpt-3.5-turbo',
            'api_key_env': 'OPENAI_API_KEY'
        },
        'scan': {
            'max_requests': 100,
            'timeout_seconds': 30,
            'parallel_workers': 1,
            'rate_limit_rps': 5.0
        },
        'attack_packs': {
            'default': 'owasp-llm-top10',
            'enabled': ['owasp-llm-top10']
        },
        'output': {
            'directory': './reports',
            'formats': ['json', 'html'],
            'retention_days': 30
        },
        'compliance': {
            'nist_rmf_enabled': True,
            'eu_ai_act_enabled': True,
            'soc2_enabled': False
        },
        'integrations': {
            'slack_webhook': None,
            'jira_project': None,
            'splunk_hec': None
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)


def get_config_template() -> str:
    """Get configuration file template as string"""
    return """# PromptStrike CLI Configuration
# Reference: cid-roadmap-v1 Sprint S-1

target:
  endpoint: "https://api.openai.com/v1/chat/completions"
  model: "gpt-3.5-turbo"
  api_key_env: "OPENAI_API_KEY"

scan:
  max_requests: 100
  timeout_seconds: 30
  parallel_workers: 1
  rate_limit_rps: 5.0

attack_packs:
  default: "owasp-llm-top10"
  enabled:
    - "owasp-llm-top10"

output:
  directory: "./reports"
  formats:
    - "json"
    - "html"
  retention_days: 30

compliance:
  nist_rmf_enabled: true
  eu_ai_act_enabled: true
  soc2_enabled: false

integrations:
  slack_webhook: null
  jira_project: null
  splunk_hec: null
"""