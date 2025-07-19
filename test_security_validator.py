#!/usr/bin/env python3
# /// script
# dependencies = ["pytest", "anthropic>=0.40.0"]
# ///

import pytest
import os
from security_validator import check_hard_blocks, get_command_type, validate_command_with_llm

class TestSecurityValidator:
    
    def test_hard_blocks_positive(self):
        dangerous_commands = [
            "sudo rm -rf /",
            "chmod 777 /etc/passwd",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "fdisk /dev/sda"
        ]
        
        for cmd in dangerous_commands:
            is_blocked, reason = check_hard_blocks(cmd)
            assert is_blocked, f"Command should be hard blocked: {cmd}"
            assert reason, f"Should have a reason for blocking: {cmd}"

    def test_hard_blocks_negative(self):
        safe_commands = [
            "rm -rf build/",
            "gcloud projects list",
            "ls -la",
            "git status",
            "npm install"
        ]
        
        for cmd in safe_commands:
            is_blocked, reason = check_hard_blocks(cmd)
            assert not is_blocked, f"Command should not be hard blocked: {cmd}"

    def test_command_type_detection(self):
        test_cases = [
            ("rm -rf temp/", "rm"),
            ("gcloud projects list", "gcloud"),
            ("ls -la", None),
            ("git status", None)
        ]
        
        for cmd, expected_type in test_cases:
            result = get_command_type(cmd)
            assert result == expected_type, f"Command '{cmd}' should return type '{expected_type}', got '{result}'"

    def test_llm_validation_no_api_key(self):
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        
        try:
            is_safe, reason = validate_command_with_llm("rm -rf build/", "rm")
            assert not is_safe, "Should block command when API key unavailable"
            assert "ANTHROPIC_API_KEY not available" in reason
        finally:
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_llm_validation_rm_safe(self):
        safe_command = "rm -rf build/"
        is_safe, reason = validate_command_with_llm(safe_command, "rm")
        assert is_safe, f"Command should be safe: {safe_command}"

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_llm_validation_rm_unsafe(self):
        unsafe_command = "rm -rf /usr"
        is_safe, reason = validate_command_with_llm(unsafe_command, "rm")
        assert not is_safe, f"Command should be unsafe: {unsafe_command}"

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_llm_validation_gcloud_safe(self):
        safe_command = "gcloud projects list"
        is_safe, reason = validate_command_with_llm(safe_command, "gcloud")
        assert is_safe, f"Command should be safe: {safe_command}"

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_llm_validation_gcloud_unsafe(self):
        unsafe_command = "gcloud compute instances create my-instance"
        is_safe, reason = validate_command_with_llm(unsafe_command, "gcloud")
        assert not is_safe, f"Command should be unsafe: {unsafe_command}"

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_llm_connection(self):
        try:
            is_safe, reason = validate_command_with_llm("rm -rf build/", "rm")
            assert reason != "LLM validation failed: Error code: 404", "LLM model not found - check model name"
        except Exception as e:
            pytest.fail(f"LLM connection failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])