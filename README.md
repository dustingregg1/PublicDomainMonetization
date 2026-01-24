# Public Domain Monetization

A project for discovering, curating, and monetizing public domain content across various digital platforms.

## Overview

This project provides tools and workflows for:
- Discovering public domain content from various sources
- Verifying public domain status
- Transforming content for different platforms
- Publishing and monetizing through multiple channels

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dustinwloring1988/PublicDomainMonetization.git
cd PublicDomainMonetization

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest tests/ -v
```

## Project Structure

```
├── src/                    # Source code
│   ├── sources/           # Content source adapters
│   ├── processors/        # Content transformation
│   └── channels/          # Monetization channels
├── tests/                  # Test files
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── .github/workflows/      # CI/CD pipelines
```

## Content Sources

- Project Gutenberg
- Internet Archive
- Library of Congress
- Wikimedia Commons
- Public domain image repositories

## Monetization Channels

- Print-on-demand (Amazon KDP, etc.)
- Digital products
- Content platforms
- Educational materials

## Development

See [CLAUDE.md](CLAUDE.md) for development guidelines and project-specific instructions.

## License

MIT License - See LICENSE file for details.
