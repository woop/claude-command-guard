# Claude LLM Guard

Command safety hook for Claude Code.

## Install

```bash
# Install the hook
uv run https://raw.githubusercontent.com/woop/claude-llm-guard/main/security_validator.py --install

# Set API key
export ANTHROPIC_API_KEY="your-key"
```

## Configure Claude

Add to your Claude settings file (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "beforeBash": {
      "script": "~/.claude/hooks/security_validator.py"
    }
  },
  "env": {
    "ANTHROPIC_API_KEY": "your-key-here"
  }
}
```

## Customize

Fork this repo and edit `HARD_BLOCK_RULES` and `LLM_VALIDATION_RULES`.

## Test

```bash
uv run test_security_validator.py
```