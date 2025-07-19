# Claude LLM Guard

Command safety hook for Claude Code.

## Install

```bash
uv run https://raw.githubusercontent.com/woop/claude-llm-guard/main/security_validator.py --install
export ANTHROPIC_API_KEY="your-key"
```

## Customize

Fork this repo and edit the rules in `security_validator.py`.

## Test

```bash
uv run security_validator.py --test
```