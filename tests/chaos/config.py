"""
Chaos Testing Configuration Management

Provides centralized configuration for chaos testing scenarios,
mutation types, and environment-specific settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Testing environments"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"
    CI = "ci"


@dataclass
class ResourceLimits:
    """Resource limits for chaos testing"""
    memory: str = "2Gi"
    cpu: str = "1000m"
    disk: str = "10Gi"
    network_bandwidth: str = "100Mbps"


@dataclass
class MutationConfig:
    """Configuration for mutation testing"""
    enabled: bool = True
    types: List[str] = field(default_factory=lambda: [
        "data_corruption", "protocol_violation", "security_payloads", "boundary_testing"
    ])
    intensity: float = 0.3
    seed: Optional[int] = None
    custom_payloads: List[str] = field(default_factory=list)
    excluded_types: List[str] = field(default_factory=list)


@dataclass
class ChaosReplayConfig:
    """Configuration for chaos replay testing"""
    enabled: bool = True
    scenarios: List[str] = field(default_factory=lambda: [
        "malformed_spans", "network_partition", "memory_pressure"
    ])
    duration: int = 120  # seconds
    intensity: float = 0.3
    concurrent_scenarios: int = 3
    recovery_timeout: float = 30.0


@dataclass
class SpanMutationConfig:
    """Configuration for span mutation testing"""
    enabled: bool = True
    malformation_rate: float = 0.8
    target_fields: List[str] = field(default_factory=lambda: [
        "trace_id", "span_id", "operation_name", "tags", "logs"
    ])
    excluded_malformations: List[str] = field(default_factory=list)
    max_nesting_depth: int = 200


@dataclass
class GorkGenerationConfig:
    """Configuration for gork generation testing"""
    enabled: bool = True
    corruption_rate: float = 0.9
    categories: List[str] = field(default_factory=lambda: [
        "binary_corruption", "encoding_corruption", "protocol_corruption"
    ])
    severity_filter: Optional[str] = None  # "high", "medium", "low"
    excluded_types: List[str] = field(default_factory=list)


@dataclass
class ReportingConfig:
    """Configuration for reporting and metrics"""
    enabled: bool = True
    formats: List[str] = field(default_factory=lambda: ["json", "text"])
    output_path: str = "./test-results"
    include_historical: bool = True
    retention_days: int = 30
    compliance_frameworks: List[str] = field(default_factory=lambda: [
        "NIST_AI_RMF", "EU_AI_ACT", "SOC2"
    ])


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    name: str
    intensity_multiplier: float = 1.0
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    disabled_scenarios: List[str] = field(default_factory=list)
    timeout_multiplier: float = 1.0
    parallel_workers: int = 4


@dataclass
class LightweightModeConfig:
    """Configuration for lightweight chaos testing mode"""
    enabled: bool = False
    auto_select_profile: bool = True
    profile_name: str = "standard"  # ultra_light, standard, balanced
    max_memory_mb: int = 512
    max_cpu_cores: float = 0.5
    max_duration_seconds: int = 30
    sample_rate: float = 0.1
    resource_monitoring: bool = True
    gc_frequency: int = 5  # Garbage collect every N tests


@dataclass
class ChaosConfig:
    """Main chaos testing configuration"""
    version: str = "1.0"
    
    # Component configurations
    mutation: MutationConfig = field(default_factory=MutationConfig)
    chaos_replay: ChaosReplayConfig = field(default_factory=ChaosReplayConfig)
    span_mutation: SpanMutationConfig = field(default_factory=SpanMutationConfig)
    gork_generation: GorkGenerationConfig = field(default_factory=GorkGenerationConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    lightweight_mode: LightweightModeConfig = field(default_factory=LightweightModeConfig)
    
    # Environment configurations
    environments: Dict[str, EnvironmentConfig] = field(default_factory=dict)
    
    # Global settings
    global_seed: Optional[int] = None
    debug_mode: bool = False
    dry_run: bool = False
    fail_fast: bool = False


class ChaosConfigManager:
    """Manages chaos testing configuration loading and validation"""
    
    DEFAULT_CONFIG_PATHS = [
        "chaos-config.yaml",
        "chaos-config.yml", 
        ".chaos.yaml",
        ".chaos.yml",
        "tests/chaos-config.yaml"
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self._load_config()
        self._apply_environment_overrides()
    
    def _load_config(self) -> ChaosConfig:
        """Load configuration from file or environment"""
        config_data = {}
        
        # Try to load from file
        if self.config_path:
            config_data = self._load_from_file(self.config_path)
        else:
            # Try default paths
            for path in self.DEFAULT_CONFIG_PATHS:
                if Path(path).exists():
                    config_data = self._load_from_file(path)
                    break
        
        # Apply environment variable overrides
        config_data = self._merge_env_vars(config_data)
        
        # Create config object
        return self._create_config_object(config_data)
    
    def _load_from_file(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config from {path}: {e}")
            return {}
    
    def _merge_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variable overrides"""
        env_mappings = {
            # Global settings
            'CHAOS_DEBUG_MODE': ('debug_mode', bool),
            'CHAOS_DRY_RUN': ('dry_run', bool),
            'CHAOS_GLOBAL_SEED': ('global_seed', int),
            'CHAOS_FAIL_FAST': ('fail_fast', bool),
            
            # Mutation settings
            'CHAOS_MUTATION_ENABLED': ('mutation.enabled', bool),
            'CHAOS_MUTATION_INTENSITY': ('mutation.intensity', float),
            'CHAOS_MUTATION_TYPES': ('mutation.types', list),
            'CHAOS_MUTATION_SEED': ('mutation.seed', int),
            
            # Chaos replay settings
            'CHAOS_REPLAY_ENABLED': ('chaos_replay.enabled', bool),
            'CHAOS_REPLAY_DURATION': ('chaos_replay.duration', int),
            'CHAOS_REPLAY_INTENSITY': ('chaos_replay.intensity', float),
            'CHAOS_REPLAY_SCENARIOS': ('chaos_replay.scenarios', list),
            
            # Span mutation settings
            'CHAOS_SPAN_ENABLED': ('span_mutation.enabled', bool),
            'CHAOS_SPAN_MALFORMATION_RATE': ('span_mutation.malformation_rate', float),
            'CHAOS_SPAN_TARGET_FIELDS': ('span_mutation.target_fields', list),
            
            # Gork generation settings
            'CHAOS_GORK_ENABLED': ('gork_generation.enabled', bool),
            'CHAOS_GORK_CORRUPTION_RATE': ('gork_generation.corruption_rate', float),
            'CHAOS_GORK_CATEGORIES': ('gork_generation.categories', list),
            'CHAOS_GORK_SEVERITY_FILTER': ('gork_generation.severity_filter', str),
            
            # Lightweight mode settings
            'CHAOS_LIGHTWEIGHT_ENABLED': ('lightweight_mode.enabled', bool),
            'CHAOS_LIGHTWEIGHT_PROFILE': ('lightweight_mode.profile_name', str),
            'CHAOS_LIGHTWEIGHT_MEMORY_MB': ('lightweight_mode.max_memory_mb', int),
            'CHAOS_LIGHTWEIGHT_CPU_CORES': ('lightweight_mode.max_cpu_cores', float),
            'CHAOS_LIGHTWEIGHT_DURATION': ('lightweight_mode.max_duration_seconds', int),
            'CHAOS_LIGHTWEIGHT_SAMPLE_RATE': ('lightweight_mode.sample_rate', float),
            
            # Reporting settings
            'CHAOS_REPORTING_ENABLED': ('reporting.enabled', bool),
            'CHAOS_REPORTING_FORMATS': ('reporting.formats', list),
            'CHAOS_REPORTING_OUTPUT_PATH': ('reporting.output_path', str),
            'CHAOS_REPORTING_RETENTION_DAYS': ('reporting.retention_days', int),
            
            # Resource limits
            'CHAOS_MEMORY_LIMIT': ('resource_limits.memory', str),
            'CHAOS_CPU_LIMIT': ('resource_limits.cpu', str),
            'CHAOS_DISK_LIMIT': ('resource_limits.disk', str),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Convert value to appropriate type
                    if value_type == bool:
                        parsed_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        parsed_value = int(env_value)
                    elif value_type == float:
                        parsed_value = float(env_value)
                    elif value_type == list:
                        parsed_value = [x.strip() for x in env_value.split(',')]
                    else:
                        parsed_value = env_value
                    
                    # Set nested config value
                    self._set_nested_value(config_data, config_path, parsed_value)
                    
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var}: {env_value} ({e})")
        
        return config_data
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> ChaosConfig:
        """Create ChaosConfig object from dictionary"""
        try:
            # Handle nested configurations
            mutation_data = config_data.get('mutation', {})
            chaos_replay_data = config_data.get('chaos_replay', {})
            span_mutation_data = config_data.get('span_mutation', {})
            gork_generation_data = config_data.get('gork_generation', {})
            reporting_data = config_data.get('reporting', {})
            lightweight_mode_data = config_data.get('lightweight_mode', {})
            
            # Create component configs
            mutation_config = MutationConfig(**mutation_data)
            chaos_replay_config = ChaosReplayConfig(**chaos_replay_data)
            span_mutation_config = SpanMutationConfig(**span_mutation_data)
            gork_generation_config = GorkGenerationConfig(**gork_generation_data)
            reporting_config = ReportingConfig(**reporting_data)
            lightweight_mode_config = LightweightModeConfig(**lightweight_mode_data)
            
            # Handle environment configurations
            environments = {}
            env_data = config_data.get('environments', {})
            for env_name, env_config in env_data.items():
                resource_limits_data = env_config.get('resource_limits', {})
                resource_limits = ResourceLimits(**resource_limits_data)
                
                env_config_obj = EnvironmentConfig(
                    name=env_name,
                    intensity_multiplier=env_config.get('intensity_multiplier', 1.0),
                    resource_limits=resource_limits,
                    disabled_scenarios=env_config.get('disabled_scenarios', []),
                    timeout_multiplier=env_config.get('timeout_multiplier', 1.0),
                    parallel_workers=env_config.get('parallel_workers', 4)
                )
                environments[env_name] = env_config_obj
            
            # Create main config
            return ChaosConfig(
                version=config_data.get('version', '1.0'),
                mutation=mutation_config,
                chaos_replay=chaos_replay_config,
                span_mutation=span_mutation_config,
                gork_generation=gork_generation_config,
                reporting=reporting_config,
                lightweight_mode=lightweight_mode_config,
                environments=environments,
                global_seed=config_data.get('global_seed'),
                debug_mode=config_data.get('debug_mode', False),
                dry_run=config_data.get('dry_run', False),
                fail_fast=config_data.get('fail_fast', False)
            )
            
        except Exception as e:
            print(f"Warning: Error creating config object: {e}")
            return ChaosConfig()  # Return default config
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        current_env = os.getenv('CHAOS_ENVIRONMENT', 'development')
        
        if current_env in self.config.environments:
            env_config = self.config.environments[current_env]
            
            # Apply intensity multiplier
            multiplier = env_config.intensity_multiplier
            self.config.mutation.intensity *= multiplier
            self.config.chaos_replay.intensity *= multiplier
            self.config.span_mutation.malformation_rate *= multiplier
            self.config.gork_generation.corruption_rate *= multiplier
            
            # Apply disabled scenarios
            for scenario in env_config.disabled_scenarios:
                if scenario in self.config.chaos_replay.scenarios:
                    self.config.chaos_replay.scenarios.remove(scenario)
                if scenario in self.config.gork_generation.categories:
                    self.config.gork_generation.categories.remove(scenario)
            
            print(f"Applied {current_env} environment configuration")
    
    def get_config(self) -> ChaosConfig:
        """Get the loaded configuration"""
        return self.config
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate intensity values
        if not 0.0 <= self.config.mutation.intensity <= 1.0:
            issues.append("mutation.intensity must be between 0.0 and 1.0")
        
        if not 0.0 <= self.config.chaos_replay.intensity <= 1.0:
            issues.append("chaos_replay.intensity must be between 0.0 and 1.0")
        
        if not 0.0 <= self.config.span_mutation.malformation_rate <= 1.0:
            issues.append("span_mutation.malformation_rate must be between 0.0 and 1.0")
        
        if not 0.0 <= self.config.gork_generation.corruption_rate <= 1.0:
            issues.append("gork_generation.corruption_rate must be between 0.0 and 1.0")
        
        # Validate durations
        if self.config.chaos_replay.duration <= 0:
            issues.append("chaos_replay.duration must be positive")
        
        if self.config.chaos_replay.recovery_timeout <= 0:
            issues.append("chaos_replay.recovery_timeout must be positive")
        
        # Validate paths
        if not self.config.reporting.output_path:
            issues.append("reporting.output_path cannot be empty")
        
        # Validate resource limits format
        for env_name, env_config in self.config.environments.items():
            limits = env_config.resource_limits
            if not self._validate_memory_format(limits.memory):
                issues.append(f"Invalid memory format in {env_name}: {limits.memory}")
            if not self._validate_cpu_format(limits.cpu):
                issues.append(f"Invalid CPU format in {env_name}: {limits.cpu}")
        
        # Validate scenario compatibility
        compatibility_issues = self._validate_scenario_compatibility()
        issues.extend(compatibility_issues)
        
        # Validate environment-specific configurations
        env_issues = self._validate_environment_configs()
        issues.extend(env_issues)
        
        # Validate resource constraints
        resource_issues = self._validate_resource_constraints()
        issues.extend(resource_issues)
        
        # Validate lightweight mode configuration
        lightweight_issues = self._validate_lightweight_mode()
        issues.extend(lightweight_issues)
        
        return issues
    
    def _validate_memory_format(self, memory: str) -> bool:
        """Validate memory format (e.g., '2Gi', '1024Mi')"""
        import re
        pattern = r'^\d+(\.\d+)?(Ki|Mi|Gi|Ti|K|M|G|T)?$'
        return bool(re.match(pattern, memory))
    
    def _validate_cpu_format(self, cpu: str) -> bool:
        """Validate CPU format (e.g., '1000m', '1.5')"""
        import re
        pattern = r'^\d+(\.\d+)?m?$'
        return bool(re.match(pattern, cpu))
    
    def _validate_scenario_compatibility(self) -> List[str]:
        """Validate scenario compatibility to prevent conflicting chaos scenarios"""
        issues = []
        
        # Define scenario incompatibility rules
        incompatible_scenarios = {
            # Memory-related conflicts
            ('memory_pressure', 'compression_bomb'): 
                "Memory pressure and compression bomb scenarios cannot run together - may cause system instability",
            ('memory_pressure', 'buffer_overflow'): 
                "Memory pressure and buffer overflow scenarios may conflict - excessive memory consumption",
            
            # Network-related conflicts
            ('network_partition', 'dependency_failure'): 
                "Network partition and dependency failure may create cascading failures",
            ('slow_network', 'timeout_chaos'): 
                "Slow network and timeout chaos may interfere with each other's timing",
            
            # Data corruption conflicts
            ('corrupted_payloads', 'gork_data'): 
                "Corrupted payloads and gork data may create overlapping mutations",
            ('malformed_spans', 'encoding_errors'): 
                "Malformed spans and encoding errors may mask each other's effects",
            
            # Resource conflicts
            ('cpu_spike', 'race_conditions'): 
                "CPU spike and race conditions may create unpredictable timing issues",
            ('disk_full', 'memory_pressure'): 
                "Disk full and memory pressure may cause system deadlock",
            
            # Protocol conflicts
            ('protocol_violation', 'malformed_spans'): 
                "Protocol violations and malformed spans may overlap - reduce one intensity",
            ('security_payloads', 'boundary_testing'): 
                "Security payloads and boundary testing may interfere - stagger execution",
                
            # Financial system conflicts (FinTech-specific)
            ('network_partition', 'memory_pressure'): 
                "Network partition + memory pressure combination is dangerous for financial systems",
            ('timeout_chaos', 'dependency_failure'): 
                "Timeout chaos + dependency failure may break transaction integrity",
        }
        
        # Get all enabled scenarios across components
        enabled_scenarios = []
        
        if self.config.chaos_replay.enabled:
            enabled_scenarios.extend(self.config.chaos_replay.scenarios)
        
        if self.config.mutation.enabled:
            enabled_scenarios.extend(self.config.mutation.types)
        
        if self.config.gork_generation.enabled:
            enabled_scenarios.extend(self.config.gork_generation.categories)
        
        # Check for incompatible scenario combinations
        for (scenario1, scenario2), message in incompatible_scenarios.items():
            if scenario1 in enabled_scenarios and scenario2 in enabled_scenarios:
                issues.append(f"Scenario compatibility issue: {message}")
        
        # Validate scenario intensity combinations
        intensity_issues = self._validate_intensity_combinations(enabled_scenarios)
        issues.extend(intensity_issues)
        
        # Validate concurrent scenario limits
        if len(enabled_scenarios) > self.config.chaos_replay.concurrent_scenarios:
            issues.append(
                f"Too many concurrent scenarios enabled ({len(enabled_scenarios)}) "
                f"- maximum is {self.config.chaos_replay.concurrent_scenarios}"
            )
        
        return issues
    
    def _validate_intensity_combinations(self, enabled_scenarios: List[str]) -> List[str]:
        """Validate that intensity combinations don't exceed safe thresholds"""
        issues = []
        
        # Calculate total chaos intensity
        total_intensity = (
            self.config.mutation.intensity +
            self.config.chaos_replay.intensity +
            self.config.span_mutation.malformation_rate +
            self.config.gork_generation.corruption_rate
        )
        
        # Define safe intensity thresholds by environment
        intensity_thresholds = {
            'production': 1.5,  # Very conservative
            'staging': 2.5,     # Moderate
            'development': 4.0, # Can handle higher chaos
            'ci': 2.0          # Moderate for CI
        }
        
        current_env = os.getenv('CHAOS_ENVIRONMENT', 'development')
        max_intensity = intensity_thresholds.get(current_env, 2.0)
        
        if total_intensity > max_intensity:
            issues.append(
                f"Total chaos intensity ({total_intensity:.2f}) exceeds safe threshold "
                f"for {current_env} environment ({max_intensity})"
            )
        
        # Check for dangerous scenario combinations with high intensity
        dangerous_combinations = [
            (['memory_pressure', 'cpu_spike'], 1.2, "System resource scenarios"),
            (['network_partition', 'timeout_chaos'], 1.0, "Network timing scenarios"),
            (['corrupted_payloads', 'malformed_spans', 'gork_data'], 1.5, "Data corruption scenarios"),
            (['security_payloads', 'protocol_violation'], 1.0, "Security testing scenarios")
        ]
        
        for scenario_group, threshold, description in dangerous_combinations:
            if all(scenario in enabled_scenarios for scenario in scenario_group):
                group_intensity = sum(getattr(self.config.chaos_replay, 'intensity', 0.3) 
                                    for _ in scenario_group)
                if group_intensity > threshold:
                    issues.append(
                        f"{description} combined intensity ({group_intensity:.2f}) "
                        f"exceeds safe threshold ({threshold})"
                    )
        
        return issues
    
    def _validate_environment_configs(self) -> List[str]:
        """Validate environment-specific configurations"""
        issues = []
        
        for env_name, env_config in self.config.environments.items():
            # Validate production environment constraints
            if env_name == 'production':
                if env_config.intensity_multiplier > 0.5:
                    issues.append(
                        f"Production environment intensity multiplier ({env_config.intensity_multiplier}) "
                        f"should not exceed 0.5 for safety"
                    )
                
                # Production should have restricted scenarios
                dangerous_scenarios = [
                    'compression_bomb', 'buffer_overflow', 'cascading_failure',
                    'disk_full', 'file_descriptor_exhaustion'
                ]
                for scenario in dangerous_scenarios:
                    if scenario not in env_config.disabled_scenarios:
                        issues.append(
                            f"Production environment should disable dangerous scenario: {scenario}"
                        )
            
            # Validate CI environment constraints  
            elif env_name == 'ci':
                if env_config.timeout_multiplier > 2.0:
                    issues.append(
                        f"CI environment timeout multiplier ({env_config.timeout_multiplier}) "
                        f"should not exceed 2.0 to avoid build timeouts"
                    )
                
                if env_config.parallel_workers > 2:
                    issues.append(
                        f"CI environment should limit parallel workers to 2 "
                        f"(currently {env_config.parallel_workers})"
                    )
        
        return issues
    
    def _validate_resource_constraints(self) -> List[str]:
        """Validate resource constraints for safe testing"""
        issues = []
        
        current_env = os.getenv('CHAOS_ENVIRONMENT', 'development')
        
        if current_env in self.config.environments:
            env_config = self.config.environments[current_env]
            limits = env_config.resource_limits
            
            # Parse memory limit
            memory_mb = self._parse_memory_to_mb(limits.memory)
            cpu_cores = self._parse_cpu_to_cores(limits.cpu)
            
            # Validate minimum requirements
            if memory_mb < 512:  # 512MB minimum
                issues.append(
                    f"Memory limit ({limits.memory}) is below minimum requirement (512MB)"
                )
            
            if cpu_cores < 0.5:  # 0.5 CPU minimum
                issues.append(
                    f"CPU limit ({limits.cpu}) is below minimum requirement (0.5 cores)"
                )
            
            # Validate maximum safe limits for different environments
            max_memory = {
                'production': 4096,  # 4GB max
                'staging': 8192,     # 8GB max  
                'development': 16384, # 16GB max
                'ci': 2048           # 2GB max
            }
            
            max_cpu = {
                'production': 2.0,   # 2 cores max
                'staging': 4.0,      # 4 cores max
                'development': 8.0,  # 8 cores max
                'ci': 1.0            # 1 core max
            }
            
            if memory_mb > max_memory.get(current_env, 8192):
                issues.append(
                    f"Memory limit ({limits.memory}) exceeds maximum for {current_env} "
                    f"environment ({max_memory.get(current_env)}MB)"
                )
            
            if cpu_cores > max_cpu.get(current_env, 4.0):
                issues.append(
                    f"CPU limit ({limits.cpu}) exceeds maximum for {current_env} "
                    f"environment ({max_cpu.get(current_env)} cores)"
                )
        
        return issues
    
    def _parse_memory_to_mb(self, memory_str: str) -> float:
        """Parse memory string to MB (e.g., '2Gi' -> 2048)"""
        import re
        match = re.match(r'^(\d+(?:\.\d+)?)(Ki|Mi|Gi|Ti|K|M|G|T)?$', memory_str)
        if not match:
            return 0
        
        value = float(match.group(1))
        unit = match.group(2) or ''
        
        multipliers = {
            'Ki': 1/1024, 'Mi': 1, 'Gi': 1024, 'Ti': 1024*1024,
            'K': 1/1024, 'M': 1, 'G': 1024, 'T': 1024*1024
        }
        
        return value * multipliers.get(unit, 1)
    
    def _parse_cpu_to_cores(self, cpu_str: str) -> float:
        """Parse CPU string to cores (e.g., '1000m' -> 1.0)"""
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)
    
    def _validate_lightweight_mode(self) -> List[str]:
        """Validate lightweight mode configuration"""
        issues = []
        
        if not self.config.lightweight_mode.enabled:
            return issues  # Skip validation if not enabled
        
        lw_config = self.config.lightweight_mode
        
        # Validate memory limits
        if lw_config.max_memory_mb < 128:
            issues.append(
                f"Lightweight mode memory limit ({lw_config.max_memory_mb}MB) "
                f"is too low - minimum 128MB required"
            )
        elif lw_config.max_memory_mb > 2048:
            issues.append(
                f"Lightweight mode memory limit ({lw_config.max_memory_mb}MB) "
                f"defeats the purpose - consider standard mode"
            )
        
        # Validate CPU limits
        if lw_config.max_cpu_cores < 0.1:
            issues.append(
                f"Lightweight mode CPU limit ({lw_config.max_cpu_cores}) "
                f"is too low - minimum 0.1 cores required"
            )
        elif lw_config.max_cpu_cores > 2.0:
            issues.append(
                f"Lightweight mode CPU limit ({lw_config.max_cpu_cores}) "
                f"is too high for lightweight mode"
            )
        
        # Validate duration
        if lw_config.max_duration_seconds < 5:
            issues.append(
                f"Lightweight mode duration ({lw_config.max_duration_seconds}s) "
                f"is too short - minimum 5 seconds"
            )
        elif lw_config.max_duration_seconds > 300:
            issues.append(
                f"Lightweight mode duration ({lw_config.max_duration_seconds}s) "
                f"is too long for lightweight mode"
            )
        
        # Validate sample rate
        if not 0.01 <= lw_config.sample_rate <= 1.0:
            issues.append(
                f"Lightweight mode sample rate ({lw_config.sample_rate}) "
                f"must be between 0.01 and 1.0"
            )
        
        # Validate profile name
        valid_profiles = ['ultra_light', 'standard', 'balanced']
        if lw_config.profile_name not in valid_profiles:
            issues.append(
                f"Invalid lightweight mode profile '{lw_config.profile_name}' "
                f"- must be one of: {valid_profiles}"
            )
        
        # Check consistency with other configurations
        if (lw_config.enabled and 
            self.config.chaos_replay.concurrent_scenarios > 2):
            issues.append(
                "Lightweight mode enabled but chaos_replay.concurrent_scenarios > 2 "
                "- reduce to 1-2 for optimal resource usage"
            )
        
        # Environment-specific lightweight mode validation
        current_env = os.getenv('CHAOS_ENVIRONMENT', 'development')
        if current_env == 'production' and lw_config.enabled:
            if lw_config.profile_name not in ['ultra_light', 'standard']:
                issues.append(
                    f"Production environment with lightweight mode should use "
                    f"'ultra_light' or 'standard' profile, not '{lw_config.profile_name}'"
                )
        
        return issues
    
    def save_config(self, path: str):
        """Save current configuration to file"""
        config_dict = self._config_to_dict()
        
        with open(path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert config object to dictionary"""
        def dataclass_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                result = {}
                for field_name, field_def in obj.__dataclass_fields__.items():
                    value = getattr(obj, field_name)
                    if hasattr(value, '__dataclass_fields__'):
                        result[field_name] = dataclass_to_dict(value)
                    elif isinstance(value, dict):
                        result[field_name] = {k: dataclass_to_dict(v) if hasattr(v, '__dataclass_fields__') else v 
                                            for k, v in value.items()}
                    elif isinstance(value, list):
                        result[field_name] = [dataclass_to_dict(item) if hasattr(item, '__dataclass_fields__') else item 
                                            for item in value]
                    else:
                        result[field_name] = value
                return result
            return obj
        
        return dataclass_to_dict(self.config)
    
    def get_environment_config(self, environment: str) -> Optional[EnvironmentConfig]:
        """Get configuration for specific environment"""
        return self.config.environments.get(environment)
    
    def is_scenario_enabled(self, scenario: str, environment: str = None) -> bool:
        """Check if a chaos scenario is enabled for the given environment"""
        if environment and environment in self.config.environments:
            env_config = self.config.environments[environment]
            if scenario in env_config.disabled_scenarios:
                return False
        
        # Check component-specific enablement
        if scenario in ['malformed_spans', 'network_partition', 'memory_pressure']:
            return self.config.chaos_replay.enabled and scenario in self.config.chaos_replay.scenarios
        elif scenario in ['data_corruption', 'protocol_violation', 'security_payloads']:
            return self.config.mutation.enabled and scenario in self.config.mutation.types
        elif scenario in ['binary_corruption', 'encoding_corruption', 'protocol_corruption']:
            return self.config.gork_generation.enabled and scenario in self.config.gork_generation.categories
        
        return True


# Global config manager instance
_config_manager = None

def get_chaos_config(config_path: Optional[str] = None) -> ChaosConfig:
    """Get global chaos configuration"""
    global _config_manager
    if _config_manager is None or config_path:
        _config_manager = ChaosConfigManager(config_path)
    return _config_manager.get_config()

def reload_chaos_config(config_path: Optional[str] = None):
    """Reload chaos configuration"""
    global _config_manager
    _config_manager = ChaosConfigManager(config_path)

def validate_chaos_config(config_path: Optional[str] = None) -> List[str]:
    """Validate chaos configuration and return issues"""
    manager = ChaosConfigManager(config_path)
    return manager.validate_config()

def validate_scenario_compatibility(scenarios: List[str], environment: str = None) -> Dict[str, Any]:
    """
    Validate compatibility of a specific set of scenarios
    
    Args:
        scenarios: List of scenario names to validate
        environment: Target environment (optional)
        
    Returns:
        Dictionary with validation results
    """
    # Load configuration
    config = get_chaos_config()
    
    # Define conflict matrix
    conflict_matrix = {
        'memory_pressure': ['compression_bomb', 'buffer_overflow', 'disk_full'],
        'network_partition': ['dependency_failure', 'slow_network'],
        'corrupted_payloads': ['gork_data', 'encoding_errors'],
        'malformed_spans': ['encoding_errors', 'protocol_violation'],
        'cpu_spike': ['race_conditions', 'memory_pressure'],
        'timeout_chaos': ['slow_network', 'dependency_failure'],
    }
    
    # Risk scoring matrix (0-10, higher = more dangerous)
    risk_scores = {
        'memory_pressure': 8, 'compression_bomb': 10, 'buffer_overflow': 9,
        'network_partition': 7, 'dependency_failure': 6, 'slow_network': 4,
        'corrupted_payloads': 5, 'gork_data': 6, 'encoding_errors': 4,
        'malformed_spans': 5, 'protocol_violation': 6, 'cpu_spike': 7,
        'race_conditions': 8, 'disk_full': 9, 'timeout_chaos': 5
    }
    
    conflicts = []
    warnings = []
    total_risk = 0
    
    # Check for direct conflicts
    for scenario in scenarios:
        total_risk += risk_scores.get(scenario, 3)
        
        conflicting = conflict_matrix.get(scenario, [])
        for conflict in conflicting:
            if conflict in scenarios:
                conflicts.append({
                    'scenario1': scenario,
                    'scenario2': conflict,
                    'severity': 'high',
                    'message': f"{scenario} conflicts with {conflict}"
                })
    
    # Environment-specific warnings
    if environment == 'production':
        high_risk_scenarios = [s for s in scenarios if risk_scores.get(s, 0) > 7]
        if high_risk_scenarios:
            warnings.append({
                'type': 'environment_risk',
                'message': f"High-risk scenarios in production: {high_risk_scenarios}"
            })
    
    # Calculate compatibility score (0-100)
    max_possible_risk = len(scenarios) * 10
    compatibility_score = max(0, 100 - int((total_risk / max_possible_risk) * 100)) if max_possible_risk > 0 else 100
    
    return {
        'compatible': len(conflicts) == 0,
        'conflicts': conflicts,
        'warnings': warnings,
        'risk_score': total_risk,
        'compatibility_score': compatibility_score,
        'recommendations': _generate_compatibility_recommendations(scenarios, conflicts, environment)
    }

def _generate_compatibility_recommendations(scenarios: List[str], conflicts: List[Dict], environment: str = None) -> List[str]:
    """Generate recommendations for improving scenario compatibility"""
    recommendations = []
    
    if conflicts:
        recommendations.append("Consider running conflicting scenarios in separate test phases")
        recommendations.append("Reduce chaos intensity when running multiple high-risk scenarios")
        
        # Specific conflict resolutions
        for conflict in conflicts:
            scenario1, scenario2 = conflict['scenario1'], conflict['scenario2']
            if 'memory' in scenario1 or 'memory' in scenario2:
                recommendations.append("For memory-related conflicts: stagger execution by 30+ seconds")
            elif 'network' in scenario1 or 'network' in scenario2:
                recommendations.append("For network-related conflicts: use different network segments")
    
    if environment == 'production':
        recommendations.append("Production environment: limit to maximum 2 concurrent scenarios")
        recommendations.append("Production environment: enable monitoring and automatic rollback")
    elif environment == 'ci':
        recommendations.append("CI environment: reduce test duration to avoid build timeouts")
        recommendations.append("CI environment: use lightweight scenarios only")
    
    if len(scenarios) > 5:
        recommendations.append("Consider breaking large test suites into smaller, focused test runs")
    
    return recommendations