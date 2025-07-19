#!/usr/bin/env python3
# /// script
# dependencies = ["anthropic>=0.40.0"]
# ///

HARD_BLOCK_RULES = {
    r'sudo\s+rm': "Privileged destructive command",
    r'chmod\s+777': "Dangerous permission change",
    r'--no-verify': "Verification bypass detected",
    r'rm\s+.*-rf.*\s+/\s*$': "Root directory deletion",
    r'rm\s+.*-rf.*\s+~': "Home directory deletion",
    r'dd\s+if=': "Dangerous disk operation",
    r'mkfs\.': "File system operation",
    r'fdisk': "Disk partitioning operation",
    r'/etc/': "System directory access",
    r'/usr/bin/': "System binary access",
    r'/System/': "System directory access",
    r'test-block': "Test command for dry run validation",
}

LLM_VALIDATION_RULES = {
    "rm": {
        "pattern": r'rm\s+',
        "instructions": "Validate rm commands for path safety",
        "safe_criteria": "Single files, or directories within worktrees, build directories, temp folders, or clearly safe local paths",
        "unsafe_criteria": "System paths, parent directory traversal (../), root paths, home directory shortcuts, or dangerous recursive operations",
        "safe_examples": [
            "rm file.txt",
            "rm -rf build/",
            "rm -rf ./temp",
            "rm -rf /Users/user/worktrees/project/dist",
            "rm -rf node_modules"
        ],
        "unsafe_examples": [
            "rm -rf ../../../",
            "rm -rf /usr",
            "rm -rf /etc",
            "rm -rf ~",
            "rm -rf /"
        ]
    },
    "gcloud": {
        "pattern": r'gcloud\s+',
        "instructions": "Validate gcloud commands for read-only operations",
        "safe_criteria": "Read-only operations (list, get, describe, show, info, auth list, config get-value)",
        "unsafe_criteria": "Write operations (create, delete, update, deploy, set, add, remove)",
        "safe_examples": [
            "gcloud projects list",
            "gcloud config get-value project",
            "gcloud compute instances list",
            "gcloud auth list"
        ],
        "unsafe_examples": [
            "gcloud compute instances create",
            "gcloud projects delete",
            "gcloud iam policy-bindings add",
            "gcloud container clusters create"
        ]
    },
    "test": {
        "pattern": r'test-llm',
        "instructions": "Test LLM validation - always block for dry run testing",
        "safe_criteria": "Never - this is a test command that should always be blocked",
        "unsafe_criteria": "Any command containing 'test-llm'",
        "safe_examples": [],
        "unsafe_examples": [
            "test-llm"
        ]
    }
}

def get_validation_prompt(command_type: str) -> str:
    rules = LLM_VALIDATION_RULES[command_type]

    safe_examples = "\n".join(f"- {ex}" for ex in rules["safe_examples"])
    unsafe_examples = "\n".join(f"- {ex}" for ex in rules["unsafe_examples"])

    return f"""You are validating a {command_type} command for safety.

TASK: {rules["instructions"]}

CRITERIA:
- SAFE: {rules["safe_criteria"]}
- UNSAFE: {rules["unsafe_criteria"]}

EXAMPLES:

✅ SAFE:
{safe_examples}

❌ UNSAFE:
{unsafe_examples}

Respond with exactly "1" if SAFE or "0" if UNSAFE."""

import sys
import json
import os
import re
from typing import Tuple, Optional
from anthropic import Anthropic

def check_hard_blocks(command: str) -> Tuple[bool, str]:
    for pattern, reason in HARD_BLOCK_RULES.items():
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def get_command_type(command: str) -> Optional[str]:
    for cmd_type, rules in LLM_VALIDATION_RULES.items():
        if re.search(rules["pattern"], command, re.IGNORECASE):
            return cmd_type
    return None

def validate_command_with_llm(command: str, command_type: str) -> Tuple[bool, str]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "ANTHROPIC_API_KEY not available - blocking command for safety"

    client = Anthropic(api_key=api_key)
    prompt = get_validation_prompt(command_type)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\nCommand to validate: {command}"
            }]
        )

        result = response.content[0].text.strip()
        is_safe = result.startswith("1")
        reason = f"Command blocked by LLM validation"
        return is_safe, reason
    except Exception as e:
        return False, f"LLM validation failed: {str(e)}"

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
        command = hook_input.get("tool_input", {}).get("command", "")

        if not command:
            sys.exit(0)

        # Tier 1: Hard blocks
        is_blocked, reason = check_hard_blocks(command)
        if is_blocked:
            print(f"🚫 BLOCKED: {reason}", file=sys.stderr)
            sys.exit(2)

        # Tier 2: LLM validation for conditional cases
        command_type = get_command_type(command)
        if command_type:
            is_safe, reason = validate_command_with_llm(command, command_type)
            if not is_safe:
                print(f"🚫 BLOCKED: {reason}", file=sys.stderr)
                sys.exit(2)

        # Tier 3: Pass through (safe by default)
        sys.exit(0)

    except Exception as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
