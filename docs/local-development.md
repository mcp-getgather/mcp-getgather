# Local Development Setup

## Prerequisites

- Python 3.11+ (project requires >= 3.11)
- Node.js 22+
- npm

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/mcp-getgather/mcp-getgather.git
cd mcp-getgather
```

### 2. Install Dependencies

#### Python Dependencies

```bash
# Using uv
uv sync
```

#### Node.js Dependencies

```bash
npm install
```

## Running the Application

### Development Mode

Run both frontend and backend:

```bash
npm run dev
```

**Open in browser: `http://localhost:5173`**

### MCP configuration

```json
{
  "mcpServers": {
    "getgather": {
      "url": "http://localhost:5173/mcp"
    }
  }
}
```

### Development

```bash
npm run dev
# or
uv run -m uvicorn getgather.main:app --reload --host 127.0.0.1 --port 23456
```

### Code Quality

```bash
npm run format        # Format code
npm run check-format  # Check formatting
```

## File Structure

```
mcp-getgather/
├── getgather/
│   ├── frontend/         # Static frontend
│   ├── main.py           # FastAPI server
│   └── ...
├── package.json          # Node.js dependencies
└── Dockerfile            # Multi-stage build
```

## Troubleshooting

### Build Issues

```bash
# Clear dependencies
rm -rf node_modules package-lock.json
npm install
```

### Python Environment

```bash
# Verify Python version
python --version  # Should be 3.11+

# Reinstall dependencies
uv sync --reinstall
```
