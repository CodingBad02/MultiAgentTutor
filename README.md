# 🤖 Multi-Agent AI Tutor System

A sophisticated AI tutoring system built with Google's Agent Development Kit (ADK) principles, featuring specialized agents for different subjects, dynamic Gemini-based routing, and comprehensive tool integration.

## ✨ Features

- **🎯 Dynamic Routing**: Intelligent Gemini-powered routing to specialist agents
- **🔧 Tool Integration**: Equation solving, formula lookup, and advanced calculations
- **📊 Comprehensive Logging**: Detailed execution tracking and debugging
- **⚡ Fast Performance**: Optimized with execution timing and caching
- **🌐 Production Ready**: Deployed on Railway/Vercel with proper CORS and health checks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Tutor Agent    │───▶│   Math Agent    │───▶│ Equation Solver │
│  (Coordinator)  │    │   (Specialist)  │    │ Calculator Tool │
└─────────────────┘    └─────────────────┘    │ Formula Lookup  │
         │                                     └─────────────────┘
         ▼
┌─────────────────┐    ┌─────────────────┐
│ Physics Agent   │───▶│ Formula Lookup  │
│ (Specialist)    │    │ Calculator Tool │
└─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**:
   ```bash
   git clone <your-repo>
   cd MultiAgentTutor
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

3. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Test the System**:
   ```bash
   curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "Solve 2x + 5 = 15"}'
   ```

### 🌐 Deployment

**For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)**

Quick Railway deployment:
1. Push to GitHub
2. Connect to Railway
3. Set `GEMINI_API_KEY` environment variable
4. Deploy automatically!

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System information and features |
| `/health` | GET | Health check endpoint |
| `/ask` | POST | Main tutoring endpoint |
| `/ask_direct/{agent}` | POST | Direct agent access |
| `/agents` | GET | List available agents |
| `/routing_info` | POST | Debug routing decisions |

### Example Usage

**Solve an Equation**:
```bash
curl -X POST "/ask" -d '{"query": "Solve 2x + 5 = 15"}'
```

**Get a Formula**:
```bash
curl -X POST "/ask" -d '{"query": "What is the formula for kinetic energy?"}'
```

**Physics Problem**:
```bash
curl -X POST "/ask" -d '{"query": "Calculate the force if mass is 5kg and acceleration is 2m/s²"}'
```

## 🔧 System Components

### Agents

- **🎯 Tutor Agent**: Main coordinator with Gemini-based routing
- **🔢 Math Agent**: Specialized for equations, calculations, formulas
- **⚡ Physics Agent**: Specialized for physics concepts and formulas

### Tools

- **🧮 Calculator**: Advanced mathematical calculations
- **⚖️ Equation Solver**: Algebraic equation solving
- **📖 Formula Lookup**: Math and physics formula database

### Features

- **📊 Comprehensive Logging**: Track every operation with detailed logs
- **⏱️ Execution Timing**: Monitor performance and response times
- **🎯 Dynamic Routing**: Gemini decides the best specialist for each query
- **🔧 Tool Calling**: Automatic tool selection and execution
- **🌐 Production Ready**: CORS, health checks, environment configuration

## 🧪 Testing Your Deployment

Use the provided test script:
```bash
python deployment_test.py https://your-app.railway.app
```

This will test:
- ✅ Health checks
- ✅ Equation solving with tools
- ✅ Formula lookup with tools
- ✅ Agent routing and responses

## 🔍 Logs and Debugging

The system provides detailed logging:

```
🎯 ROUTING DECISION
   Query: 'Solve 2x + 5 = 15'
   Action: delegate
   Target: Math Tutor
   Reasoning: This is an algebraic equation

🤖 MATH TUTOR STARTED
   Processing: 'Solve 2x + 5 = 15'

🔧 Available tools: equation_solver, calculator, formula_lookup

📞 FUNCTION CALL DETECTED
   Function: equation_solver
   Arguments: {'equation': '2x + 5 = 15'}

⚡ TOOL CALL: equation_solver
   Arguments: {'equation': '2x + 5 = 15'}
   Result: [5.0]

✅ MATH TUTOR COMPLETED
   Execution time: 5234.56ms
   Confidence: 0.90
```

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `ENVIRONMENT` | Deployment environment | Optional |
| `PORT` | Server port (Railway) | Optional |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides
- **Testing**: Use `deployment_test.py` to verify your deployment works correctly

---

Built with ❤️ using Google Gemini 2.0 Flash and FastAPI
