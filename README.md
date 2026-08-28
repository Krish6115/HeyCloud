# ☁️ HeyCloud — Cloud-Native Real-Time Streaming Analytics Platform

[![CI Pipeline](https://github.com/YOUR_USERNAME/HeyCloud/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/HeyCloud/actions/workflows/ci.yml)
[![Infrastructure](https://github.com/YOUR_USERNAME/HeyCloud/actions/workflows/deploy-infra.yml/badge.svg)](https://github.com/YOUR_USERNAME/HeyCloud/actions/workflows/deploy-infra.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> A production-grade, event-driven, serverless real-time analytics platform built on AWS — simulating enterprise-scale e-commerce streaming systems (Netflix, Amazon, Uber).

---

## 🏗️ Architecture

```
Dockerized Event Producer
        ↓
   API Gateway (REST)
        ↓
  Kinesis Data Stream
        ↓
 Lambda Stream Processor
        ↓
  Data Transformation
        ↓
 ┌──────────┬──────────┐
 ↓          ↓          ↓
DynamoDB   Amazon S3   CloudWatch
(Hot)      (Cold/Lake) (Metrics)
 ↓          ↓          ↓
Analytics  QuickSight  SNS Alerts
Lambda     /Grafana
 ↓
React Dashboard
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Event Generation** | Python, Docker |
| **Ingestion** | API Gateway, Kinesis Data Streams |
| **Processing** | AWS Lambda (Python 3.12) |
| **Hot Storage** | DynamoDB (On-Demand, TTL) |
| **Cold Storage** | S3 (Lifecycle Policies) |
| **Analytics** | Lambda API, QuickSight, Grafana |
| **Monitoring** | CloudWatch, SNS |
| **IaC** | Terraform (Modular) |
| **CI/CD** | GitHub Actions |
| **Frontend** | React (Vite) |

## 📦 Project Structure

```
HeyCloud/
├── infrastructure/terraform/    # IaC with reusable modules
├── services/
│   ├── event-producer/          # Dockerized event generator
│   └── stream-processor/       # Lambda stream consumer
├── api/analytics/               # Analytics API Lambda
├── frontend/                    # React dashboard
├── scripts/                     # Deployment & utility scripts
├── tests/                       # Unit & integration tests
├── docs/                        # Documentation & diagrams
└── .github/workflows/           # CI/CD pipelines
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate credentials
- Terraform >= 1.5
- Docker & Docker Compose
- Node.js >= 18
- Python >= 3.11

### 1. Clone & Configure
```bash
git clone https://github.com/YOUR_USERNAME/HeyCloud.git
cd HeyCloud
cp .env.example .env
# Edit .env with your AWS account details
```

### 2. Deploy Infrastructure
```bash
make init      # Initialize Terraform
make plan      # Review changes
make apply     # Deploy to AWS
```

### 3. Run Event Producer
```bash
make producer-build
make producer-run
```

### 4. Launch Dashboard
```bash
make frontend-install
make frontend-dev
```

## 📊 Simulated Events

| Event Type | Description |
|-----------|-------------|
| `PRODUCT_VIEW` | User views a product page |
| `ADD_TO_CART` | User adds item to cart |
| `PURCHASE` | Order completed |
| `PAYMENT` | Payment success/failure |
| `USER_LOGIN` | Authentication event |
| `SEARCH` | Search query executed |

## 📈 Analytics Capabilities

- **Top Selling Products** — Real-time leaderboard
- **Revenue per Minute** — Live revenue tracking
- **Active Users** — Concurrent session monitoring
- **Purchase Trends** — Time-series analysis
- **Fraud Detection** — Spike/anomaly alerts
- **Region Analytics** — Geographic distribution

## 🔒 Security

- IAM least-privilege roles per service
- API Gateway throttling & API keys
- Encryption at rest (S3 SSE, DynamoDB, Kinesis)
- No hardcoded credentials
- AWS Parameter Store for secrets

## 💰 Cost Estimate (Free Tier)

| Service | Monthly Cost |
|---------|-------------|
| Lambda | $0.00 |
| DynamoDB | $0.00-$2 |
| S3 | $0.00 |
| API Gateway | $0.00 |
| Kinesis (1 shard) | ~$15 |
| CloudWatch | $0.00 |
| **Total** | **~$15/mo** |

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

This is a portfolio project. Feel free to fork and adapt for your own learning.
