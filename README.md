# Claude Command Guard

Command safety hook for Claude Code that blocks dangerous bash commands.

### How it works

- **Hard blocks**: Always blocks obviously dangerous commands (`sudo rm`, `chmod 777`, `--no-verify`, etc.)
- **LLM validation**: Uses Anthropic API to evaluate context-dependent commands (`rm -rf`, `gcloud`)  
- **Pass-through**: All other commands allowed by default

Examples:
- ✅ `rm -rf build/` → Safe local directory
- ❌ `rm -rf /usr` → System directory  
- ✅ `gcloud projects list` → Read-only
- ❌ `gcloud instances create` → Write operation
- ❌ `git commit --no-verify` → Verification bypass

### Setup

Requires: [Claude Code](https://claude.ai/code), `uv`, and Anthropic API key.

```bash
git clone https://github.com/woop/claude-command-guard.git \
  ~/.claude/hooks/claude-command-guard
```

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "beforeBash": {
      "script": "uv run ~/.claude/hooks/claude-command-guard/security_validator.py"
    }
  },
  "env": {
    "ANTHROPIC_API_KEY": "your-key-here"
  }
}
```

#### Alternative: remote execution

```json
{
  "hooks": {
    "beforeBash": {
      "script": "uv run https://raw.githubusercontent.com/woop/claude-command-guard/main/security_validator.py"
    }
  },
  "env": {
    "ANTHROPIC_API_KEY": "your-key-here"
  }
}
```

### Customize

Fork this repo and edit `HARD_BLOCK_RULES` and `LLM_VALIDATION_RULES`.

Example hard block rule:
```python
HARD_BLOCK_RULES = {
    r'sudo\s+rm': "Privileged destructive command",
    r'--no-verify': "Verification bypass detected",
    r'test-block': "Test command for dry run validation",
}
```

Example LLM validation rule:
```python
LLM_VALIDATION_RULES = {
    "rm": {
        "pattern": r'rm\s+.*-rf',
        "instructions": "Validate rm -rf commands for path safety",
        "safe_criteria": "Paths within worktrees, build directories, temp folders",
        "unsafe_criteria": "System paths, parent directory traversal, root paths",
        "safe_examples": ["rm -rf build/", "rm -rf ./temp"],
        "unsafe_examples": ["rm -rf ../../../", "rm -rf /usr"]
    }
}
```

### Testing

Use built-in dry-run commands:
- `test-block` → Hard block validation
- `test-llm` → LLM validation