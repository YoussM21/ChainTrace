# ChainTrace 🔗

A comprehensive Bitcoin transaction forensics tool designed for blockchain investigators, compliance teams, and security researchers. ChainTrace maps fund flows across the Bitcoin network, scores wallet addresses for suspicious behavior, and renders transaction graphs visually — all through an intuitive web interface.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-18+-61dafb.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109-009688.svg)

## ✨ Features

### 🔍 Transaction Tracing
- Map the flow of funds across the Bitcoin network
- Follow transactions through multiple hops (1-4 levels deep)
- Filter by minimum transaction value
- Interactive graph exploration

### ⚠️ Risk Scoring
- Advanced algorithms to score wallet addresses (0-100 scale)
- Multiple risk factors analyzed:
  - Transaction frequency patterns
  - Mixing service detection
  - High-velocity fund movement
  - Structured transaction patterns
  - Privacy tool usage
  - Round number transactions
- Risk level classification (LOW, MEDIUM, HIGH, CRITICAL)
- Automatic flagging of suspicious behaviors

### 📊 Graph Visualization
- Interactive force-directed graph layout
- Color-coded nodes by risk level
- Zoom, pan, and node dragging
- Real-time graph metrics
- Click nodes to explore further

### 🔗 Address Clustering
- Identify related addresses using heuristics
- Common-input-ownership detection
- Peeling chain pattern recognition
- Mixing behavior analysis

### 📈 Analytics
- Real-time balance and transaction history
- USD value conversion
- Network centrality analysis
- Graph density metrics

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Redis (caching)
- NetworkX (graph analysis)

### Frontend
- React 18+ with TypeScript
- Vite
- TailwindCSS
- D3.js / React Force Graph
- Recharts (for analytics)

## Project Structure

```
ChainTrace/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core config, security
│   │   ├── models/      # Data models
│   │   ├── services/    # Business logic
│   │   │   ├── blockchain.py    # Bitcoin API integration
│   │   │   ├── graph.py         # Graph building
│   │   │   ├── risk_scorer.py   # Risk scoring engine
│   │   │   └── clustering.py    # Address clustering
│   │   └── utils/       # Helper functions
│   ├── tests/
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API client
│   │   ├── hooks/       # Custom hooks
│   │   └── utils/       # Utilities
│   └── package.json
└── docker-compose.yml   # Local development setup
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Run the setup script
./scripts/setup.sh

# Or manually:
docker-compose up
```

Visit:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your BlockCypher API token to .env
uvicorn app.main:app --reload
```

**Frontend** (in a new terminal)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

See [SETUP.md](SETUP.md) for detailed instructions.

## 📖 Documentation

- [Setup Guide](SETUP.md) - Detailed installation and configuration
- [Contributing](CONTRIBUTING.md) - How to contribute to the project
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🎯 Use Cases

- **Blockchain Investigations**: Track fund flows in criminal investigations
- **Compliance & AML**: Screen addresses for regulatory compliance
- **Security Research**: Analyze mixing patterns and privacy tools
- **Forensic Analysis**: Investigate exchange hacks and fraud
- **Academic Research**: Study Bitcoin transaction patterns
- **Portfolio Projects**: Demonstrate full-stack blockchain development skills

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic API docs
- **NetworkX**: Graph analysis and algorithms
- **Redis**: Caching layer for API responses
- **Pydantic**: Data validation and settings management
- **httpx**: Async HTTP client for blockchain APIs

### Frontend
- **React 18**: Modern UI with hooks and functional components
- **TypeScript**: Type-safe development
- **Vite**: Lightning-fast build tool
- **TailwindCSS**: Utility-first styling
- **react-force-graph**: Interactive graph visualization
- **Recharts**: Analytics charts
- **Lucide Icons**: Beautiful icon set

### Infrastructure
- **Docker**: Containerized deployment
- **GitHub Actions**: CI/CD pipeline
- **BlockCypher API**: Bitcoin blockchain data

## 📊 API Endpoints

- `GET /api/v1/address/{address}` - Get address information
- `GET /api/v1/address/{address}/transactions` - Get transaction history
- `GET /api/v1/address/{address}/risk` - Calculate risk score
- `GET /api/v1/transaction/{tx_hash}` - Get transaction details
- `GET /api/v1/graph/{address}` - Build transaction graph
- `GET /api/v1/address/{address}/clustering` - Analyze address relationships

Full API documentation available at `/docs` when running the backend.

## 🧪 Testing

**Backend**
```bash
cd backend
pytest tests/ -v
```

**Frontend**
```bash
cd frontend
npm run lint
npm run build
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas we'd love help with:
- Additional risk scoring algorithms
- Support for other cryptocurrencies
- Performance optimizations
- UI/UX improvements
- Documentation

## 📝 Example Addresses to Try

- `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` - Genesis block (Satoshi Nakamoto)
- `3Cbq7aT1tY8kMxWLbitaG7yT6bPbKChq64` - Binance cold wallet
- Any Bitcoin address you're curious about!

## ⚖️ Legal & Ethics

ChainTrace is designed for **defensive security, compliance, and research purposes only**.

- ✅ Legal use cases: AML compliance, fraud investigation, academic research
- ❌ Do not use for: Harassment, doxxing, or illegal surveillance

Bitcoin addresses are public information on the blockchain. This tool simply aggregates and analyzes publicly available data.

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [BlockCypher](https://blockcypher.com) for blockchain API
- [Blockchain.com](https://blockchain.com) for alternative data source
- Open source community for amazing tools and libraries

## 📧 Contact & Support

- Open an issue for bugs or feature requests
- Star this repo if you find it useful!
- Share with others interested in blockchain forensics

---

**Built with ❤️ for the blockchain security community**
