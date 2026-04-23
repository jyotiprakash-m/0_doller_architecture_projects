# Ghost-Editor — AI Documentation Agent

Intelligent AI agent for automated documentation maintenance. $0 cost, local-first documentation management.

## Project Structure

- `backend/`: FastAPI server for processing webhooks and managing repos.
- `frontend/`: Next.js dashboard for monitoring agent activity.

## Testing

### Backend Testing (Python)

1.  **Install dependencies**:
    ```bash
    cd backend
    pip install -r requirements.txt
    ```
2.  **Run tests**:
    ```bash
    pytest
    ```

### Frontend Testing (TypeScript)

1.  **Install dependencies**:
    ```bash
    cd frontend
    npm install
    ```
2.  **Run tests**:
    ```bash
    npm test
    ```

### Manual Verification

#### Backend Health Check
```bash
curl http://localhost:8000/api/health
```

#### GitHub Webhook Simulation
```bash
curl -X POST http://localhost:8000/api/webhooks/github \
  -H "X-GitHub-Event: ping" \
  -H "Content-Type: application/json" \
  -d '{"zen": "Keep it simple"}'
```

## Running the Project

### Start Backend
```bash
cd backend
python main.py
```

### Start Frontend
```bash
cd frontend
npm run dev
```
