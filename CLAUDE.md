# Public Domain Monetization - Project Instructions

## Project Overview
This project focuses on monetizing public domain content through various digital channels and platforms.

## Project Structure
```
PublicDomainMonetization/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── .claude/
│   ├── skills/            # Project-specific skills
│   ├── agents/            # Project-specific agents
│   ├── hooks/             # Project-specific hooks
│   └── reviews/           # Code review outputs
├── .github/workflows/      # CI/CD pipelines
├── .env.example           # Environment template
├── .gitignore
└── README.md
```

## Development Guidelines

### Code Standards
- Python 3.11+ with type hints on all functions
- Black formatting (line length 88)
- pytest for testing
- All external API calls must use `os.environ.get()` for credentials

### Security Rules
- NEVER commit API keys or secrets
- Use `.env` for local development (excluded from git)
- All sensitive config via environment variables

### Testing Requirements
- All new features must have corresponding tests
- Maintain minimum 80% code coverage
- Run `pytest tests/ -v` before committing

## Key Workflows

### Adding New Content Sources
1. Create source adapter in `src/sources/`
2. Add tests in `tests/test_sources/`
3. Document in `docs/sources/`

### Monetization Channels
- Document each channel integration in `docs/channels/`
- Track revenue metrics in designated location

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Format code
black src/ tests/
```

## Notes
- Check global CLAUDE.md for universal rules
- Use research agents for content discovery
- Document all public domain verification processes
