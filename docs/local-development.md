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

### Separate Development Servers

#### Backend Only

```bash
npm run dev:backend
# or
uvicorn getgather.api.main:app --reload --host 127.0.0.1 --port 8000
```

**Open in browser: `http://localhost:8000`**

#### Frontend Only

```bash
npm run dev:frontend
# or
vite
```

**Open in browser: `http://localhost:5173`**

## Building for Production

### Build Frontend

```bash
npm run build
```

This compiles TypeScript and builds the React app to `getgather/api/frontend/`.

### Run Production Build

```bash
# Start backend (serves built frontend)
uvicorn getgather.api.main:app --host 0.0.0.0 --port 8000
```

**Open in browser: `http://localhost:8000`**

In production mode, FastAPI serves both the API and the built frontend.

## Development Workflow

### Code Quality

```bash
npm run lint          # Lint code
npm run format        # Format code
npm run check-format  # Check formatting
npm run preview       # Preview production build
```

## File Structure

```
mcp-getgather/
├── frontend/              # React frontend source
│   ├── src/
│   ├── index.html
│   └── ...
├── getgather/
│   ├── api/
│   │   ├── frontend/     # Built frontend (generated)
│   │   └── main.py       # FastAPI server
│   └── ...
├── package.json          # Node.js dependencies
├── vite.config.ts        # Vite configuration
└── Dockerfile           # Multi-stage build
```

## Troubleshooting

### Port Conflicts

- **Backend**: Change port in `package.json` dev:backend script
- **Frontend**: Vite will automatically try alternative ports (5174, 5175, etc.)

### Build Issues

```bash
# Clear dependencies
rm -rf node_modules package-lock.json
npm install

# Clear build cache
npm run build
```

### Python Environment

```bash
# Verify Python version
python --version  # Should be 3.11+

# Reinstall dependencies
uv sync --reinstall
```
