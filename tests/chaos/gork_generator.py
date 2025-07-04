"""
Gork Generator - Garbled/Corrupted Data Generator

Specialized generator for creating "gork" data - deliberately garbled, corrupted,
or malformed data that tests system resilience against various data corruption scenarios.

"Gork" encompasses:
- Binary corruption in text fields
- Encoding nightmares  
- Protocol buffer corruption
- Compression artifacts
- Network transmission errors
- File system corruption patterns
- Memory corruption patterns
"""

import random
import struct
import zlib
import base64
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass

class GorkType(Enum):
    """Types of gork (garbled data) patterns"""
    # Binary corruption
    RANDOM_BINARY = "random_binary"
    NULL_BYTE_INJECTION = "null_byte_injection"
    HIGH_BIT_SET = "high_bit_set"
    BINARY_IN_TEXT = "binary_in_text"
    
    # Encoding corruption
    INVALID_UTF8 = "invalid_utf8"
    MIXED_ENCODING = "mixed_encoding"
    OVERLONG_UTF8 = "overlong_utf8"
    SURROGATE_PAIRS = "surrogate_pairs"
    BOM_CORRUPTION = "bom_corruption"
    
    # Protocol corruption
    PROTOBUF_CORRUPTION = "protobuf_corruption"
    JSON_CORRUPTION = "json_corruption"
    XML_CORRUPTION = "xml_corruption"
    HTTP_HEADER_CORRUPTION = "http_header_corruption"
    
    # Compression corruption
    GZIP_CORRUPTION = "gzip_corruption"
    DEFLATE_CORRUPTION = "deflate_corruption"
    COMPRESSION_BOMB = "compression_bomb"
    
    # Network corruption
    PACKET_CORRUPTION = "packet_corruption"
    TCP_CORRUPTION = "tcp_corruption"
    ETHERNET_CORRUPTION = "ethernet_corruption"
    
    # File system corruption
    INODE_CORRUPTION = "inode_corruption"
    METADATA_CORRUPTION = "metadata_corruption"
    BLOCK_CORRUPTION = "block_corruption"
    
    # Memory corruption
    HEAP_CORRUPTION = "heap_corruption"
    STACK_CORRUPTION = "stack_corruption"
    BUFFER_OVERFLOW = "buffer_overflow"
    USE_AFTER_FREE = "use_after_free"
    
    # Format corruption
    BASE64_CORRUPTION = "base64_corruption"
    HEX_CORRUPTION = "hex_corruption"
    URL_ENCODING_CORRUPTION = "url_encoding_corruption"
    
    # Control flow corruption
    UNICODE_DIRECTION = "unicode_direction"
    ZERO_WIDTH_CHARS = "zero_width_chars"
    COMBINING_CHARS = "combining_chars"
    
    # Time corruption
    EPOCH_CORRUPTION = "epoch_corruption"
    TIMEZONE_CORRUPTION = "timezone_corruption"
    
    # Cryptographic corruption
    HASH_COLLISION = "hash_collision"
    SIGNATURE_CORRUPTION = "signature_corruption"
    CERTIFICATE_CORRUPTION = "certificate_corruption"

@dataclass
class GorkResult:
    """Result of gork generation"""
    gork_type: GorkType
    original_data: Any
    gork_data: Any
    corruption_points: List[str]
    description: str
    expected_failures: List[str]  # Expected failure modes

