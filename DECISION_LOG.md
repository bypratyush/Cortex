# Architecture & Implementation Decision Log

This document outlines the reasoning behind the architectural choices and technical decisions made during the integration of the AI features (Learner Profile, Lesson Generation, Quiz Generation, Curriculum Engine, and Socratic Tutor) into the Cortex platform.

## 1. Centralized LLM Service (`backend/app/services/llm.py`)
- **Decision:** All prompts and interactions with the AI models (AWS Bedrock) were centralized into a single `llm.py` service.
- **Reasoning:** Centralizing the LLM calls provides a single point of failure and a single place to implement cross-cutting concerns (such as retry logic, rate limiting, and logging). It significantly improves testability, as we only need to mock this one service instead of mocking API calls across 5 different service files.
- **Alternative Considered:** Calling AWS Bedrock (or another provider) directly inside `tutor.py`, `quiz.py`, `lesson.py`, etc. This was rejected because it violates the DRY (Don't Repeat Yourself) principle and makes swapping out LLM providers in the future much harder.

## 2. Lightweight JSON Parsing & Pydantic Validation
- **Decision:** We instructed the LLM to return plain JSON arrays/objects in its response and used simple string manipulation (stripping markdown backticks) combined with Python's native `json` library and Pydantic schemas.
- **Reasoning:** This is a highly portable, platform-agnostic approach that does not rely on a specific provider's function-calling or structured-output APIs. The LLM simply returns text, which we parse and immediately validate against our strictly defined Pydantic schemas to ensure data integrity before it reaches the database.
- **Alternative Considered:** Using heavier frameworks like LangChain or provider-specific tools (like OpenAI function calling). This was avoided to keep the dependency graph small, fast, and completely decoupled from specific AI vendor lock-in.

## 3. Database Migrations via Alembic
- **Decision:** When we needed to add `structured_understanding` to the `LearnerProfile` and a `roadmap` column to the `LearningPath`, we used Alembic to auto-generate and apply the migration scripts.
- **Reasoning:** Managing schema changes via migrations ensures that the database schema is version-controlled. This guarantees that anyone cloning the repository can quickly set up their database and that production deployments won't require manual table alterations.
- **Alternative Considered:** Manually executing SQL `ALTER TABLE` commands or dropping and recreating the database. This was rejected as it leads to data loss and "drift" between local and production environments.

## 4. Strict Enum Usage over Magic Strings
- **Decision:** When fixing the `AttributeError` in the `TutorService`, we explicitly wired the message history to use the `TutorMessageRole.LEARNER` and `TutorMessageRole.TUTOR` enums instead of raw strings like `"USER"` or `"ASSISTANT"`.
- **Reasoning:** Python Enums enforce type safety at the application level. Using them ensures that our code strictly adheres to the domain logic defined in the `models/enums.py` file, catching typos and invalid states before they reach the database.

## 5. Separating "Socratic" Logic from the Main Prompt
- **Decision:** The Socratic Tutor uses a dynamic "hint escalation" strategy based on an `attempt_count` parameter that increments, rather than hardcoding all the logic in one giant static prompt.
- **Reasoning:** This ensures the tutor actually adapts over time. By tracking `attempt_count` and passing it dynamically, we force the LLM to give more direct help when the learner struggles repeatedly, mimicking a real educator.
