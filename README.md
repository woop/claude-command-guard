# Claude Command Guard

Command safety hook for Claude Code that blocks dangerous bash commands.

### How it works

- **Hard blocks**: Always blocks obviously dangerous commands (`sudo rm`, `chmod 777`, `--no-verify`, etc.)
- **LLM validation**: Uses Claude to evaluate context-dependent commands (`rm -rf`, `gcloud`)  
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