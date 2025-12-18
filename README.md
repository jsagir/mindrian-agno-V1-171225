# Mindrian - AI-Powered Innovation Platform

Mindrian is a cognitive orchestration platform that helps users explore, validate, and develop business opportunities through structured thinking frameworks and AI-powered analysis.

## Features

- **Larry the Clarifier** - Conversational agent that helps clarify problems (What/Who/Success)
- **Framework Agents** - Minto Pyramid, Beautiful Question, Domain Analysis, CSIO
- **Deep Research Team** - Multi-agent workflow for comprehensive opportunity discovery
- **Bank of Opportunities** - Save and revisit promising opportunities with full context
- **Deep Dive Sessions** - Return to banked opportunities for focused exploration

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MINDRIAN ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Frontend (Next.js + shadcn/ui + Syncfusion)                    │
│  └── Repo: github.com/jsagir/mindrian-ui                        │
│  └── Host: Vercel (FREE)                                        │
│                                                                  │
│  Backend (FastAPI + Agno Framework) ← THIS REPO                 │
│  └── Host: Render (FREE)                                        │
│  └── URL: https://mindrian-api.onrender.com                     │
│                                                                  │
│  Databases                                                       │
│  ├── Neo4j Aura (Knowledge Graph) - FREE tier                   │
│  └── Pinecone (Vector Search) - FREE tier                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

> **Note**: The UI is in a separate repository: [mindrian-ui](https://github.com/jsagir/mindrian-ui)

## Project Structure

```
mindrian-agno/
├── mindrian/                    # Main Python package
│   ├── agents/                  # AI Agents
│   │   ├── conversational/      # Larry, Devil's Advocate
│   │   ├── frameworks/          # Minto, PWS, JTBD
│   │   └── research/            # Beautiful Question, Domain, CSIO
│   ├── teams/                   # Multi-agent teams
│   │   ├── deep_research_team.py
│   │   └── deep_dive_team.py
│   ├── services/                # Business services
│   │   └── opportunity_bank.py  # Bank of Opportunities
│   ├── handoff/                 # Agent handoff protocol
│   ├── tools/                   # MCP tools integration
│   └── config/                  # Configuration
├── api/                         # FastAPI backend
├── docs/                        # Documentation
└── tests/                       # Test suite
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Neo4j Aura account (free tier)
- Pinecone account (free tier)
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone https://github.com/jsagir/mindrian-agno-V1-171225.git
cd mindrian-agno-V1-171225

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Start the backend
python -m uvicorn api.main:app --reload --port 8000

# Or run the playground
python playground.py
```

## Cloud Deployment

See [deployment documentation](docs/DEPLOYMENT.md) for instructions on deploying to:
- **Backend**: Render (free tier)
- **Frontend**: Vercel (free tier)

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes |
| `NEO4J_URI` | Neo4j Aura connection URI | Yes |
| `NEO4J_PASSWORD` | Neo4j password | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `PINECONE_INDEX` | Pinecone index name | Yes |

## Available Agents

| Agent | Purpose |
|-------|---------|
| **Larry** | The Clarifier - asks penetrating questions |
| **Devil's Advocate** | Finds weaknesses, stress-tests ideas |
| **Minto Pyramid** | Structures content with SCQA |
| **Beautiful Question** | Generates Why/What If/How questions |
| **Domain Analysis** | Maps domains and intersections |
| **CSIO** | Cross-Sectional Innovation Opportunities |

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Bank of Opportunities](docs/BANK_OF_OPPORTUNITIES.md)
- [Syncfusion Integration](docs/SYNCFUSION_AI_INTEGRATION.md)
- [UI Strategy](docs/UI_STRATEGY.md)
- [Agno v2 Migration](docs/AGNO_V2_MIGRATION_GUIDE.md)

## Tech Stack

**Backend:**
- Python 3.11+
- Agno Framework (AI agents)
- FastAPI (API server)
- Neo4j (Knowledge graph)
- Pinecone (Vector search)

**Frontend:**
- Next.js 14
- TypeScript
- Tailwind CSS
- Agno Agent UI
- Syncfusion AI Components

## License

MIT

## Author

Built with Mindrian methodology.
