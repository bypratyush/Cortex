import json
import logging
from datetime import datetime
from typing import Optional

import boto3
from apscheduler.schedulers.blocking import BlockingScheduler
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.assessment import AssessmentQuestion
from app.models.curriculum import Concept
from app.models.enums import DifficultyLevel, QuestionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuestionHarvester")


class GeneratedQuestion(BaseModel):
    question_type: str = Field(description="Must be 'MCQ' or 'CODING_EXERCISE'")
    prompt: str = Field(description="The question prompt or coding task description")
    choices: Optional[list[str]] = Field(default=None, description="Exactly 4 choices if MCQ. Null if CODING_EXERCISE.")
    starter_code: Optional[str] = Field(default=None, description="Boilerplate python code if CODING_EXERCISE. Null if MCQ.")
    expected_answer: str = Field(description="The correct choice letter if MCQ. The hidden python 'assert' tests if CODING_EXERCISE.")
    explanation: str = Field(description="A brief explanation of why the answer is correct")
    difficulty: str = Field(description="One of: EASY, MEDIUM, HARD")


class LLMResponse(BaseModel):
    questions: list[GeneratedQuestion]


def generate_questions_with_bedrock(concept_name: str, count: int) -> list[GeneratedQuestion]:
    """
    Calls AWS Bedrock (using Amazon Nova) to generate questions via the Converse API.
    Generates a mix of MCQs and Coding Exercises.
    """
    client = boto3.client(
        'bedrock-runtime',
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key
    )
    model_id = "amazon.nova-micro-v1:0"
    
    prompt = f"""
    You are an expert Python tutor. Generate {count} questions about "{concept_name}".
    Generate a mix of 'MCQ' (Multiple Choice) and 'CODING_EXERCISE' (Programming tasks).
    
    Rules for CODING_EXERCISE:
    - 'prompt' should clearly state what the python function should do.
    - 'starter_code' MUST contain the python function signature, e.g. "def add(a, b):\n    # Write code here".
    - 'expected_answer' MUST be purely hidden python assert statements to test their code, e.g. "assert add(1, 2) == 3".
    - 'choices' must be null.
    
    Rules for MCQ:
    - 'choices' must be a list of exactly 4 strings.
    - 'expected_answer' must exactly match one of the strings in the choices array.
    - 'starter_code' must be null.

    Return the response ONLY as valid JSON matching this schema:
    {{
      "questions": [
        {{
          "question_type": "CODING_EXERCISE",
          "prompt": "Write a function...",
          "choices": null,
          "starter_code": "def my_func():",
          "expected_answer": "assert my_func() == True",
          "explanation": "...",
          "difficulty": "EASY"
        }}
      ]
    }}
    Do not include any markdown formatting, code blocks, or extra text. Just output raw JSON.
    """
    
    try:
        response = client.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }],
            inferenceConfig={
                "maxTokens": 3000,
                "temperature": 0.4
            }
        )
        
        raw_text = response['output']['message']['content'][0]['text']
        raw_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
        
        parsed_json = json.loads(raw_text)
        validated_data = LLMResponse(**parsed_json)
        return validated_data.questions
    except Exception as e:
        logger.error(f"Failed to generate questions for {concept_name}: {e}")
        return []


def harvest_questions():
    logger.info(f"Starting Question Harvester run at {datetime.now()}")
    db: Session = SessionLocal()
    
    try:
        concepts = db.scalars(select(Concept).where(Concept.is_active == True)).all()
        
        for concept in concepts:
            count = db.scalar(
                select(func.count(AssessmentQuestion.id))
                .where(AssessmentQuestion.concept_id == concept.id, AssessmentQuestion.is_approved == True)
            ) or 0
            
            if count < 50:
                logger.info(f"Concept '{concept.name}' has only {count} questions. Generating 5 more...")
                generated = generate_questions_with_bedrock(concept.name, 5)
                
                for q in generated:
                    diff_map = {
                        "EASY": DifficultyLevel.EASY,
                        "MEDIUM": DifficultyLevel.MEDIUM,
                        "HARD": DifficultyLevel.HARD
                    }
                    
                    q_type = QuestionType.MCQ if q.question_type == "MCQ" else QuestionType.CODING_EXERCISE
                    
                    db_question = AssessmentQuestion(
                        concept_id=concept.id,
                        difficulty=diff_map.get(q.difficulty.upper(), DifficultyLevel.EASY),
                        question_type=q_type,
                        prompt=q.prompt,
                        choices=q.choices,
                        starter_code=q.starter_code,
                        expected_answer=q.expected_answer,
                        explanation=q.explanation,
                        is_active=True,
                        is_approved=False
                    )
                    db.add(db_question)
                
                db.commit()
                logger.info(f"Successfully saved {len(generated)} unapproved questions for '{concept.name}'.")
                
    except Exception as e:
        logger.error(f"Harvester job failed: {e}")
        db.rollback()
    finally:
        db.close()
        logger.info("Harvester run complete.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        harvest_questions()
    else:
        scheduler = BlockingScheduler()
        scheduler.add_job(harvest_questions, 'cron', hour='0,12', minute=0)
        logger.info("Starting APScheduler. Waiting for next cron interval (12 AM / 12 PM)...")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass
