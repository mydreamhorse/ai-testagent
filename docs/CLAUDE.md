# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a car seat software testing agent that uses AI to automatically generate test cases and evaluate their quality. The system consists of a FastAPI backend, Vue.js frontend, and AI models for requirement parsing, test case generation, and quality evaluation.

## Architecture

- **Backend**: Python FastAPI application in `/backend/`
- **Frontend**: Vue.js 3 + TypeScript application in `/frontend/`
- **AI Components**: Located in `/backend/ai/` containing requirement parser, test case generator, and quality evaluator
- **Database**: SQLAlchemy with SQLite (configurable to PostgreSQL)
- **Cache**: Redis for caching and async task queues (Celery)

## Development Commands

### Backend Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run development server
cd backend && python main.py
# Or with uvicorn directly:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run tests (when test files exist)
pytest tests/ --cov=backend --cov-report=html

# Code formatting and linting
black backend/
flake8 backend/
isort backend/
```

### Frontend Development
```bash
# Install Node.js dependencies
cd frontend && npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Linting and type checking
npm run lint
npm run type-check
```

## Key Components

### Backend Structure
- `main.py`: FastAPI application entry point with CORS and router configuration
- `config.py`: Application settings using Pydantic Settings
- `models.py`: SQLAlchemy database models
- `database.py`: Database connection and session management
- `schemas.py`: Pydantic schemas for API request/response validation
- `routers/`: API route handlers for different modules (auth, requirements, test_cases, etc.)
- `ai/`: AI-related modules
  - `requirement_parser.py`: Parses requirement documents
  - `test_case_generator.py`: Generates test cases from requirements
  - `quality_evaluator.py`: Evaluates test case quality with multi-dimensional scoring

### Frontend Structure
- Vue 3 with Composition API and TypeScript
- Pinia for state management
- Vue Router for routing
- Element Plus for UI components
- ECharts for data visualization
- Axios for API communication

## Configuration

- Backend configuration is in `backend/config.py` using environment variables or `.env` file
- Database URL, Redis URL, OpenAI API key, and other settings are configurable
- Default database is SQLite for development, can be changed to PostgreSQL for production
- API endpoints are prefixed with `/api/v1`

## AI Model Integration

The system integrates with various AI models:
- Uses transformers library for NLP tasks
- OpenAI GPT models for test case generation
- Custom trained models for quality evaluation
- Model files cached in `models/` directory

## Quality Evaluation Scoring

Test cases are evaluated on 5 dimensions (100 points total):
- Completeness (25 points): Preconditions, steps, expected results
- Accuracy (25 points): Technical terms, operation steps, expected results  
- Executability (20 points): Step operability, result verifiability
- Coverage (20 points): Function coverage, scenario coverage
- Clarity (10 points): Language clarity, structural organization

## Common Tasks

When working on this codebase:
1. Backend changes require restarting the FastAPI server
2. Database schema changes need migration scripts (Alembic)
3. AI model changes may require retraining and cache clearing
4. Frontend changes are hot-reloaded in development
5. API changes should update both backend routes and frontend API calls
6. New dependencies should be added to requirements.txt (backend) or package.json (frontend)

## Testing

- Backend: Use pytest for unit and integration tests
- Frontend: Test commands available via npm scripts
- Coverage reports generated for both backend and frontend
- AI model performance should be evaluated against expert-labeled data