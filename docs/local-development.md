# Local Development Setup

## Prerequisites

- Python 3.11+ (project requires >= 3.11)
- Node.js 22+
- npm

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd mcp-getgather
```

### 2. Install Dependencies

#### Python Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
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

Starts:

- Backend: FastAPI server on `http://localhost:8000`
- Frontend: Vite dev server on `http://localhost:5173`

Frontend proxies API calls to backend.

### Separate Development Servers

#### Backend Only

```bash
npm run dev:backend
# or
uvicorn getgather.api.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend Only

```bash
npm run dev:frontend
# or
vite
```

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

Frontend will be available at `http://localhost:8000`.

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

- Backend: Change port in `package.json` dev:backend script
- Frontend: Set `--port` flag: `vite --port 3000`

### Build Issues

```bash
# Clear dependencies
rm -rf node_modules package-lock.json
npm install

# Clear build cache
rm -rf getgather/api/frontend
npm run build
```

### Python Environment

```bash
# Verify Python version
python --version  # Should be 3.11+

# Reinstall dependencies
uv sync --reinstall
```
