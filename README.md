# Process Monitor Dashboard

A comprehensive system for monitoring running processes on Windows machines with a web-based dashboard interface.

## Project Overview

This project consists of three main components:

1. **Agent (EXE)**: A standalone Windows executable that collects process information  
2. **Backend (Django)**: REST API server that receives and stores process data  
3. **Frontend**: Web interface for viewing process hierarchies and system information

## Architecture

```
Windows Machine (Agent) → Django Backend → Web Frontend
     ↓                        ↓              ↓
Process Data           SQLite Database   Process Tree
Collection            Storage           Visualization
```

## Prerequisites

- Python 3.8+
- Django 4.2+
- Windows machine for the agent
- Modern web browser for the frontend

## Clone the Repository

```bash
git clone https://github.com/gungunkhandelwal/Process-Monitoring-Agent.git
```

## Quick Start

### 1. One-Command Setup

You can set up the backend, install dependencies, run migrations, and create an API key automatically using the provided quick start script:

```bash
python quick_start.py
```

- This script will:
  - Install all dependencies (from `requirements.txt` if available)
  - Run Django migrations
  - Create an API key for the agent and update `agent/config.json`
  - Optionally start the Django server for you

**If you choose not to start the server automatically, you can do so manually:**

```bash
cd cyethack
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

---

### 2. Agent Setup

```bash
cd agent

pip install -r requirments.txt

python system_monitor_agent.py
```

---

### 3. Build Agent EXE (Optional)

```bash
python build_agent.py

```

---

### 4. Frontend Access

Open your browser and navigate to `http://localhost:8000`

---

## Setup Instructions

### Backend Configuration

1. **Database**: SQLite is used by default (no additional setup required)
2. **API Keys**: Use the management command or quick start script to create keys
3. **CORS**: Configured for local development

### Agent Configuration

The agent uses `config.json` for configuration:

```json
{
  "api_url": "http://localhost:8000/api",
  "api_key": "your-api-key-here",
  "collection_interval": 60,
  "include_system_processes": true,
  "max_processes": 1000
}
```

### Frontend Features

- **Process Tree**: Subprocess view of running processes
- **Search**: Filter processes by name, PID, or command line
- **Host Management**: Support for multiple monitored machines

## API Endpoints

### Agent Endpoints
- `POST /api/submit/` - Submit process data

### Frontend Endpoints
- `GET /api/hosts/` - List all monitored hosts
- `GET /api/hosts/{hostname}/processes/` - Get process for a host
- `GET /api/hosts/{hostname}/snapshots/` - Get process snapshots for a host
- `GET /api/status/` - System status info

## Data Collection

The agent collects:
- Process name and PID
- Parent-child relationships
- CPU and memory usage
- Process status and username
- Command line information
- Creation timestamps

## Security

- API key authentication for agent communication
- CORS configuration for frontend access
- Input validation and sanitization

## Development

### Project Structure

```
Cyethack/
├── agent/           
├── cyethack/          
│   ├── process_monitor/  
│   └── manage.py        
├── templates/            
├── requirements.txt      
├── quick_start.py        
└── build_agent.py        