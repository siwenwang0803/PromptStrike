#!/usr/bin/env python3
"""
update_risk_matrix.py

Replaces the Owner column in the Risk Mitigation Matrix with Jira ticket
Markdown links based on threat_to_jira.yml mapping.

Usage:
    python scripts/update_risk_matrix.py
    python scripts/update_risk_matrix.py --doc path/to/threat_model.md --map scripts/threat_to_jira.yml
"""

import re
import yaml
import argparse
import pathlib
import difflib
import sys
from typing import Dict, List


# Pattern to match the Risk Mitigation Matrix table
TABLE_PATTERN = re.compile(
    r"(## Risk Mitigation Matrix\n\n"
    r"\|.*?\|\n"      # header row
    r"\|.*?\|\n"      # separator row
    r"(?:\|.*?\|\n)+)",  # data rows
    re.DOTALL | re.MULTILINE,
)

# Alternative pattern for the comprehensive threat risk rankings table
RANKINGS_PATTERN = re.compile(
    r"(### Comprehensive Threat Risk Rankings\n\n"
    r"\|.*?\|\n"      # header row
    r"\|.*?\|\n"      # separator row
    r"(?:\|.*?\|\n)+)",  # data rows
    re.DOTALL | re.MULTILINE,
)


def load_mapping(map_path: pathlib.Path) -> Dict[str, str]:
    """Load threat ID to Jira ticket mapping from YAML file."""
    try:
        mapping = yaml.safe_load(map_path.read_text(encoding="utf-8"))
        if not isinstance(mapping, dict):
            sys.exit(f"❌ Invalid mapping format in {map_path}")
        return mapping
    except FileNotFoundError:
        sys.exit(f"❌ Mapping file not found: {map_path}")
    except yaml.YAMLError as e:
        sys.exit(f"❌ YAML parsing error: {e}")


def update_table(table_block: str, mapping: Dict[str, str], jira_base_url: str) -> str:
    """Update a table block with Jira links."""
    lines = table_block.strip().splitlines()
    if len(lines) < 3:
        return table_block
    
    # Keep header and separator rows
    new_lines = lines[:2]
    
    for row in lines[2:]:
        if not row.strip():
            continue
            
        # Parse table row
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 5:
            new_lines.append(row)
            continue
            
        threat_id = cols[0].strip()
        jira_ticket = mapping.get(threat_id)
        
        if jira_ticket:
            # Replace the Owner column (index 4) with Jira link
            jira_link = f"[{jira_ticket}]({jira_base_url}/{jira_ticket})"
            cols[4] = jira_link
        
        # Reconstruct the row
        new_row = "| " + " | ".join(cols) + " |"
        new_lines.append(new_row)
    
    return "\n".join(new_lines)


def update_comprehensive_table(table_block: str, mapping: Dict[str, str], jira_base_url: str) -> str:
    """Update the comprehensive threat risk rankings table with Jira links."""
    lines = table_block.strip().splitlines()
    if len(lines) < 3:
        return table_block
    
    # Keep header and separator rows
    new_lines = lines[:2]
    
    for row in lines[2:]:
        if not row.strip():
            continue
            
        # Parse table row
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 9:  # Expecting more columns in comprehensive table
            new_lines.append(row)
            continue
            
        threat_id = cols[1].strip()  # Threat ID is in column 1
        jira_ticket = mapping.get(threat_id)
        
        if jira_ticket:
            # Replace the Jira column (index 8) with proper link
            jira_link = f"[{jira_ticket}]({jira_base_url}/{jira_ticket})"
            cols[8] = jira_link
        
        # Reconstruct the row
        new_row = "| " + " | ".join(cols) + " |"
        new_lines.append(new_row)
    
    return "\n".join(new_lines)


def main(md_path: pathlib.Path, map_path: pathlib.Path, in_place: bool = True, 
         jira_base_url: str = "https://jira.promptstrike.ai/browse") -> None:
    """Main function to update threat model with Jira links."""
    
    # Load files
    try:
        md_text = md_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        sys.exit(f"❌ Threat model file not found: {md_path}")
    
    mapping = load_mapping(map_path)
    print(f"✅ Loaded {len(mapping)} threat-to-jira mappings")
    
    # Find and update Risk Mitigation Matrix
    updates_made = 0
    original_text = md_text
    
    # Update Risk Mitigation Matrix
    risk_matrix_match = TABLE_PATTERN.search(md_text)
    if risk_matrix_match:
        table_block = risk_matrix_match.group(1).rstrip()
        updated_table = update_table(table_block, mapping, jira_base_url)
        md_text = md_text.replace(table_block, updated_table)
        updates_made += 1
        print("✅ Updated Risk Mitigation Matrix")
    else:
        print("⚠️  Risk Mitigation Matrix not found")
    
    # Update Comprehensive Threat Risk Rankings table
    rankings_match = RANKINGS_PATTERN.search(md_text)
    if rankings_match:
        table_block = rankings_match.group(1).rstrip()
        updated_table = update_comprehensive_table(table_block, mapping, jira_base_url)
        md_text = md_text.replace(table_block, updated_table)
        updates_made += 1
        print("✅ Updated Comprehensive Threat Risk Rankings")
    else:
        print("⚠️  Comprehensive Threat Risk Rankings table not found")
    
    # Save updated file
    if in_place and updates_made > 0:
        md_path.write_text(md_text, encoding="utf-8")
        print(f"✅ Updated {md_path} with {updates_made} table(s)")
    elif updates_made == 0:
        print("❌ No tables were updated - check file format")
        return
    
    # Show diff
    diff_lines = list(difflib.unified_diff(
        original_text.splitlines(keepends=True),
        md_text.splitlines(keepends=True),
        fromfile=f"a/{md_path.name}",
        tofile=f"b/{md_path.name}",
        n=3
    ))
    
    if diff_lines:
        print("\n" + "="*60)
        print("DIFF PREVIEW:")
        print("="*60)
        for line in diff_lines[:50]:  # Limit diff output
            print(line.rstrip())
        if len(diff_lines) > 50:
            print(f"... ({len(diff_lines) - 50} more lines)")
    else:
        print("ℹ️  No changes detected")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update threat model Risk Matrix with Jira ticket links"
    )
    parser.add_argument(
        "--doc",
        type=pathlib.Path,
        default="docs/PromptStrike/Security/Guardrail_Threat_Model.md",
        help="Path to threat model markdown file"
    )
    parser.add_argument(
        "--map",
        type=pathlib.Path,
        default="scripts/threat_to_jira.yml",
        help="Path to threat-to-jira mapping YAML file"
    )
    parser.add_argument(
        "--jira-base-url",
        default="https://jira.promptstrike.ai/browse",
        help="Base URL for Jira tickets"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files"
    )
    
    args = parser.parse_args()
    
    main(
        md_path=args.doc,
        map_path=args.map,
        in_place=not args.dry_run,
        jira_base_url=args.jira_base_url
    )