class GorkGenerator:
    """
    Generator for various types of garbled/corrupted data patterns.
    Creates realistic corruption scenarios that could occur in production systems.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        
        # Common corruption patterns
        self.binary_patterns = [
            b'\\x00',  # Null bytes
            b'\\xff',  # High bytes
            b'\\x7f',  # DEL character
            b'\\x1f\\x8b',  # GZIP header
            b'\\x89PNG',  # PNG header
            b'\\x25PDF',  # PDF header
            b'\\xde\\xad\\xbe\\xef',  # Classic hex pattern
            b'\\xca\\xfe\\xba\\xbe',  # Java class file magic
        ]
        
        # Invalid UTF-8 sequences
        self.invalid_utf8_sequences = [
            b'\\xc0\\x80',  # Overlong encoding of NULL
            b'\\xc1\\xbf',  # Overlong encoding
            b'\\xe0\\x80\\x80',  # Overlong 3-byte
            b'\\xf0\\x80\\x80\\x80',  # Overlong 4-byte
            b'\\xed\\xa0\\x80',  # High surrogate
            b'\\xed\\xb0\\x80',  # Low surrogate
            b'\\xf4\\x90\\x80\\x80',  # Above Unicode range
            b'\\xff\\xfe\\x00\\x00',  # UTF-32 BOM
        ]
        
        # Unicode direction and control characters
        self.unicode_corruption = [
            '\\u202e',  # Right-to-left override
            '\\u202d',  # Left-to-right override
            '\\u200e',  # Left-to-right mark
            '\\u200f',  # Right-to-left mark
            '\\u061c',  # Arabic letter mark
            '\\u2066',  # Left-to-right isolate
            '\\u2067',  # Right-to-left isolate
            '\\u2068',  # First strong isolate
            '\\u2069',  # Pop directional isolate
        ]
        
        # Zero-width and combining characters
        self.zero_width_chars = [
            '\\u200b',  # Zero width space
            '\\u200c',  # Zero width non-joiner
            '\\u200d',  # Zero width joiner
            '\\ufeff',  # Zero width no-break space (BOM)
            '\\u034f',  # Combining grapheme joiner
        ]
        
        # Gork generation strategies
        self.gork_strategies = {
            GorkType.RANDOM_BINARY: self._generate_random_binary_gork,
            GorkType.NULL_BYTE_INJECTION: self._generate_null_byte_gork,
            GorkType.HIGH_BIT_SET: self._generate_high_bit_gork,
            GorkType.BINARY_IN_TEXT: self._generate_binary_in_text_gork,
            GorkType.INVALID_UTF8: self._generate_invalid_utf8_gork,
            GorkType.MIXED_ENCODING: self._generate_mixed_encoding_gork,
            GorkType.OVERLONG_UTF8: self._generate_overlong_utf8_gork,
            GorkType.SURROGATE_PAIRS: self._generate_surrogate_pairs_gork,
            GorkType.BOM_CORRUPTION: self._generate_bom_corruption_gork,
            GorkType.PROTOBUF_CORRUPTION: self._generate_protobuf_corruption_gork,
            GorkType.JSON_CORRUPTION: self._generate_json_corruption_gork,
            GorkType.XML_CORRUPTION: self._generate_xml_corruption_gork,
            GorkType.HTTP_HEADER_CORRUPTION: self._generate_http_header_corruption_gork,
            GorkType.GZIP_CORRUPTION: self._generate_gzip_corruption_gork,
            GorkType.DEFLATE_CORRUPTION: self._generate_deflate_corruption_gork,
            GorkType.COMPRESSION_BOMB: self._generate_compression_bomb_gork,
            GorkType.PACKET_CORRUPTION: self._generate_packet_corruption_gork,
            GorkType.TCP_CORRUPTION: self._generate_tcp_corruption_gork,
            GorkType.ETHERNET_CORRUPTION: self._generate_ethernet_corruption_gork,
            GorkType.INODE_CORRUPTION: self._generate_inode_corruption_gork,
            GorkType.METADATA_CORRUPTION: self._generate_metadata_corruption_gork,
            GorkType.BLOCK_CORRUPTION: self._generate_block_corruption_gork,
            GorkType.HEAP_CORRUPTION: self._generate_heap_corruption_gork,
            GorkType.STACK_CORRUPTION: self._generate_stack_corruption_gork,
            GorkType.BUFFER_OVERFLOW: self._generate_buffer_overflow_gork,
            GorkType.USE_AFTER_FREE: self._generate_use_after_free_gork,
            GorkType.BASE64_CORRUPTION: self._generate_base64_corruption_gork,
            GorkType.HEX_CORRUPTION: self._generate_hex_corruption_gork,
            GorkType.URL_ENCODING_CORRUPTION: self._generate_url_encoding_corruption_gork,
            GorkType.UNICODE_DIRECTION: self._generate_unicode_direction_gork,
            GorkType.ZERO_WIDTH_CHARS: self._generate_zero_width_chars_gork,
            GorkType.COMBINING_CHARS: self._generate_combining_chars_gork,
            GorkType.EPOCH_CORRUPTION: self._generate_epoch_corruption_gork,
            GorkType.TIMEZONE_CORRUPTION: self._generate_timezone_corruption_gork,
            GorkType.HASH_COLLISION: self._generate_hash_collision_gork,
            GorkType.SIGNATURE_CORRUPTION: self._generate_signature_corruption_gork,
            GorkType.CERTIFICATE_CORRUPTION: self._generate_certificate_corruption_gork,
        }
    
    def generate_gork(self, data: Any, gork_type: Optional[GorkType] = None, 
                     corruption_rate: float = 0.5) -> GorkResult:
        """
        Generate gork (garbled/corrupted) data from input data.
        
        Args:
            data: Original data to corrupt
            gork_type: Type of gork to generate (random if None)
            corruption_rate: Intensity of corruption (0.0-1.0)
            
        Returns:
            GorkResult with original and corrupted data
        """
        if gork_type is None:
            gork_type = self.random.choice(list(GorkType))
        
        try:
            strategy = self.gork_strategies[gork_type]
            gork_data, corruption_points, description, expected_failures = strategy(data, corruption_rate)
            
            return GorkResult(
                gork_type=gork_type,
                original_data=data,
                gork_data=gork_data,
                corruption_points=corruption_points,
                description=description,
                expected_failures=expected_failures
            )
        except Exception as e:
            # Fallback to basic corruption
            return GorkResult(
                gork_type=gork_type,
                original_data=data,
                gork_data=f"GORK_ERROR_{str(data)}_{str(e)}",
                corruption_points=[f"error_{type(e).__name__}"],
                description=f"Gork generation failed: {str(e)}",
                expected_failures=["parsing_error", "encoding_error"]
            )
    
    def batch_generate_gork(self, data_samples: List[Any], 
                           gork_types: Optional[List[GorkType]] = None) -> List[GorkResult]:
        """Generate gork for multiple data samples"""
        results = []
        
        for data in data_samples:
            gork_type = None
            if gork_types:
                gork_type = self.random.choice(gork_types)
            result = self.generate_gork(data, gork_type)
            results.append(result)
        
        return results
    
    def get_gork_severity(self, gork_type: GorkType) -> str:
        """Get severity level for a gork type"""
        high_severity = {
            GorkType.COMPRESSION_BOMB, GorkType.BUFFER_OVERFLOW, 
            GorkType.HEAP_CORRUPTION, GorkType.STACK_CORRUPTION,
            GorkType.USE_AFTER_FREE
        }
        
        medium_severity = {
            GorkType.PROTOBUF_CORRUPTION, GorkType.JSON_CORRUPTION,
            GorkType.INVALID_UTF8, GorkType.MIXED_ENCODING,
            GorkType.GZIP_CORRUPTION
        }
        
        if gork_type in high_severity:
            return "high"
        elif gork_type in medium_severity:
            return "medium"
        else:
            return "low"
    
    def generate_gork_test_suite(self, base_data: Any, 
                                include_categories: Optional[List[str]] = None) -> List[GorkResult]:
        """Generate a comprehensive test suite of gork patterns"""
        categories = {
            "binary_corruption": [
                GorkType.RANDOM_BINARY, GorkType.NULL_BYTE_INJECTION,
                GorkType.HIGH_BIT_SET, GorkType.BINARY_IN_TEXT
            ],
            "encoding_corruption": [
                GorkType.INVALID_UTF8, GorkType.MIXED_ENCODING,
                GorkType.OVERLONG_UTF8, GorkType.BOM_CORRUPTION
            ],
            "protocol_corruption": [
                GorkType.PROTOBUF_CORRUPTION, GorkType.JSON_CORRUPTION,
                GorkType.XML_CORRUPTION, GorkType.HTTP_HEADER_CORRUPTION
            ],
            "compression_corruption": [
                GorkType.GZIP_CORRUPTION, GorkType.COMPRESSION_BOMB
            ],
            "memory_corruption": [
                GorkType.HEAP_CORRUPTION, GorkType.BUFFER_OVERFLOW
            ]
        }
        
        if include_categories is None:
            include_categories = list(categories.keys())
        
        test_suite = []
        for category in include_categories:
            if category in categories:
                for gork_type in categories[category]:
                    result = self.generate_gork(base_data, gork_type)
                    test_suite.append(result)
        
        return test_suite
    
    def validate_gork(self, gork_result: GorkResult) -> bool:
        """Validate that gork was successfully generated"""
        return gork_result.gork_data != gork_result.original_data
    
    def get_recovery_suggestions(self, gork_type: GorkType) -> List[str]:
        """Get recovery suggestions for handling specific gork types"""
        suggestions = {
            GorkType.INVALID_UTF8: [
                "Implement UTF-8 validation before processing",
                "Use error handling for encoding issues",
                "Consider fallback encoding detection"
            ],
            GorkType.JSON_CORRUPTION: [
                "Add JSON schema validation",
                "Implement graceful JSON parsing fallbacks",
                "Log malformed JSON for analysis"
            ],
            GorkType.BUFFER_OVERFLOW: [
                "Implement bounds checking",
                "Use safe string handling functions",
                "Add input length validation"
            ]
        }
        return suggestions.get(gork_type, ["Review error handling for this corruption type"])
    
    def get_gork_statistics(self, results: List[GorkResult]) -> Dict[str, Any]:
        """Get statistics about generated gork"""
        if not results:
            return {}
        
        type_distribution = {}
        corruption_point_total = 0
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        
        for result in results:
            gork_type = result.gork_type.value
            type_distribution[gork_type] = type_distribution.get(gork_type, 0) + 1
            corruption_point_total += len(result.corruption_points)
            
            severity = self.get_gork_severity(result.gork_type)
            severity_counts[severity] += 1
        
        return {
            "gork_type_distribution": type_distribution,
            "corruption_point_average": corruption_point_total / len(results),
            "severity_distribution": severity_counts,
            "total_results": len(results)
        }
    
    # Gork generation strategy implementations
    
    def _generate_random_binary_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate random binary corruption"""
        if isinstance(data, str):
            # Inject random binary bytes
            data_bytes = data.encode('utf-8', errors='ignore')
            corrupted_bytes = bytearray(data_bytes)
            
            corruption_points = []
            for i in range(len(corrupted_bytes)):
                if self.random.random() < corruption_rate * 0.1:  # 10% of corruption rate
                    corrupted_bytes[i] = self.random.randint(0, 255)
                    corruption_points.append(f"byte_{i}")
            
            try:
                corrupted = corrupted_bytes.decode('utf-8', errors='replace')
            except:
                corrupted = str(corrupted_bytes)
            
            return corrupted, corruption_points, "Random binary corruption in text", ["encoding_error", "parsing_failure"]
        
        elif isinstance(data, dict):
            corrupted = data.copy()
            corrupted["_binary_corruption"] = self.random.choice(self.binary_patterns)
            return corrupted, ["binary_field"], "Added binary corruption field", ["serialization_error"]
        
        return data, [], "No corruption applied", []
    
    def _generate_null_byte_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate null byte injection"""
        if isinstance(data, str):
            # Inject null bytes at random positions
            corrupted = data
            injection_points = []
            
            for i in range(int(len(data) * corruption_rate)):
                pos = self.random.randint(0, len(corrupted))
                corrupted = corrupted[:pos] + '\\x00' + corrupted[pos:]
                injection_points.append(f"pos_{pos}")
            
            return corrupted, injection_points, "Null byte injection", ["string_termination", "parsing_error"]
        
        return data, [], "No null byte injection applied", []
    
    def _generate_high_bit_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate high bit corruption"""
        if isinstance(data, str):
            corrupted_chars = []
            corruption_points = []
            
            for i, char in enumerate(data):
                if self.random.random() < corruption_rate * 0.2:
                    # Set high bit
                    corrupted_char = chr(ord(char) | 0x80)
                    corrupted_chars.append(corrupted_char)
                    corruption_points.append(f"char_{i}")
                else:
                    corrupted_chars.append(char)
            
            return ''.join(corrupted_chars), corruption_points, "High bit corruption", ["encoding_error", "display_issues"]
        
        return data, [], "No high bit corruption applied", []
    
    def _generate_binary_in_text_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Inject binary data into text fields"""
        if isinstance(data, str):
            binary_pattern = self.random.choice(self.binary_patterns)
            insertion_point = self.random.randint(0, len(data))
            corrupted = data[:insertion_point] + binary_pattern.decode('latin-1', errors='ignore') + data[insertion_point:]
            
            return corrupted, [f"binary_at_{insertion_point}"], "Binary data in text", ["encoding_error", "protocol_violation"]
        
        return data, [], "No binary injection applied", []
    
    def _generate_invalid_utf8_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate invalid UTF-8 sequences"""
        if isinstance(data, str):
            invalid_seq = self.random.choice(self.invalid_utf8_sequences)
            insertion_point = self.random.randint(0, len(data))
            
            try:
                invalid_str = invalid_seq.decode('latin-1', errors='ignore')
                corrupted = data[:insertion_point] + invalid_str + data[insertion_point:]
                return corrupted, [f"invalid_utf8_at_{insertion_point}"], "Invalid UTF-8 sequences", ["encoding_error", "parsing_failure"]
            except:
                return data + "\\xff\\xfe", ["utf8_corruption"], "UTF-8 corruption", ["encoding_error"]
        
        return data, [], "No UTF-8 corruption applied", []
    
    def _generate_mixed_encoding_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate mixed encoding issues"""
        if isinstance(data, str):
            # Mix different encodings
            encodings = ['latin-1', 'cp1252', 'utf-16']
            mixed_parts = []
            corruption_points = []
            
            for i, char in enumerate(data):
                if self.random.random() < corruption_rate * 0.1:
                    encoding = self.random.choice(encodings)
                    try:
                        encoded = char.encode('utf-8')
                        decoded = encoded.decode(encoding, errors='ignore')
                        mixed_parts.append(decoded)
                        corruption_points.append(f"encoding_mix_{i}")
                    except:
                        mixed_parts.append(char)
                else:
                    mixed_parts.append(char)
            
            return ''.join(mixed_parts), corruption_points, "Mixed encoding corruption", ["encoding_mismatch", "display_corruption"]
        
        return data, [], "No mixed encoding applied", []
    
    def _generate_overlong_utf8_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate overlong UTF-8 sequences"""
        if isinstance(data, str):
            # Insert overlong encoding sequences
            overlong_null = "\\xc0\\x80"  # Overlong encoding of NULL
            insertion_point = self.random.randint(0, len(data))
            corrupted = data[:insertion_point] + overlong_null + data[insertion_point:]
            
            return corrupted, [f"overlong_at_{insertion_point}"], "Overlong UTF-8 encoding", ["security_bypass", "encoding_error"]
        
        return data, [], "No overlong UTF-8 applied", []
    
    def _generate_surrogate_pairs_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate invalid surrogate pairs"""
        if isinstance(data, str):
            # Insert unpaired surrogates
            high_surrogate = "\\ud800"  # High surrogate without pair
            low_surrogate = "\\udc00"   # Low surrogate without pair
            
            corrupted = data + high_surrogate + low_surrogate
            return corrupted, ["unpaired_surrogates"], "Invalid surrogate pairs", ["unicode_error", "encoding_error"]
        
        return data, [], "No surrogate pair corruption applied", []
    
    def _generate_bom_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate BOM corruption"""
        if isinstance(data, str):
            # Insert BOM in wrong places
            bom_utf8 = "\\ufeff"
            bom_utf16_be = "\\ufffe"
            
            bom = self.random.choice([bom_utf8, bom_utf16_be])
            insertion_point = self.random.randint(0, len(data))
            corrupted = data[:insertion_point] + bom + data[insertion_point:]
            
            return corrupted, [f"bom_at_{insertion_point}"], "BOM corruption", ["encoding_detection_error", "parsing_error"]
        
        return data, [], "No BOM corruption applied", []
    
    def _generate_protobuf_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate protobuf corruption"""
        protobuf_like = "\\x08\\x96\\x01\\x12\\x04\\x08\\xac\\x02"
        
        if isinstance(data, dict):
            corrupted = data.copy()
            corrupted["_protobuf_corruption"] = protobuf_like
            return corrupted, ["protobuf_field"], "Protobuf corruption", ["deserialization_error", "protocol_error"]
        elif isinstance(data, str):
            corrupted = data + protobuf_like
            return corrupted, ["protobuf_suffix"], "Protobuf corruption in text", ["parsing_error"]
        
        return data, [], "No protobuf corruption applied", []
    
    def _generate_json_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate JSON corruption"""
        if isinstance(data, dict):
            # Convert to JSON and corrupt it
            json_str = json.dumps(data)
            
            corruptions = [
                lambda s: s.replace(',', ',,'),
                lambda s: s.replace('{', '{{'),
                lambda s: s.replace('"', "'"),
                lambda s: s[:-1],  # Remove closing brace
                lambda s: s + ',',  # Trailing comma
                lambda s: s.replace('true', 'True'),
                lambda s: s.replace('null', 'None'),
            ]
            
            corruption_func = self.random.choice(corruptions)
            corrupted_json = corruption_func(json_str)
            
            return corrupted_json, ["json_structure"], "JSON corruption", ["json_parse_error", "syntax_error"]
        
        return data, [], "No JSON corruption applied", []
    
    def _generate_xml_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate XML corruption"""
        xml_corruptions = [
            "<tag>unclosed",
            "<tag attribute=no_quotes>",
            "<?xml version='1.0' encoding='invalid'?>",
            "<root><nested></root>",  # Mismatched tags
            "<tag>&invalid_entity;</tag>"
        ]
        
        corruption = self.random.choice(xml_corruptions)
        
        if isinstance(data, str):
            corrupted = data + corruption
            return corrupted, ["xml_corruption"], "XML corruption", ["xml_parse_error", "syntax_error"]
        
        return corruption, ["xml_structure"], "XML corruption", ["xml_parse_error"]
    
    def _generate_http_header_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate HTTP header corruption"""
        header_corruptions = [
            "Content-Length: -1\\r\\n",
            "Transfer-Encoding: chunked\\r\\nContent-Length: 100\\r\\n",  # Conflicting headers
            "Content-Type: text/html\\x00\\r\\n",  # Null byte in header
            "Header-Name\\x0d\\x0aInjected: value\\r\\n",  # Header injection
        ]
        
        corruption = self.random.choice(header_corruptions)
        
        if isinstance(data, str):
            corrupted = data + corruption
            return corrupted, ["http_header"], "HTTP header corruption", ["http_parse_error", "protocol_violation"]
        
        return corruption, ["http_structure"], "HTTP header corruption", ["http_parse_error"]
    
    def _generate_gzip_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate GZIP corruption"""
        if isinstance(data, str):
            try:
                # Compress and then corrupt
                compressed = zlib.compress(data.encode('utf-8'))
                corrupted_compressed = bytearray(compressed)
                
                # Corrupt random bytes
                for i in range(min(5, len(corrupted_compressed))):
                    if self.random.random() < corruption_rate:
                        corrupted_compressed[i] = self.random.randint(0, 255)
                
                return bytes(corrupted_compressed), [f"gzip_byte_{i}" for i in range(5)], "GZIP corruption", ["decompression_error", "checksum_mismatch"]
            except:
                pass
        
        # Fallback: invalid GZIP header
        invalid_gzip = "\\x1f\\x8b\\x08\\xff"  # Invalid GZIP header
        return invalid_gzip, ["gzip_header"], "Invalid GZIP header", ["decompression_error"]
    
    def _generate_deflate_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate DEFLATE corruption"""
        # Similar to GZIP but without header
        if isinstance(data, str):
            try:
                compressed = zlib.compress(data.encode('utf-8'))[2:-4]  # Remove header/trailer
                corrupted = bytearray(compressed)
                
                for i in range(min(3, len(corrupted))):
                    if self.random.random() < corruption_rate:
                        corrupted[i] = self.random.randint(0, 255)
                
                return bytes(corrupted), ["deflate_corruption"], "DEFLATE corruption", ["decompression_error"]
            except:
                pass
        
        return "corrupted_deflate_data", ["deflate_structure"], "DEFLATE corruption", ["decompression_error"]
    
    def _generate_compression_bomb_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate compression bomb"""
        # Create highly compressible data that expands dramatically
        bomb_data = "A" * 100000  # 100KB of repeated character
        
        try:
            compressed = zlib.compress(bomb_data.encode('utf-8'))
            return compressed, ["compression_bomb"], "Compression bomb", ["resource_exhaustion", "memory_explosion"]
        except:
            return bomb_data, ["large_expansion"], "Potential compression bomb", ["resource_exhaustion"]
    
    # Network corruption methods (simplified implementations)
    def _generate_packet_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate packet-level corruption"""
        return f"PACKET_CORRUPTED_{data}", ["packet_header"], "Packet corruption", ["network_error", "checksum_failure"]
    
    def _generate_tcp_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate TCP-level corruption"""
        return f"TCP_CORRUPTED_{data}", ["tcp_header"], "TCP corruption", ["connection_error", "retransmission"]
    
    def _generate_ethernet_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate Ethernet-level corruption"""
        return f"ETH_CORRUPTED_{data}", ["ethernet_frame"], "Ethernet corruption", ["frame_error", "crc_mismatch"]
    
    # File system corruption methods
    def _generate_inode_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate inode corruption"""
        return f"INODE_CORRUPTED_{data}", ["inode_table"], "Inode corruption", ["filesystem_error", "file_access_denied"]
    
    def _generate_metadata_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate metadata corruption"""
        return f"METADATA_CORRUPTED_{data}", ["file_metadata"], "Metadata corruption", ["stat_error", "permission_error"]
    
    def _generate_block_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate block-level corruption"""
        return f"BLOCK_CORRUPTED_{data}", ["disk_block"], "Block corruption", ["io_error", "data_loss"]
    
    # Memory corruption methods
    def _generate_heap_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate heap corruption simulation"""
        return f"HEAP_CORRUPTED_{data}_{'X' * 10000}", ["heap_overflow"], "Heap corruption", ["memory_error", "segmentation_fault"]
    
    def _generate_stack_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate stack corruption simulation"""
        return f"STACK_CORRUPTED_{data}_{'Y' * 5000}", ["stack_overflow"], "Stack corruption", ["stack_overflow", "program_crash"]
    
    def _generate_buffer_overflow_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate buffer overflow simulation"""
        overflow_data = str(data) + "Z" * 50000  # Simulate large overflow
        return overflow_data, ["buffer_bounds"], "Buffer overflow", ["memory_corruption", "security_vulnerability"]
    
    def _generate_use_after_free_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate use-after-free simulation"""
        return f"USE_AFTER_FREE_{data}_FREED_MEMORY", ["freed_pointer"], "Use after free", ["memory_corruption", "undefined_behavior"]
    
    # Format corruption methods
    def _generate_base64_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate Base64 corruption"""
        if isinstance(data, str):
            # Encode to base64 and corrupt
            encoded = base64.b64encode(data.encode('utf-8')).decode('ascii')
            corrupted = encoded.replace('A', '@').replace('=', '#')  # Invalid base64 chars
            return corrupted, ["base64_chars"], "Base64 corruption", ["decoding_error", "invalid_padding"]
        
        return "SW52YWxpZCBCYXNlNjQ@", ["base64_format"], "Invalid Base64", ["decoding_error"]
    
    def _generate_hex_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate hex encoding corruption"""
        if isinstance(data, str):
            hex_encoded = data.encode('utf-8').hex()
            corrupted = hex_encoded.replace('a', 'g').replace('f', 'z')  # Invalid hex chars
            return corrupted, ["hex_chars"], "Hex corruption", ["hex_decode_error"]
        
        return "48656c6c6fG", ["hex_format"], "Invalid hex", ["hex_decode_error"]
    
    def _generate_url_encoding_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate URL encoding corruption"""
        corrupted_url = f"%GG%HH%II{data}%ZZ"  # Invalid percent encoding
        return corrupted_url, ["url_encoding"], "URL encoding corruption", ["url_decode_error", "invalid_percent_encoding"]
    
    # Unicode corruption methods
    def _generate_unicode_direction_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate Unicode direction corruption"""
        if isinstance(data, str):
            direction_char = self.random.choice(self.unicode_corruption)
            corrupted = direction_char + data + direction_char
            return corrupted, ["unicode_direction"], "Unicode direction corruption", ["display_corruption", "text_rendering_error"]
        
        return data, [], "No Unicode direction corruption applied", []
    
    def _generate_zero_width_chars_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate zero-width character corruption"""
        if isinstance(data, str):
            zw_char = self.random.choice(self.zero_width_chars)
            # Insert zero-width chars randomly
            corrupted = ""
            for char in data:
                corrupted += char
                if self.random.random() < corruption_rate * 0.3:
                    corrupted += zw_char
            
            return corrupted, ["zero_width_insertion"], "Zero-width character corruption", ["display_issues", "length_mismatch"]
        
        return data, [], "No zero-width corruption applied", []
    
    def _generate_combining_chars_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate combining character corruption"""
        combining_chars = ['\\u0300', '\\u0301', '\\u0302', '\\u0303']  # Combining diacriticals
        
        if isinstance(data, str):
            corrupted = ""
            for char in data:
                corrupted += char
                if self.random.random() < corruption_rate * 0.2:
                    corrupted += self.random.choice(combining_chars)
            
            return corrupted, ["combining_chars"], "Combining character corruption", ["normalization_issues", "display_corruption"]
        
        return data, [], "No combining character corruption applied", []
    
    # Time corruption methods
    def _generate_epoch_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate epoch time corruption"""
        epoch_corruptions = [
            "2147483648",  # 32-bit overflow
            "-1",  # Negative time
            "253402300800",  # Year 9999
            "invalid_epoch"
        ]
        
        corruption = self.random.choice(epoch_corruptions)
        
        if isinstance(data, dict):
            corrupted = data.copy()
            corrupted["timestamp"] = corruption
            return corrupted, ["timestamp_field"], "Epoch corruption", ["time_parse_error", "overflow_error"]
        
        return corruption, ["epoch_value"], "Epoch corruption", ["time_error"]
    
    def _generate_timezone_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate timezone corruption"""
        tz_corruptions = [
            "2023-01-01T12:00:00+99:99",  # Invalid timezone
            "2023-01-01T12:00:00Z+05:00",  # Conflicting timezone
            "2023-01-01T25:61:61Z",  # Invalid time components
        ]
        
        corruption = self.random.choice(tz_corruptions)
        return corruption, ["timezone_format"], "Timezone corruption", ["datetime_parse_error", "timezone_error"]
    
    # Cryptographic corruption methods
    def _generate_hash_collision_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate hash collision simulation"""
        # Simulate hash collision scenario
        collision_data = f"HASH_COLLISION_{data}_COLLIDING_DATA"
        return collision_data, ["hash_collision"], "Hash collision", ["integrity_check_failure", "security_breach"]
    
    def _generate_signature_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate signature corruption"""
        corrupted_sig = f"CORRUPTED_SIGNATURE_{data}"
        return corrupted_sig, ["digital_signature"], "Signature corruption", ["signature_verification_failure", "authenticity_error"]
    
    def _generate_certificate_corruption_gork(self, data: Any, corruption_rate: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate certificate corruption"""
        corrupted_cert = f"-----BEGIN CORRUPTED CERTIFICATE-----\\n{data}\\n-----END CORRUPTED CERTIFICATE-----"
        return corrupted_cert, ["x509_certificate"], "Certificate corruption", ["certificate_parse_error", "ssl_handshake_failure"]
        
        # Common protocol corruption patterns
        self.protocol_corruptions = {
            'http': [
                'Content-Length: -1\\r\\n',
                'Transfer-Encoding: chunked\\r\\nContent-Length: 100\\r\\n',
                'Host: \\x00\\x01\\x02\\r\\n',
            ],
            'json': [
                '{,}',  # Invalid comma
                '{"key":}',  # Missing value
                '{"key": "value",}',  # Trailing comma
                '{key: "value"}',  # Unquoted key
            ],
            'xml': [
                '<?xml version="1.0"?><root><unclosed>',
                '<root xmlns:ns=""><ns:tag></tag></root>',  # Namespace mismatch
                '<root>\\x00\\x01\\x02</root>',  # Binary in XML
            ]
        }
        
        # Gork generation strategies
        self.gork_strategies = {
            GorkType.RANDOM_BINARY: self._generate_random_binary,
            GorkType.NULL_BYTE_INJECTION: self._generate_null_byte_injection,
            GorkType.HIGH_BIT_SET: self._generate_high_bit_set,
            GorkType.BINARY_IN_TEXT: self._generate_binary_in_text,
            GorkType.INVALID_UTF8: self._generate_invalid_utf8,
            GorkType.MIXED_ENCODING: self._generate_mixed_encoding,
            GorkType.OVERLONG_UTF8: self._generate_overlong_utf8,
            GorkType.SURROGATE_PAIRS: self._generate_surrogate_pairs,
            GorkType.BOM_CORRUPTION: self._generate_bom_corruption,
            GorkType.PROTOBUF_CORRUPTION: self._generate_protobuf_corruption,
            GorkType.JSON_CORRUPTION: self._generate_json_corruption,
            GorkType.XML_CORRUPTION: self._generate_xml_corruption,
            GorkType.HTTP_HEADER_CORRUPTION: self._generate_http_header_corruption,
            GorkType.GZIP_CORRUPTION: self._generate_gzip_corruption,
            GorkType.DEFLATE_CORRUPTION: self._generate_deflate_corruption,
            GorkType.COMPRESSION_BOMB: self._generate_compression_bomb,
            GorkType.PACKET_CORRUPTION: self._generate_packet_corruption,
            GorkType.TCP_CORRUPTION: self._generate_tcp_corruption,
            GorkType.ETHERNET_CORRUPTION: self._generate_ethernet_corruption,
            GorkType.INODE_CORRUPTION: self._generate_inode_corruption,
            GorkType.METADATA_CORRUPTION: self._generate_metadata_corruption,
            GorkType.BLOCK_CORRUPTION: self._generate_block_corruption,
            GorkType.HEAP_CORRUPTION: self._generate_heap_corruption,
            GorkType.STACK_CORRUPTION: self._generate_stack_corruption,
            GorkType.BUFFER_OVERFLOW: self._generate_buffer_overflow,
            GorkType.USE_AFTER_FREE: self._generate_use_after_free,
            GorkType.BASE64_CORRUPTION: self._generate_base64_corruption,
            GorkType.HEX_CORRUPTION: self._generate_hex_corruption,
            GorkType.URL_ENCODING_CORRUPTION: self._generate_url_encoding_corruption,
            GorkType.UNICODE_DIRECTION: self._generate_unicode_direction,
            GorkType.ZERO_WIDTH_CHARS: self._generate_zero_width_chars,
            GorkType.COMBINING_CHARS: self._generate_combining_chars,
            GorkType.EPOCH_CORRUPTION: self._generate_epoch_corruption,
            GorkType.TIMEZONE_CORRUPTION: self._generate_timezone_corruption,
            GorkType.HASH_COLLISION: self._generate_hash_collision,
            GorkType.SIGNATURE_CORRUPTION: self._generate_signature_corruption,
            GorkType.CERTIFICATE_CORRUPTION: self._generate_certificate_corruption,
        }
    
    def generate_gork(self, 
                     original_data: Any,
                     gork_types: Optional[List[GorkType]] = None,
                     intensity: float = 0.5) -> GorkResult:
        """
        Generate gork (garbled data) from original data.
        
        Args:
            original_data: Original data to corrupt
            gork_types: Types of corruption to apply
            intensity: Corruption intensity (0.0-1.0)
            
        Returns:
            GorkResult with corrupted data
        """
        if gork_types is None:
            gork_types = list(GorkType)
        
        # Select random gork type
        gork_type = self.random.choice(gork_types)
        
        # Apply corruption strategy
        strategy = self.gork_strategies[gork_type]
        gork_data, corruption_points, description, expected_failures = strategy(original_data, intensity)
        
        return GorkResult(
            gork_type=gork_type,
            original_data=original_data,
            gork_data=gork_data,
            corruption_points=corruption_points,
            description=description,
            expected_failures=expected_failures
        )
    
    def generate_gork_suite(self, base_data: Any) -> Dict[str, GorkResult]:
        """
        Generate a comprehensive suite of gork patterns.
        
        Args:
            base_data: Base data to corrupt in various ways
            
        Returns:
            Dictionary mapping gork type names to GorkResults
        """
        suite = {}
        
        for gork_type in GorkType:
            try:
                result = self.generate_gork(base_data, [gork_type], intensity=0.8)
                suite[gork_type.value] = result
            except Exception as e:
                # Some gork types might not be applicable to all data types
                continue
        
        return suite
    
    # Gork generation strategies
    
    def _generate_random_binary(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate random binary corruption"""
        if isinstance(data, str):
            # Inject random binary bytes
            corruption_length = max(1, int(len(data) * intensity * 0.1))
            corruption_pos = self.random.randint(0, len(data))
            
            binary_bytes = bytes([self.random.randint(0, 255) for _ in range(corruption_length)])
            binary_str = ''.join([f'\\\\x{b:02x}' for b in binary_bytes])
            
            gork_data = data[:corruption_pos] + binary_str + data[corruption_pos:]
            
            return (
                gork_data,
                [f"binary_injection_{corruption_pos}"],
                f"Injected {corruption_length} random binary bytes at position {corruption_pos}",
                ["encoding_error", "unicode_decode_error", "invalid_character"]
            )
        
        elif isinstance(data, dict):
            # Add binary field
            gork_data = data.copy()
            binary_bytes = bytes([self.random.randint(0, 255) for _ in range(int(20 * intensity))])
            gork_data["__binary_corruption__"] = binary_bytes
            
            return (
                gork_data,
                ["binary_field_added"],
                "Added binary data field to dictionary",
                ["serialization_error", "json_encode_error"]
            )
        
        return data, [], "No corruption applied", []
    
    def _generate_null_byte_injection(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Inject null bytes"""
        if isinstance(data, str):
            # Inject null bytes at random positions
            injection_count = max(1, int(len(data) * intensity * 0.05))
            gork_data = data
            positions = []
            
            for _ in range(injection_count):
                pos = self.random.randint(0, len(gork_data))
                gork_data = gork_data[:pos] + '\\x00' + gork_data[pos:]
                positions.append(pos)
            
            return (
                gork_data,
                [f"null_byte_{pos}" for pos in positions],
                f"Injected {injection_count} null bytes",
                ["string_truncation", "c_string_termination", "security_bypass"]
            )
        
        return data, [], "No null byte injection applied", []
    
    def _generate_high_bit_set(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Set high bits in byte sequences"""
        if isinstance(data, str):
            # Convert some characters to high-bit variants
            gork_data = ""
            corruptions = []
            
            for i, char in enumerate(data):
                if self.random.random() < intensity * 0.1:
                    # Set high bit
                    high_bit_char = chr(ord(char) | 0x80)
                    gork_data += high_bit_char
                    corruptions.append(f"high_bit_{i}")
                else:
                    gork_data += char
            
            return (
                gork_data,
                corruptions,
                f"Set high bits on {len(corruptions)} characters",
                ["ascii_decode_error", "encoding_mismatch"]
            )
        
        return data, [], "No high bit corruption applied", []
    
    def _generate_binary_in_text(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Inject binary patterns into text data"""
        if isinstance(data, str):
            pattern = self.random.choice(self.binary_patterns)
            pattern_str = pattern.decode('latin-1', errors='replace')
            
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + pattern_str + data[pos:]
            
            return (
                gork_data,
                [f"binary_pattern_{pos}"],
                f"Injected binary pattern {pattern} at position {pos}",
                ["binary_in_text_field", "rendering_corruption"]
            )
        
        return data, [], "No binary injection applied", []
    
    def _generate_invalid_utf8(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate invalid UTF-8 sequences"""
        if isinstance(data, str):
            sequence = self.random.choice(self.invalid_utf8_sequences)
            sequence_str = sequence.decode('latin-1', errors='replace')
            
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + sequence_str + data[pos:]
            
            return (
                gork_data,
                [f"invalid_utf8_{pos}"],
                f"Injected invalid UTF-8 sequence at position {pos}",
                ["utf8_decode_error", "mojibake", "character_replacement"]
            )
        
        return data, [], "No UTF-8 corruption applied", []
    
    def _generate_mixed_encoding(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Mix different text encodings"""
        if isinstance(data, str):
            # Create mixed encoding nightmare
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            mixed_parts = []
            current_pos = 0
            
            while current_pos < len(data):
                chunk_size = min(10, len(data) - current_pos)
                chunk = data[current_pos:current_pos + chunk_size]
                
                if self.random.random() < intensity:
                    # Encode with random encoding, decode with different one
                    encoding1 = self.random.choice(encodings)
                    encoding2 = self.random.choice(encodings)
                    
                    try:
                        # This creates encoding corruption
                        corrupted = chunk.encode(encoding1, errors='replace').decode(encoding2, errors='replace')
                        mixed_parts.append(corrupted)
                    except:
                        mixed_parts.append(chunk)
                else:
                    mixed_parts.append(chunk)
                
                current_pos += chunk_size
            
            gork_data = ''.join(mixed_parts)
            
            return (
                gork_data,
                ["mixed_encoding"],
                "Applied mixed encoding corruption",
                ["mojibake", "character_corruption", "encoding_detection_failure"]
            )
        
        return data, [], "No encoding mixing applied", []
    
    def _generate_overlong_utf8(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate overlong UTF-8 encodings"""
        if isinstance(data, str):
            # Replace some ASCII chars with overlong encodings
            gork_data = ""
            corruptions = []
            
            for i, char in enumerate(data):
                if self.random.random() < intensity * 0.1 and ord(char) < 128:
                    # Create overlong encoding (security vulnerability)
                    overlong = f"\\xc{1 + (ord(char) >> 6):x}\\x{0x80 + (ord(char) & 0x3f):02x}"
                    gork_data += overlong
                    corruptions.append(f"overlong_{i}")
                else:
                    gork_data += char
            
            return (
                gork_data,
                corruptions,
                f"Created {len(corruptions)} overlong UTF-8 sequences",
                ["security_bypass", "utf8_validation_bypass", "path_traversal"]
            )
        
        return data, [], "No overlong UTF-8 applied", []
    
    def _generate_surrogate_pairs(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate invalid surrogate pairs"""
        if isinstance(data, str):
            # Inject invalid surrogate sequences
            invalid_surrogates = [
                '\\ud800',  # High surrogate without low
                '\\udc00',  # Low surrogate without high
                '\\ud800\\ud800',  # Double high surrogate
                '\\udc00\\udc00',  # Double low surrogate
            ]
            
            surrogate = self.random.choice(invalid_surrogates)
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + surrogate + data[pos:]
            
            return (
                gork_data,
                [f"invalid_surrogate_{pos}"],
                f"Injected invalid surrogate at position {pos}",
                ["surrogate_decode_error", "unicode_normalization_error"]
            )
        
        return data, [], "No surrogate corruption applied", []
    
    def _generate_bom_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt with byte order marks"""
        if isinstance(data, str):
            # Insert BOMs at random positions
            boms = [
                '\\ufeff',  # UTF-8 BOM
                '\\ufffe',  # UTF-16 LE BOM
                '\\u0000\\ufeff',  # UTF-32 BE BOM
            ]
            
            bom = self.random.choice(boms)
            insertion_count = max(1, int(intensity * 3))
            
            gork_data = data
            positions = []
            
            for _ in range(insertion_count):
                pos = self.random.randint(0, len(gork_data))
                gork_data = gork_data[:pos] + bom + gork_data[pos:]
                positions.append(pos)
            
            return (
                gork_data,
                [f"bom_{pos}" for pos in positions],
                f"Injected {insertion_count} BOMs",
                ["bom_handling_error", "text_rendering_corruption"]
            )
        
        return data, [], "No BOM corruption applied", []
    
    def _generate_protobuf_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate corrupted protobuf-like data"""
        if isinstance(data, dict):
            # Create protobuf-style corruption
            protobuf_corruption = {
                "__proto_field_1__": b"\\x08\\x96\\x01",  # Invalid varint
                "__proto_field_2__": b"\\x12\\x04\\x08\\xac\\x02",  # Malformed message
                "__proto_field_3__": b"\\x1a\\xff\\xff\\xff\\xff\\x0f",  # Invalid length
                "__proto_unknown_field__": b"\\xf8\\x7f\\x01",  # Unknown field
            }
            
            gork_data = data.copy()
            gork_data.update(protobuf_corruption)
            
            return (
                gork_data,
                list(protobuf_corruption.keys()),
                "Added protobuf corruption fields",
                ["protobuf_decode_error", "message_parsing_error"]
            )
        
        return data, [], "No protobuf corruption applied", []
    
    def _generate_json_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate JSON corruption"""
        if isinstance(data, (dict, list)):
            # Convert to JSON and corrupt
            try:
                json_str = json.dumps(data)
                corruptions = self.protocol_corruptions['json']
                corruption = self.random.choice(corruptions)
                
                # Insert corruption at random position
                pos = self.random.randint(0, len(json_str))
                gork_json = json_str[:pos] + corruption + json_str[pos:]
                
                return (
                    gork_json,
                    [f"json_corruption_{pos}"],
                    f"Injected JSON corruption: {corruption}",
                    ["json_parse_error", "syntax_error", "unexpected_token"]
                )
            except:
                pass
        
        return data, [], "No JSON corruption applied", []
    
    def _generate_xml_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate XML corruption"""
        if isinstance(data, str) and ('<' in data or 'xml' in data.lower()):
            corruptions = self.protocol_corruptions['xml']
            corruption = self.random.choice(corruptions)
            
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + corruption + data[pos:]
            
            return (
                gork_data,
                [f"xml_corruption_{pos}"],
                f"Injected XML corruption: {corruption}",
                ["xml_parse_error", "malformed_markup", "namespace_error"]
            )
        
        return data, [], "No XML corruption applied", []
    
    def _generate_http_header_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate HTTP header corruption"""
        if isinstance(data, dict):
            # Add corrupted HTTP-like headers
            header_corruptions = {
                "Content-Length": "-1",
                "Transfer-Encoding": "chunked\\r\\nContent-Length: 100",
                "Host": "\\x00\\x01\\x02.example.com",
                "User-Agent": "Mozilla/5.0\\x00(corruption)",
                "Authorization": "Bearer \\xff\\xfe\\x00\\x00invalid",
            }
            
            gork_data = data.copy()
            for header, corrupt_value in header_corruptions.items():
                if self.random.random() < intensity:
                    gork_data[f"__http_{header.lower()}__"] = corrupt_value
            
            return (
                gork_data,
                list(header_corruptions.keys()),
                "Added HTTP header corruptions",
                ["http_parse_error", "header_injection", "protocol_violation"]
            )
        
        return data, [], "No HTTP corruption applied", []
    
    def _generate_gzip_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate GZIP corruption"""
        if isinstance(data, (str, bytes)):
            try:
                # Create valid gzip, then corrupt it
                if isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                else:
                    data_bytes = data
                
                compressed = zlib.compress(data_bytes)
                
                # Corrupt random bytes
                corruption_count = max(1, int(len(compressed) * intensity * 0.1))
                corrupted = bytearray(compressed)
                
                for _ in range(corruption_count):
                    pos = self.random.randint(0, len(corrupted) - 1)
                    corrupted[pos] = self.random.randint(0, 255)
                
                return (
                    bytes(corrupted),
                    [f"gzip_corruption_{corruption_count}_bytes"],
                    f"Corrupted {corruption_count} bytes in GZIP data",
                    ["decompression_error", "crc_mismatch", "truncated_data"]
                )
            except:
                pass
        
        return data, [], "No GZIP corruption applied", []
    
    def _generate_deflate_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate deflate corruption"""
        return self._generate_gzip_corruption(data, intensity)  # Similar to GZIP
    
    def _generate_compression_bomb(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate compression bomb"""
        # Create highly compressible data that expands enormously
        bomb_size = int(1000000 * intensity)  # Up to 1MB of repeated data
        bomb_data = "A" * bomb_size
        
        try:
            compressed = zlib.compress(bomb_data.encode('utf-8'))
            
            return (
                compressed,
                [f"compression_bomb_{bomb_size}_bytes"],
                f"Created compression bomb: {len(compressed)} -> {bomb_size} bytes",
                ["memory_exhaustion", "dos_attack", "resource_consumption"]
            )
        except:
            return data, [], "No compression bomb created", []
    
    def _generate_packet_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate network packet corruption"""
        if isinstance(data, (str, bytes)):
            # Simulate bit flips that could occur during network transmission
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            corrupted = bytearray(data_bytes)
            bit_flips = max(1, int(len(corrupted) * intensity * 0.01))
            
            for _ in range(bit_flips):
                byte_pos = self.random.randint(0, len(corrupted) - 1)
                bit_pos = self.random.randint(0, 7)
                corrupted[byte_pos] ^= (1 << bit_pos)
            
            if isinstance(data, str):
                try:
                    result = corrupted.decode('utf-8', errors='replace')
                except:
                    result = str(corrupted)
            else:
                result = bytes(corrupted)
            
            return (
                result,
                [f"packet_corruption_{bit_flips}_bits"],
                f"Simulated {bit_flips} bit flips from network corruption",
                ["checksum_error", "bit_error", "network_corruption"]
            )
        
        return data, [], "No packet corruption applied", []
    
    def _generate_tcp_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate TCP-level corruption"""
        # Similar to packet corruption but with TCP-specific patterns
        return self._generate_packet_corruption(data, intensity)
    
    def _generate_ethernet_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate Ethernet frame corruption"""
        # Ethernet-level corruption (similar to packet)
        return self._generate_packet_corruption(data, intensity)
    
    def _generate_inode_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate filesystem inode corruption"""
        if isinstance(data, dict):
            inode_corruption = {
                "__inode_number__": -1,  # Invalid inode
                "__file_size__": 2**64,  # Impossible size
                "__link_count__": -1,  # Invalid link count
                "__permissions__": 777777,  # Invalid permissions
                "__timestamp__": -1,  # Invalid timestamp
            }
            
            gork_data = data.copy()
            gork_data.update(inode_corruption)
            
            return (
                gork_data,
                list(inode_corruption.keys()),
                "Added filesystem inode corruption",
                ["filesystem_error", "metadata_corruption", "file_access_error"]
            )
        
        return data, [], "No inode corruption applied", []
    
    def _generate_metadata_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate metadata corruption"""
        return self._generate_inode_corruption(data, intensity)  # Similar concept
    
    def _generate_block_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate disk block corruption"""
        if isinstance(data, (str, bytes)):
            # Simulate bad sectors/blocks
            block_size = 512  # Typical disk block size
            
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            if len(data_bytes) >= block_size:
                # Corrupt entire blocks
                corrupted = bytearray(data_bytes)
                blocks_to_corrupt = max(1, int((len(data_bytes) // block_size) * intensity))
                
                for _ in range(blocks_to_corrupt):
                    block_start = self.random.randint(0, len(data_bytes) - block_size)
                    block_start = (block_start // block_size) * block_size  # Align to block
                    
                    # Zero out the block (simulating bad sector)
                    for i in range(block_size):
                        if block_start + i < len(corrupted):
                            corrupted[block_start + i] = 0
                
                if isinstance(data, str):
                    result = corrupted.decode('utf-8', errors='replace')
                else:
                    result = bytes(corrupted)
                
                return (
                    result,
                    [f"block_corruption_{blocks_to_corrupt}_blocks"],
                    f"Corrupted {blocks_to_corrupt} disk blocks",
                    ["bad_sector", "data_loss", "disk_error"]
                )
        
        return data, [], "No block corruption applied", []
    
    def _generate_heap_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate heap memory corruption"""
        if isinstance(data, dict):
            # Add heap corruption markers
            heap_corruption = {
                "__heap_canary__": "DEADBEEF",  # Corrupted canary
                "__heap_metadata__": b"\\x00\\x00\\x00\\x00",  # Null metadata
                "__free_list_ptr__": 0xDEADBEEF,  # Invalid pointer
                "__chunk_size__": -1,  # Invalid size
            }
            
            gork_data = data.copy()
            gork_data.update(heap_corruption)
            
            return (
                gork_data,
                list(heap_corruption.keys()),
                "Added heap corruption markers",
                ["heap_corruption", "memory_error", "segmentation_fault"]
            )
        
        return data, [], "No heap corruption applied", []
    
    def _generate_stack_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate stack corruption"""
        if isinstance(data, list):
            # Corrupt list structure to simulate stack corruption
            gork_data = data.copy()
            
            # Add invalid stack frames
            stack_corruption = [
                {"return_address": 0xDEADBEEF, "frame_pointer": None},
                {"return_address": -1, "frame_pointer": "invalid"},
                "CORRUPTED_FRAME",  # Invalid frame type
            ]
            
            # Insert at random positions
            for corruption in stack_corruption:
                if gork_data:
                    pos = self.random.randint(0, len(gork_data))
                    gork_data.insert(pos, corruption)
            
            return (
                gork_data,
                ["stack_corruption"],
                "Added stack corruption frames",
                ["stack_overflow", "return_address_corruption", "buffer_overflow"]
            )
        
        return data, [], "No stack corruption applied", []
    
    def _generate_buffer_overflow(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate buffer overflow"""
        if isinstance(data, str):
            # Create extremely long string to simulate overflow
            overflow_size = int(65536 * intensity)  # Up to 64KB overflow
            overflow_data = "A" * overflow_size
            
            gork_data = data + overflow_data
            
            return (
                gork_data,
                [f"buffer_overflow_{overflow_size}"],
                f"Added buffer overflow of {overflow_size} bytes",
                ["buffer_overflow", "memory_corruption", "code_execution"]
            )
        
        return data, [], "No buffer overflow applied", []
    
    def _generate_use_after_free(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Simulate use-after-free corruption"""
        if isinstance(data, dict):
            # Add markers that simulate freed memory being accessed
            uaf_corruption = {
                "__freed_ptr__": 0xFEEDFACE,  # Freed memory marker
                "__freed_size__": 0,  # Size of freed block
                "__freed_data__": "\\xde\\xad\\xbe\\xef" * int(10 * intensity),  # Freed memory pattern
            }
            
            gork_data = data.copy()
            gork_data.update(uaf_corruption)
            
            return (
                gork_data,
                list(uaf_corruption.keys()),
                "Added use-after-free corruption markers",
                ["use_after_free", "memory_corruption", "dangling_pointer"]
            )
        
        return data, [], "No use-after-free corruption applied", []
    
    def _generate_base64_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt base64 encoding"""
        if isinstance(data, str):
            # Create base64, then corrupt it
            try:
                encoded = base64.b64encode(data.encode('utf-8')).decode('ascii')
                
                # Corrupt random characters
                corrupted_chars = []
                gork_list = list(encoded)
                
                corruption_count = max(1, int(len(encoded) * intensity * 0.1))
                
                for _ in range(corruption_count):
                    pos = self.random.randint(0, len(gork_list) - 1)
                    original = gork_list[pos]
                    
                    # Replace with invalid base64 characters
                    invalid_chars = ['!', '@', '#', '$', '%', '^', '&', '*']
                    gork_list[pos] = self.random.choice(invalid_chars)
                    corrupted_chars.append(f"{pos}:{original}->{gork_list[pos]}")
                
                gork_data = ''.join(gork_list)
                
                return (
                    gork_data,
                    corrupted_chars,
                    f"Corrupted {corruption_count} base64 characters",
                    ["base64_decode_error", "invalid_character", "padding_error"]
                )
            except:
                pass
        
        return data, [], "No base64 corruption applied", []
    
    def _generate_hex_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt hexadecimal encoding"""
        if isinstance(data, str) and all(c in '0123456789abcdefABCDEF' for c in data.replace(' ', '')):
            # Corrupt hex string
            gork_list = list(data)
            corruptions = []
            
            corruption_count = max(1, int(len(data) * intensity * 0.1))
            
            for _ in range(corruption_count):
                pos = self.random.randint(0, len(gork_list) - 1)
                if gork_list[pos] != ' ':  # Don't corrupt spaces
                    original = gork_list[pos]
                    # Replace with non-hex characters
                    invalid_hex = ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
                    gork_list[pos] = self.random.choice(invalid_hex)
                    corruptions.append(f"hex_{pos}")
            
            gork_data = ''.join(gork_list)
            
            return (
                gork_data,
                corruptions,
                f"Corrupted {len(corruptions)} hex characters",
                ["hex_decode_error", "invalid_hex_character"]
            )
        
        return data, [], "No hex corruption applied", []
    
    def _generate_url_encoding_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt URL encoding"""
        if isinstance(data, str):
            # Add corrupted URL encoding
            corruptions = [
                "%GG",  # Invalid hex
                "%",   # Incomplete encoding
                "%2",  # Incomplete encoding
                "%ZZ", # Invalid hex
                "%%20", # Double encoding
                "%u0041", # Unicode encoding (non-standard)
            ]
            
            corruption = self.random.choice(corruptions)
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + corruption + data[pos:]
            
            return (
                gork_data,
                [f"url_corruption_{pos}"],
                f"Injected URL encoding corruption: {corruption}",
                ["url_decode_error", "invalid_percent_encoding"]
            )
        
        return data, [], "No URL encoding corruption applied", []
    
    def _generate_unicode_direction(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Inject Unicode direction control characters"""
        if isinstance(data, str):
            direction_char = self.random.choice(self.unicode_corruption)
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + direction_char + data[pos:]
            
            return (
                gork_data,
                [f"unicode_direction_{pos}"],
                f"Injected Unicode direction control at {pos}",
                ["text_direction_corruption", "spoofing_attack", "visual_confusion"]
            )
        
        return data, [], "No Unicode direction corruption applied", []
    
    def _generate_zero_width_chars(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Inject zero-width characters"""
        if isinstance(data, str):
            zero_width = self.random.choice(self.zero_width_chars)
            injection_count = max(1, int(len(data) * intensity * 0.05))
            
            gork_data = data
            positions = []
            
            for _ in range(injection_count):
                pos = self.random.randint(0, len(gork_data))
                gork_data = gork_data[:pos] + zero_width + gork_data[pos:]
                positions.append(pos)
            
            return (
                gork_data,
                [f"zero_width_{pos}" for pos in positions],
                f"Injected {injection_count} zero-width characters",
                ["invisible_characters", "text_processing_confusion", "hidden_content"]
            )
        
        return data, [], "No zero-width corruption applied", []
    
    def _generate_combining_chars(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Inject combining characters"""
        if isinstance(data, str):
            # Combining characters that can create visual corruption
            combining_chars = [
                '\\u0300',  # Combining grave accent
                '\\u0301',  # Combining acute accent
                '\\u0302',  # Combining circumflex
                '\\u0303',  # Combining tilde
                '\\u0304',  # Combining macron
                '\\u0305',  # Combining overline
                '\\u0306',  # Combining breve
                '\\u0307',  # Combining dot above
            ]
            
            # Add multiple combining chars to create zalgo text
            combining_sequence = ''.join(self.random.choices(combining_chars, k=int(10 * intensity)))
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + combining_sequence + data[pos:]
            
            return (
                gork_data,
                [f"combining_chars_{pos}"],
                f"Injected combining character sequence at {pos}",
                ["zalgo_text", "rendering_corruption", "unicode_normalization_issues"]
            )
        
        return data, [], "No combining character corruption applied", []
    
    def _generate_epoch_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt timestamps with epoch issues"""
        if isinstance(data, dict):
            epoch_corruptions = {
                "__timestamp_negative__": -1,
                "__timestamp_year_2038__": 2147483648,  # Y2038 problem
                "__timestamp_far_future__": 253402300799,  # Year 9999
                "__timestamp_zero__": 0,  # Unix epoch
                "__timestamp_overflow__": 2**63 - 1,  # Max 64-bit
            }
            
            gork_data = data.copy()
            
            # Add corrupted timestamps to any existing time fields
            for key, value in data.items():
                if any(time_word in key.lower() for time_word in ['time', 'date', 'timestamp', 'created', 'updated']):
                    corruption_key = f"{key}_corrupted"
                    gork_data[corruption_key] = self.random.choice(list(epoch_corruptions.values()))
            
            return (
                gork_data,
                ["epoch_corruption"],
                "Added epoch timestamp corruptions",
                ["timestamp_overflow", "y2038_problem", "time_parsing_error"]
            )
        
        return data, [], "No epoch corruption applied", []
    
    def _generate_timezone_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt timezone information"""
        if isinstance(data, str) and any(tz in data for tz in ['UTC', 'GMT', '+', '-', 'Z']):
            # Corrupt timezone part
            tz_corruptions = [
                "+25:00",  # Invalid timezone
                "-15:99",  # Invalid minutes
                "UTC+25",  # Invalid UTC offset
                "GMT-99",  # Invalid GMT offset
                "Z+05:00", # Invalid format
                "PST+08:XX", # Invalid format
            ]
            
            corruption = self.random.choice(tz_corruptions)
            # Replace timezone info with corruption
            gork_data = data + corruption
            
            return (
                gork_data,
                ["timezone_corruption"],
                f"Added timezone corruption: {corruption}",
                ["timezone_parse_error", "invalid_offset", "time_conversion_error"]
            )
        
        return data, [], "No timezone corruption applied", []
    
    def _generate_hash_collision(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Generate data that could cause hash collisions"""
        if isinstance(data, str):
            # Create collision-prone patterns
            collision_patterns = [
                "Aa" + "B" * int(100 * intensity),  # Hash collision pattern
                "BB" + "A" * int(100 * intensity),  # Different but may collide
                "\\x00\\x01" * int(50 * intensity),  # Binary collision pattern
            ]
            
            pattern = self.random.choice(collision_patterns)
            gork_data = data + pattern
            
            return (
                gork_data,
                ["hash_collision_pattern"],
                f"Added hash collision pattern: {pattern[:20]}...",
                ["hash_collision", "hashtable_attack", "dos_via_collision"]
            )
        
        return data, [], "No hash collision pattern applied", []
    
    def _generate_signature_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt cryptographic signatures"""
        if isinstance(data, dict):
            # Add corrupted signature fields
            signature_corruptions = {
                "__signature__": "invalid_signature_" + "A" * int(100 * intensity),
                "__signature_algorithm__": "INVALID_ALG",
                "__public_key__": "\\x00\\x01\\x02" * int(20 * intensity),
                "__certificate__": "CORRUPTED_CERT_" + "X" * int(50 * intensity),
            }
            
            gork_data = data.copy()
            gork_data.update(signature_corruptions)
            
            return (
                gork_data,
                list(signature_corruptions.keys()),
                "Added signature corruptions",
                ["signature_verification_failure", "certificate_error", "crypto_error"]
            )
        
        return data, [], "No signature corruption applied", []
    
    def _generate_certificate_corruption(self, data: Any, intensity: float) -> Tuple[Any, List[str], str, List[str]]:
        """Corrupt certificate data"""
        if isinstance(data, str) and ('BEGIN CERTIFICATE' in data or 'certificate' in data.lower()):
            # Corrupt certificate-like data
            cert_corruptions = [
                "-----BEGIN CORRUPTED CERTIFICATE-----",
                "\\x00\\x01\\x02\\x03" + "A" * int(100 * intensity),
                "INVALID_CERT_FORMAT_" + "X" * int(50 * intensity),
            ]
            
            corruption = self.random.choice(cert_corruptions)
            pos = self.random.randint(0, len(data))
            gork_data = data[:pos] + corruption + data[pos:]
            
            return (
                gork_data,
                [f"certificate_corruption_{pos}"],
                f"Injected certificate corruption at {pos}",
                ["certificate_parse_error", "invalid_certificate", "tls_error"]
            )
        
        return data, [], "No certificate corruption applied", []