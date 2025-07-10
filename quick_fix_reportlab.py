#!/usr/bin/env python3
"""
Quick fix to remove ReportLab import issues
"""

import re

# Read the report.py file
with open('redforge/core/report.py', 'r') as f:
    content = f.read()

# Replace problematic sections with simplified versions
fixes = [
    # Fix method signatures that reference ReportLab classes
    (r'def _create_vulnerability_section\(self, result: AttackResult, styles\) -> Paragraph:', 
     'def _create_vulnerability_section(self, result: AttackResult, styles):'),
    
    # Fix any other Paragraph references in method signatures
    (r' -> Paragraph:', ' -> str:'),
    (r' -> Table:', ' -> str:'),
    (r' -> PageBreak:', ' -> str:'),
]

for pattern, replacement in fixes:
    content = re.sub(pattern, replacement, content)

# Write back
with open('redforge/core/report.py', 'w') as f:
    f.write(content)

print("Fixed ReportLab type hints")