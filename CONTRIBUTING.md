# Contributing to Cortex

First off, thank you for considering contributing to Cortex! We welcome contributions from everyone—whether you're fixing a bug, improving the Socratic Tutor logic, or adding new features to the frontend.

## Project Structure

Cortex is a monorepo consisting of two main parts:
- **`frontend/`**: The Next.js application (App Router), built with TypeScript, Tailwind CSS, and shadcn/ui.
- **`backend/`**: The FastAPI server (Python), using SQLAlchemy for ORM and PostgreSQL.

## Getting Started

To get the project running locally, follow these steps:

### 1. Fork and Clone
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Cortex.git
   cd Cortex
   ```

### 2. Frontend Setup
Make sure you have [Node.js](https://nodejs.org/) installed (v18+ recommended).
```bash
cd frontend
npm install
npm run dev
```
The frontend will be running at `http://localhost:3000`.

### 3. Backend Setup
Make sure you have Python 3.10+ installed.
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev main.py
```
The backend API docs will be available at `http://localhost:8000/docs`.

### 4. Database & Environment Variables
- You will need a PostgreSQL database (e.g., Supabase, Neon, or local Docker).
- Copy the environment variable templates (`.env.example` -> `.env`) in both the frontend and backend directories and fill in the required keys (like Database connection strings and Clerk Auth API keys).

## How to Contribute

1. **Create a branch**: `git checkout -b feature/your-feature-name` or `fix/your-fix-name`.
2. **Make your changes**: Write clean, readable code.
3. **Commit your changes**: Please use clear, descriptive commit messages.
   ```bash
   git commit -m "Add adaptive path recalculation logic"
   ```
4. **Push to your fork**: `git push origin feature/your-feature-name`.
5. **Open a Pull Request**: Go to the main Cortex repository and open a Pull Request against the `main` branch. Provide a clear description of what your PR solves or adds.

## Code Style Guidelines

- **Frontend**: We use ESLint and Prettier. Please run `npm run lint` before committing to ensure there are no formatting or linting errors. Use the existing Tailwind and shadcn/ui patterns for styling.
- **Backend**: Ensure your code follows PEP 8 standards. Use type hints for all function arguments and return types. 

## Reporting Bugs

If you find a bug, please open an Issue on GitHub with:
- A clear title and description.
- Steps to reproduce the issue.
- Expected behavior vs. actual behavior.
- Relevant screenshots or logs.

Thank you for helping make Cortex better!
