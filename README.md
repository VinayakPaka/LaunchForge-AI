<div align="center">

```
██╗      █████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗  ██╗██╗██╗   ██╗███╗   ███╗
██║     ██╔══██╗██║   ██║████╗  ██║██╔════╝██║  ██║██║██║   ██║████╗ ████║
██║     ███████║██║   ██║██╔██╗ ██║██║     ███████║██║██║   ██║██╔████╔██║
██║     ██╔══██║██║   ██║██║╚██╗██║██║     ██╔══██║██║██║   ██║██║╚██╔╝██║
███████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╗██║  ██║██║╚██████╔╝██║ ╚═╝ ██║
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝
```

**Your startup idea. Validated. Pitched. Launched. — by AI agents working together.**

[![Built at Complete AI Hackathon](https://img.shields.io/badge/Built%20at-Complete%20AI%20Hackathon-blueviolet?style=for-the-badge)](https://lablab.ai/ai-hackathons/complete-ai-agent-hackathon)
[![Python](https://img.shields.io/badge/Python-60%25-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-37%25-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-→%20Try%20it-22c55e?style=for-the-badge)](https://tb314nms.run.complete.dev/)

</div>

---

## 🚀 What is Launchium?

> **The gap between "I have an idea" and "I have a business" used to take months. Launchium collapses it to minutes.**

Launchium is a **multi-agent AI platform** that takes your raw startup idea and autonomously builds everything you need to go from zero to launch-ready — market validation, competitive analysis, pitch decks, go-to-market strategies, and more. All in one shared workspace, all powered by collaborating AI agents.

No more bouncing between 10 different tools. No more generic ChatGPT outputs. Just describe your idea, and watch a coordinated squad of specialized AI agents do the heavy lifting — the way a real founding team would.

---

## ✨ Features

| Agent | What it does |
|---|---|
| 🔍 **Research Agent** | Deep-dives market size, trends, and real competitor data |
| ✅ **Validation Agent** | Scores your idea on viability, timing, and demand signals |
| 📊 **Pitch Agent** | Crafts a compelling, investor-ready pitch narrative |
| 🗺️ **GTM Agent** | Builds your go-to-market roadmap with actionable steps |
| 📝 **Content Agent** | Writes landing page copy, taglines, and marketing assets |

- **Real-time collaborative workspace** — agents share context and build on each other's work
- **End-to-end in one place** — from napkin idea to market-ready assets
- **Human-in-the-loop** — you stay in control; agents do the grunt work
- **Fast** — built to ship in days, not months

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Launchium Platform                │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │  Next.js │    │ FastAPI  │    │  Agent       │   │
│  │  Frontend│───▶│ Backend  │───▶│  Orchestrator│   │
│  └──────────┘    └──────────┘    └──────┬───────┘   │
│                                         │           │
│              ┌──────────────────────────▼─────────┐ │
│              │         Agent Swarm                │ │
│              │  [Research] [Validate] [Pitch]     │ │
│              │  [GTM]      [Content]              │ │
│              └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Stack:**
- **Frontend:** Next.js + TypeScript
- **Backend:** Python / FastAPI
- **Agents:** Multi-agent framework with shared context window
- **Infra:** Complete.dev (collaborative AI workspaces)

---

## ⚡ Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- Git

### Installation

```bash
# Clone the repo
git clone https://github.com/VinayakPaka/Launchium.git
cd Launchium

# Start everything with one command
chmod +x start.sh
./start.sh
```

The `start.sh` script boots both the frontend and backend services. Open your browser and go to `http://localhost:3000`.

### Manual Setup

```bash
# Backend
cd apps/backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (new terminal)
cd apps/frontend
npm install
npm run dev
```

---

## 🎮 How to Use

1. **Describe your idea** — just talk to Launchium like you'd pitch it to a friend
2. **Watch the agents work** — each agent tackles its specialty in real time
3. **Review outputs** — validation score, competitor map, pitch deck, GTM plan
4. **Iterate** — refine your idea, re-run, compare results
5. **Launch** — take your polished assets and go build

---

## 🏆 Built at Complete AI Hackathon

Launchium was built during the **[Complete AI Agent Hackathon](https://lablab.ai/ai-hackathons/complete-ai-agent-hackathon)** hosted by [lablab.ai](https://lablab.ai) (February 23 – March 1, 2026).

The challenge: build an end-to-end agentic AI product, using at least 2 AI agents working together, in 6 days inside a shared collaborative workspace.

We took that challenge and ran with it.

---

## 📁 Project Structure

```
Launchium/
├── apps/
│   ├── frontend/          # Next.js app (TypeScript)
│   └── backend/           # FastAPI server (Python)
├── start.sh               # One-command launcher
└── .gitignore
```

---

## 🤝 Contributing

Got ideas to make Launchium even more powerful? PRs are welcome.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add: your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 👨‍💻 Team

Built with ❤️ by [@VinayakPaka](https://github.com/VinayakPaka) and team.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

**If Launchium helped you, give it a ⭐ — it means the world.**

[🌐 Live Demo](https://tb314nms.run.complete.dev/) · [🐛 Report Bug](https://github.com/VinayakPaka/Launchium/issues) · [💡 Request Feature](https://github.com/VinayakPaka/Launchium/issues)

</div>
