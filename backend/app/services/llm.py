import json
import logging
import boto3
from app.core.config import settings

logger = logging.getLogger("CortexLLM")


def analyze_learner_profile(
    goal: str,
    motivation: str,
    learning_style: str,
    target_proficiency: str,
    assessment_results: str
) -> dict:
    """
    Executes Prompt 1 to analyze the learner's profile and initial assessment.
    Returns a parsed JSON object matching the Prompt 1 response schema.
    """
    prompt = f"""You are Cortex, an adaptive learning coach.

A new learner has provided their profile. Analyze it and return a structured understanding of this learner that will be used by all other AI modules.

Input:
- Goal: {goal}
- Motivation: {motivation}
- Learning Style: {learning_style}
- Target Proficiency: {target_proficiency}
- Assessment Results: {assessment_results}

Return a JSON object with the following fields:
{{
  "goal": string,
  "motivation": string,
  "style": "visual" | "hands-on" | "reading" | "auditory",
  "target_level": "beginner" | "intermediate" | "advanced",
  "current_level": "beginner" | "intermediate" | "advanced",
  "strengths": [string],
  "gaps": [string],
  "pace_preference": "slow" | "moderate" | "fast",
  "teaching_notes": string
}}

teaching_notes should be a short paragraph that guides how lessons and tutoring should be adapted for this specific learner. Be specific, not generic.

Return only valid JSON. No preamble."""

    # Check if AWS credentials are configured
    has_aws_creds = (
        settings.aws_access_key_id is not None
        and settings.aws_secret_access_key is not None
        and settings.aws_default_region is not None
    )

    if not has_aws_creds:
        logger.warning("AWS credentials not configured. Falling back to local mock profile analysis.")
        return _generate_mock_analysis(goal, motivation, learning_style, target_proficiency, assessment_results)

    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        # We use amazon.nova-micro-v1:0 as standard, matching question_harvester.py
        model_id = "amazon.nova-micro-v1:0"

        response = client.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.3
            }
        )

        raw_text = response['output']['message']['content'][0]['text'].strip()
        
        # Strip potential markdown formatting
        if raw_text.startswith("```json"):
            raw_text = raw_text.removeprefix("```json").removesuffix("```").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.removeprefix("```").removesuffix("```").strip()

        data = json.loads(raw_text)
        return _validate_and_sanitize_analysis(data, goal, motivation)

    except Exception as e:
        logger.error(f"Failed to generate profile analysis via Bedrock: {e}. Falling back to mock data.")
        return _generate_mock_analysis(goal, motivation, learning_style, target_proficiency, assessment_results)


def _validate_and_sanitize_analysis(data: dict, fallback_goal: str, fallback_motivation: str) -> dict:
    """Ensure all expected keys exist and have valid values according to the spec."""
    sanitized = {}

    sanitized["goal"] = str(data.get("goal", fallback_goal))
    sanitized["motivation"] = str(data.get("motivation", fallback_motivation))

    style = str(data.get("style", "")).lower().strip()
    if style not in ["visual", "hands-on", "reading", "auditory"]:
        sanitized["style"] = "hands-on"
    else:
        sanitized["style"] = style

    for lvl_field in ["target_level", "current_level"]:
        lvl = str(data.get(lvl_field, "")).lower().strip()
        if lvl not in ["beginner", "intermediate", "advanced"]:
            sanitized[lvl_field] = "beginner" if lvl_field == "current_level" else "intermediate"
        else:
            sanitized[lvl_field] = lvl

    sanitized["strengths"] = [str(x) for x in data.get("strengths", []) if isinstance(x, (str, int, float))]
    sanitized["gaps"] = [str(x) for x in data.get("gaps", []) if isinstance(x, (str, int, float))]

    pace = str(data.get("pace_preference", "")).lower().strip()
    if pace not in ["slow", "moderate", "fast"]:
        sanitized["pace_preference"] = "moderate"
    else:
        sanitized["pace_preference"] = pace

    sanitized["teaching_notes"] = str(data.get("teaching_notes", "Adapt lessons to focus on practical coding exercises and step-by-step guidance."))
    
    return sanitized


def _generate_mock_analysis(
    goal: str,
    motivation: str,
    learning_style: str,
    target_proficiency: str,
    assessment_results: str
) -> dict:
    """Generates a realistic analysis structure locally as a fallback."""
    # Infer style
    style_map = {
        "practice": "hands-on",
        "reading": "reading",
        "examples": "visual",
        "mixed": "hands-on"
    }
    inferred_style = style_map.get(learning_style.lower(), "hands-on")

    # Infer target level
    target_lvl_map = {
        "beginner": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
        "job_ready": "advanced"
    }
    inferred_target = target_lvl_map.get(target_proficiency.lower(), "intermediate")

    # Analyze assessment results for strengths/gaps
    strengths = []
    gaps = []
    current_level = "beginner"

    try:
        # Simplistic parsing of assessment results text to identify correct vs incorrect concepts
        lines = assessment_results.split("\n")
        correct_count = 0
        total_count = 0
        for line in lines:
            if ":" in line:
                parts = line.split(":")
                concept = parts[0].strip().replace("-", "").strip()
                outcome = parts[1].strip().lower()
                total_count += 1
                if "correct" in outcome or "1.0" in outcome or "100%" in outcome:
                    strengths.append(concept)
                    correct_count += 1
                else:
                    gaps.append(concept)
        
        if total_count > 0:
            ratio = correct_count / total_count
            if ratio > 0.75:
                current_level = "intermediate"
            elif ratio > 0.4:
                current_level = "intermediate"
            else:
                current_level = "beginner"
    except Exception:
        pass

    if not strengths:
        strengths = ["Basic Syntax", "Sequential execution"]
    if not gaps:
        gaps = ["Control Flow", "Object-Oriented Programming"]

    teaching_notes = (
        f"This learner is driven by {motivation.lower() or 'personal development'} to achieve '{goal}'. "
        f"They benefit most from a {inferred_style} approach. Tutoring should bridge gaps in "
        f"{', '.join(gaps[:2])} before advancing, pacing lessons at a moderate speed to build solid fundamentals."
    )

    return {
        "goal": goal,
        "motivation": motivation,
        "style": inferred_style,
        "target_level": inferred_target,
        "current_level": current_level,
        "strengths": strengths,
        "gaps": gaps,
        "pace_preference": "moderate",
        "teaching_notes": teaching_notes
    }


def generate_personalized_lesson(
    concept_name: str,
    concept_description: str,
    learner_profile_json: str,
    mastery_level: int
) -> dict:
    """
    Executes Prompt 2 to generate a personalized lesson.
    Parses the markdown headers into a structured dict payload.
    """
    prompt = f"""You are an expert educator inside Cortex, an adaptive learning platform.

Generate a personalized lesson for the concept below, tailored to the learner profile provided.

Concept: Name: {concept_name}
Description: {concept_description}
Learner Profile: {learner_profile_json}
Mastery Level on this concept: {mastery_level} (0–100)

Rules:
- If mastery < 30, treat the learner as a beginner. Use the simplest possible language.
- If mastery 30–70, treat as intermediate. Introduce nuance and edge cases.
- If mastery > 70, treat as advanced. Focus on depth, trade-offs, and real-world complexity.
- Prefer examples over theory.
- Match the learner's style from their profile (hands-on → code examples; visual → analogies and diagrams described in words; reading → structured explanations).
- Never write more than the learner needs.

Output the lesson in this exact structure:

## Overview
[2–3 sentence plain-language explanation of the concept]

## Analogy
[A relatable real-world analogy tailored to the learner's background and goal]

## Example
[A concrete example. If the learner's goal is technical, include a code snippet.]

## Common Mistakes
[2–3 misconceptions or errors learners typically make with this concept]

## Practice Question
[One question that requires the learner to apply — not recall — this concept]"""

    has_aws_creds = (
        settings.aws_access_key_id is not None
        and settings.aws_secret_access_key is not None
        and settings.aws_default_region is not None
    )

    if not has_aws_creds:
        logger.warning("AWS credentials not configured. Falling back to local mock lesson generation.")
        return _generate_mock_lesson(concept_name, concept_description, learner_profile_json, mastery_level)

    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        model_id = "amazon.nova-micro-v1:0"

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
        return parse_markdown_lesson(raw_text)

    except Exception as e:
        logger.error(f"Failed to generate personalized lesson via Bedrock: {e}. Falling back to mock data.")
        return _generate_mock_lesson(concept_name, concept_description, learner_profile_json, mastery_level)


def parse_markdown_lesson(text: str) -> dict:
    import re
    patterns = {
        "overview": re.compile(r"(?i)(?:^|\n)(?:##+|#|\*\*)\s*Overview\s*(?:\*\*|:)?\s*\n"),
        "analogy": re.compile(r"(?i)(?:^|\n)(?:##+|#|\*\*)\s*Analogy\s*(?:\*\*|:)?\s*\n"),
        "example": re.compile(r"(?i)(?:^|\n)(?:##+|#|\*\*)\s*Example\s*(?:\*\*|:)?\s*\n"),
        "common_mistakes": re.compile(r"(?i)(?:^|\n)(?:##+|#|\*\*)\s*(?:Common\s+Mistakes|Mistakes)\s*(?:\*\*|:)?\s*\n"),
        "practice_question": re.compile(r"(?i)(?:^|\n)(?:##+|#|\*\*)\s*(?:Practice\s+Question|Question)\s*(?:\*\*|:)?\s*\n")
    }
    
    indices = []
    for key, regex in patterns.items():
        match = regex.search(text)
        if match:
            indices.append((key, match.start(), match.end()))
            
    indices.sort(key=lambda x: x[1])
    
    parsed = {
        "overview": "",
        "analogy": "",
        "example": "",
        "common_mistakes": "",
        "practice_question": ""
    }
    
    for i in range(len(indices)):
        key, start, end = indices[i]
        next_start = indices[i+1][1] if i + 1 < len(indices) else len(text)
        content = text[end:next_start].strip()
        parsed[key] = content
        
    if not any(parsed.values()):
        parsed["overview"] = text
        
    return parsed


def _generate_mock_lesson(
    concept_name: str,
    concept_description: str,
    learner_profile_json: str,
    mastery_level: int
) -> dict:
    style = "hands-on"
    try:
        profile_data = json.loads(learner_profile_json)
        style = profile_data.get("style", "hands-on")
    except Exception:
        pass

    level = "beginner"
    if mastery_level > 70:
        level = "advanced"
    elif mastery_level >= 30:
        level = "intermediate"

    overview = f"This is a personalized {level} overview for {concept_name}. {concept_description or 'It is a crucial programming concept.'}"
    
    if style == "hands-on":
        analogy = f"Think of {concept_name} like a mechanical lever in a factory. You pull the level to trigger a specific process."
        example = f"# Hands-on {level} Example for {concept_name}\n"
        if level == "beginner":
            example += "x = 10\nprint(x)\n# Simple and direct variable definition."
        elif level == "intermediate":
            example += "def process(val):\n    return val * 2\n\nprint(process(10)) # Adding function boundaries."
        else:
            example += "class ProcessPipeline:\n    def __init__(self, val):\n        self.val = val\n    def execute(self):\n        return self.val * 2\n# Advanced OOP structure."
    else:
        analogy = f"Imagine a tree structure where {concept_name} represents branching paths to different outcomes."
        example = f"Visual description of {concept_name} in action: [Diagram: Root -> Left Branch / Right Branch]"

    common_mistakes = (
        f"1. Forgetting boundary conditions when working with {concept_name}.\n"
        f"2. Incorrect syntax or type mismatches when executing operations."
    )
    
    practice_question = f"Apply your understanding of {concept_name} to solve: write a python code chunk that handles boundary conditions correctly."

    return {
        "overview": overview,
        "analogy": analogy,
        "example": example,
        "common_mistakes": common_mistakes,
        "practice_question": practice_question
    }


def generate_personalized_quiz(
    concept_name: str,
    concept_description: str,
    learner_profile_json: str,
    mastery_level: int
) -> list[dict]:
    """
    Executes Prompt 3 to generate a personalized quiz.
    Returns a parsed list of JSON objects matching the dynamic quiz schema.
    """
    prompt = f"""You are a quiz designer inside Cortex, an adaptive learning platform.

Generate a concept-specific quiz based on the inputs below.

Concept: Name: {concept_name}
Description: {concept_description}
Learner Profile: {learner_profile_json}
Mastery Level: {mastery_level} (0–100)

Requirements:
- Generate exactly 5 questions: 3 MCQs, 1 Conceptual, 1 Application-based.
- Questions must increase in difficulty from Q1 to Q5.
- Questions must test understanding, not memorization.
- Adapt difficulty ceiling to mastery level:
  - mastery < 30 → keep questions foundational
  - mastery 30–70 → include reasoning and "why" questions
  - mastery > 70 → include edge cases, trade-offs, and real-world application

Return a JSON array:
[
  {{
    "id": 1,
    "type": "mcq",
    "question": string,
    "options": {{ "A": string, "B": string, "C": string, "D": string }},
    "correct": "A" | "B" | "C" | "D",
    "explanation": string
  }},
  {{
    "id": 4,
    "type": "conceptual",
    "question": string,
    "sample_answer": string,
    "evaluation_hint": string
  }},
  {{
    "id": 5,
    "type": "application",
    "question": string,
    "sample_answer": string,
    "evaluation_hint": string
  }}
]

Return only valid JSON. No preamble."""

    has_aws_creds = (
        settings.aws_access_key_id is not None
        and settings.aws_secret_access_key is not None
        and settings.aws_default_region is not None
    )

    if not has_aws_creds:
        logger.warning("AWS credentials not configured. Falling back to local mock quiz generation.")
        return _generate_mock_quiz(concept_name, concept_description, learner_profile_json, mastery_level)

    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        model_id = "amazon.nova-micro-v1:0"

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

        raw_text = response['output']['message']['content'][0]['text'].strip()
        
        # Strip potential markdown formatting
        if raw_text.startswith("```json"):
            raw_text = raw_text.removeprefix("```json").removesuffix("```").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.removeprefix("```").removesuffix("```").strip()

        data = json.loads(raw_text)
        if not isinstance(data, list):
            raise ValueError("Expected a list of questions")
            
        return _validate_and_sanitize_quiz(data)

    except Exception as e:
        logger.error(f"Failed to generate personalized quiz via Bedrock: {e}. Falling back to mock data.")
        return _generate_mock_quiz(concept_name, concept_description, learner_profile_json, mastery_level)


def _validate_and_sanitize_quiz(questions: list) -> list[dict]:
    sanitized = []
    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue
        q_type = str(q.get("type", "mcq")).lower().strip()
        if q_type not in ["mcq", "conceptual", "application"]:
            q_type = "mcq"

        sq = {
            "id": int(q.get("id", idx)),
            "type": q_type,
            "question": str(q.get("question", "Solve this challenge.")),
        }

        if q_type == "mcq":
            options = q.get("options", {})
            if not isinstance(options, dict) or not all(k in options for k in ["A", "B", "C", "D"]):
                options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
            sq["options"] = {k: str(v) for k, v in options.items()}
            
            correct = str(q.get("correct", "A")).upper().strip()
            if correct not in ["A", "B", "C", "D"]:
                correct = "A"
            sq["correct"] = correct
            sq["explanation"] = str(q.get("explanation", "No explanation provided."))
        else:
            sq["sample_answer"] = str(q.get("sample_answer", "This is the sample answer."))
            sq["evaluation_hint"] = str(q.get("evaluation_hint", "Use reasoning in your solution."))

        sanitized.append(sq)
        
    while len(sanitized) < 5:
        sanitized.append({
            "id": len(sanitized) + 1,
            "type": "mcq",
            "question": "Question content filler.",
            "options": {"A": "Correct", "B": "Incorrect", "C": "Incorrect", "D": "Incorrect"},
            "correct": "A",
            "explanation": "Padded question explanation."
        })
        
    return sanitized[:5]


def _generate_mock_quiz(
    concept_name: str,
    concept_description: str,
    learner_profile_json: str,
    mastery_level: int
) -> list[dict]:
    level = "beginner"
    if mastery_level > 70:
        level = "advanced"
    elif mastery_level >= 30:
        level = "intermediate"

    q1_text = f"Q1 ({level}): Which of the following is correct syntax for {concept_name}?"
    q2_text = f"Q2 ({level}): What is the primary purpose of {concept_name}?"
    q3_text = f"Q3 ({level}): What happens when you execute {concept_name} under normal conditions?"
    
    q4_text = f"Q4 ({level}): Explain in your own words why {concept_name} is useful and how it is structured."
    q5_text = f"Q5 ({level}): Write a python statement or script implementing {concept_name} to handle boundary cases."

    return [
        {
            "id": 1,
            "type": "mcq",
            "question": q1_text,
            "options": {"A": "Correct Syntax option", "B": "Syntax error option", "C": "Mismatched indent option", "D": "Deprecated style option"},
            "correct": "A",
            "explanation": f"Correct syntax is required to run {concept_name} successfully."
        },
        {
            "id": 2,
            "type": "mcq",
            "question": q2_text,
            "options": {"A": "To perform core logic operations", "B": "To delete files", "C": "To build hardware components", "D": "To import external web protocols only"},
            "correct": "A",
            "explanation": f"The primary goal of {concept_name} is logic execution."
        },
        {
            "id": 3,
            "type": "mcq",
            "question": q3_text,
            "options": {"A": "It executes and updates the runtime stack state", "B": "It triggers compile errors", "C": "It does nothing", "D": "It terminates the entire operating system"},
            "correct": "A",
            "explanation": f"Executing {concept_name} alters state."
        },
        {
            "id": 4,
            "type": "conceptual",
            "question": q4_text,
            "sample_answer": f"Conceptual answer detailing structure of {concept_name} for {level}.",
            "evaluation_hint": f"Look for key terms like '{concept_name}', state changes, and logic flow."
        },
        {
            "id": 5,
            "type": "application",
            "question": q5_text,
            "sample_answer": "def my_func(val):\n    # implementation of Variables and Assignments logic\n    pass",
            "evaluation_hint": "Check that assert assertions or return matches boundary requirements."
        }
    ]


def generate_curriculum_roadmap(
    goal: str,
    mastery_scores_json: str,
    knowledge_graph_json: str
) -> dict:
    """
    Executes Prompt 4 to generate a personalized curriculum roadmap.
    Returns the parsed JSON response payload.
    """
    prompt = f"""You are the curriculum engine inside Cortex, an adaptive learning platform.

Based on the learner's goal, current mastery scores, and the knowledge graph, generate an ordered learning roadmap.

Learner Goal: {goal}
Mastery Scores: {mastery_scores_json}
Knowledge Graph: {knowledge_graph_json}

The knowledge graph is a map of concepts and their prerequisites, structured as:
{{ "concept": {{ "prerequisites": [string], "unlocks": [string] }} }}

Rules:
- Do not recommend concepts the learner has already mastered (mastery ≥ 80).
- Prioritize prerequisite concepts before advanced ones.
- Group concepts into logical phases (e.g., Phase 1: Foundations, Phase 2: Core Skills).
- The roadmap should be goal-directed — only include concepts relevant to the learner's stated goal.
- Mark already-completed concepts clearly.

Return a JSON object:
{{
  "phases": [
    {{
      "phase": 1,
      "title": string,
      "concepts": [
        {{
          "name": string,
          "status": "completed" | "in_progress" | "next" | "upcoming",
          "mastery": number,
          "estimated_sessions": number
        }}
      ]
    }}
  ],
  "immediate_next": string,
  "reasoning": string
}}

reasoning should explain in 1–2 sentences why this roadmap is ordered this way for this specific learner.

Return only valid JSON. No preamble."""

    has_aws_creds = (
        settings.aws_access_key_id is not None
        and settings.aws_secret_access_key is not None
        and settings.aws_default_region is not None
    )

    if not has_aws_creds:
        logger.warning("AWS credentials not configured. Falling back to local mock roadmap generation.")
        return _generate_mock_roadmap(goal, mastery_scores_json, knowledge_graph_json)

    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        model_id = "amazon.nova-micro-v1:0"

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

        raw_text = response['output']['message']['content'][0]['text'].strip()
        
        # Strip potential markdown formatting
        if raw_text.startswith("```json"):
            raw_text = raw_text.removeprefix("```json").removesuffix("```").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.removeprefix("```").removesuffix("```").strip()

        data = json.loads(raw_text)
        return _validate_and_sanitize_roadmap(data)

    except Exception as e:
        logger.error(f"Failed to generate curriculum roadmap via Bedrock: {e}. Falling back to mock data.")
        return _generate_mock_roadmap(goal, mastery_scores_json, knowledge_graph_json)


def _validate_and_sanitize_roadmap(data: dict) -> dict:
    sanitized = {}
    
    phases = data.get("phases", [])
    sanitized_phases = []
    
    for p in phases:
        if not isinstance(p, dict):
            continue
        
        concepts = p.get("concepts", [])
        sanitized_concepts = []
        for c in concepts:
            if not isinstance(c, dict):
                continue
            
            status = str(c.get("status", "upcoming")).lower().strip()
            if status not in ["completed", "in_progress", "next", "upcoming"]:
                status = "upcoming"
                
            sanitized_concepts.append({
                "name": str(c.get("name", "Concept")),
                "status": status,
                "mastery": int(c.get("mastery", 0)),
                "estimated_sessions": int(c.get("estimated_sessions", 1))
            })
            
        sanitized_phases.append({
            "phase": int(p.get("phase", len(sanitized_phases) + 1)),
            "title": str(p.get("title", "Logical Phase")),
            "concepts": sanitized_concepts
        })
        
    sanitized["phases"] = sanitized_phases
    sanitized["immediate_next"] = str(data.get("immediate_next", ""))
    sanitized["reasoning"] = str(data.get("reasoning", "Roadmap structured based on prerequisites hierarchy."))
    
    return sanitized


def _generate_mock_roadmap(
    goal: str,
    mastery_scores_json: str,
    knowledge_graph_json: str
) -> dict:
    try:
        mastery = json.loads(mastery_scores_json)
    except Exception:
        mastery = {}
        
    try:
        kg = json.loads(knowledge_graph_json)
    except Exception:
        kg = {}

    all_concepts = list(kg.keys())
    
    def get_prereq_depth(concept_name, visited=None):
        if visited is None:
            visited = set()
        if concept_name in visited:
            return 0
        visited.add(concept_name)
        prereqs = kg.get(concept_name, {}).get("prerequisites", [])
        if not prereqs:
            return 0
        return 1 + max(get_prereq_depth(p, visited) for p in prereqs)

    all_concepts.sort(key=get_prereq_depth)
    
    completed_concepts = []
    remaining_concepts = []
    
    for c in all_concepts:
        score = round(mastery.get(c, 0.0) * 100)
        if score >= 80:
            completed_concepts.append({
                "name": c,
                "status": "completed",
                "mastery": score,
                "estimated_sessions": 0
            })
        else:
            remaining_concepts.append((c, score))
            
    phases = []
    immediate_next = ""
    
    p1_concepts = list(completed_concepts)
    p2_concepts = []
    
    for idx, (c, score) in enumerate(remaining_concepts):
        if idx == 0:
            status = "next"
            immediate_next = c
        elif score > 0:
            status = "in_progress"
        else:
            status = "upcoming"
            
        concept_entry = {
            "name": c,
            "status": status,
            "mastery": score,
            "estimated_sessions": 2 if status in ["next", "in_progress"] else 3
        }
        
        if idx < len(remaining_concepts) // 2 + 1:
            p1_concepts.append(concept_entry)
        else:
            p2_concepts.append(concept_entry)
            
    if p1_concepts:
        phases.append({
            "phase": 1,
            "title": "Foundations & Core Skills",
            "concepts": p1_concepts
        })
    if p2_concepts:
        phases.append({
            "phase": 2,
            "title": "Advanced Implementations",
            "concepts": p2_concepts
        })
        
    reasoning = f"This roadmap is designed to guide you toward '{goal}'. It builds foundations before introducing advanced concepts."
    
    return {
        "phases": phases,
        "immediate_next": immediate_next,
        "reasoning": reasoning
    }


def generate_socratic_response(
    learner_profile_json: str,
    concept: str,
    conversation_history: list[dict],
    attempt_count: int
) -> str:
    """
    Executes Prompt 5 as a Socratic Tutor.
    """
    history_str = ""
    for msg in conversation_history:
        role = msg.get("role", "learner")
        content = msg.get("content", "")
        history_str += f"{role}: {content}\n"

    prompt = f"""You are Cortex, an AI Socratic Tutor.

Your job is to help the learner arrive at understanding through their own reasoning — not to give them answers.

Learner Profile: {learner_profile_json}
Current Concept: {concept}
Conversation History:
{history_str}
Attempt Count on this question: {attempt_count}

Rules:
1. Never directly answer a question the learner can reason through.
2. Begin with a question that activates what the learner already knows.
3. If the learner says "I don't know", offer a concrete analogy or a smaller sub-question — not the answer.
4. Provide hints progressively. Each hint should be more specific than the last.
5. Track attempt_count. Hint quality should increase with each attempt.
6. Only reveal a direct explanation after 3+ failed attempts — and even then, explain the reasoning process, not just the answer.
7. Be warm, patient, and never condescending.
8. Adapt language complexity to the learner's level from their profile.

Hint escalation guide:
- Attempt 1: Ask a reframing question ("What do you already know about X?")
- Attempt 2: Offer a real-world analogy
- Attempt 3: Provide a partial answer and ask the learner to complete it
- Attempt 4+: Explain directly, then ask the learner to explain it back to you

Respond only with your next tutor message. Do not include meta-commentary, labels, or JSON."""

    has_aws_creds = (
        settings.aws_access_key_id is not None
        and settings.aws_secret_access_key is not None
        and settings.aws_default_region is not None
    )

    if not has_aws_creds:
        logger.warning("AWS credentials not configured. Falling back to local mock Socratic response.")
        user_message = ""
        for m in reversed(conversation_history):
            if m.get("role") == "learner":
                user_message = m.get("content", "")
                break
        return _generate_mock_socratic_response(concept, attempt_count, user_message)

    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        model_id = "amazon.nova-micro-v1:0"

        response = client.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.5
            }
        )

        return response['output']['message']['content'][0]['text'].strip()

    except Exception as e:
        logger.error(f"Failed to generate Socratic response via Bedrock: {e}. Falling back to mock data.")
        user_message = ""
        for m in reversed(conversation_history):
            if m.get("role") == "learner":
                user_message = m.get("content", "")
                break
        return _generate_mock_socratic_response(concept, attempt_count, user_message)


def _generate_mock_socratic_response(concept: str, attempt_count: int, user_message: str) -> str:
    concept_lower = concept.lower()
    
    # Check if the user says "I don't know"
    is_clueless = False
    clean_msg = user_message.strip().lower().replace("'", "").replace("’", "")
    if clean_msg in ["i dont know", "dont know", "no idea", "unsure", "not sure", "i am not sure", "i have no idea", "help"]:
        is_clueless = True

    # Dictionary of specific content for core Python concepts
    concept_fallbacks = {
        "variables": {
            "reframing": "What do you already know about how Python stores values in memory using variables?",
            "analogy": "Think of a variable like a labeled box where you can store a toy. If you write `box = 'toy'`, you put the toy inside. How would you store a number like 5 in a box named x?",
            "partial": "Here is a start: `x = ...` where we want to assign the number 10. Can you complete the statement?",
            "explanation": "In Python, we assign a value to a variable using the `=` symbol, like `x = 10`. This stores the value 10 in the memory location labeled x. Now, could you explain this back to me in your own words?"
        },
        "data types": {
            "reframing": "What do you already know about data types like strings, integers, and booleans in Python?",
            "analogy": "Think of data types like sorting recycling items (paper, plastic, glass). Python sorts data into text, whole numbers, or decimals. What type would a whole number like 10 be?",
            "partial": "Text is represented as a string (`str`), like `'hello'`. A whole number is an integer (`int`). If we have a true/false value, what built-in type starts with `b`?",
            "explanation": "Python classifies data into types: integers (`int`) for whole numbers, floats (`float`) for decimals, strings (`str`) for text, and booleans (`bool`) for True/False. Can you explain in your own words how Python distinguishes between 5 and '5'?"
        },
        "operators": {
            "reframing": "What do you already know about operators like arithmetic, comparison, and logical operators in Python?",
            "analogy": "Think of operators like buttons on a calculator that perform calculations or check conditions. What operator would you use to check if two values are equal?",
            "partial": "To add values, we use `+`. To check if two values are equal, we use a double equals sign. Can you write down that double equals sign operator?",
            "explanation": "Operators are symbols that perform operations. For example, `+` is arithmetic, and `==` is a comparison operator that returns True or False. Can you explain the difference between `=` and `==` in your own words?"
        },
        "conditionals": {
            "reframing": "What do you already know about conditionals like `if`, `elif`, and `else` statements in Python?",
            "analogy": "Think of conditionals like a fork in the road. If it is raining, you take the left path; otherwise, you take the right path. What keyword is used for the default path?",
            "partial": "We write `if condition:` to start. If we want a default block that runs when all conditions are false, we use the `else` keyword. Can you write the basic structure of an `if` and `else` block?",
            "explanation": "Conditionals execute different blocks of code depending on whether conditions are true or false using `if`, `elif`, and `else`. Now, can you explain how Python decides which branch of a conditional to run?"
        },
        "loops": {
            "reframing": "What do you already know about repeating actions using loops in Python?",
            "analogy": "Imagine running laps around a track. You repeat the action of running until you've completed a set number of laps. What loop would you use if you know the exact number of laps?",
            "partial": "A `for` loop is great for repeating a set number of times. We write `for i in range(3):` to print 'Hi' 3 times. Can you write a loop that prints 'Hi' 5 times using this structure?",
            "explanation": "Loops repeat code blocks. A `for` loop iterates over a sequence (like a range), whereas a `while` loop runs as long as a condition is true. Could you explain the main difference between a `for` loop and a `while` loop?"
        },
        "functions": {
            "reframing": "What do you already know about functions and scope in Python?",
            "analogy": "Think of a function like a recipe card: it lists ingredients (parameters) and instructions, and gives you a dish (return value) whenever you call it. What keyword starts a recipe definition?",
            "partial": "We define a function using the `def` keyword, followed by parameters in parentheses. To send a value back to the caller, we use the `return` keyword. Can you write a function named `greet` that returns 'Hello'?",
            "explanation": "Functions are reusable code blocks defined with `def` that can take inputs (parameters) and output a result using `return`. Can you explain the benefit of using functions instead of copying code?"
        },
        "lists": {
            "reframing": "What do you already know about storing collections of items using lists in Python?",
            "analogy": "Think of a list like a labeled grocery list or a row of numbered lockers starting at locker index 0. How would you access the item in the first locker?",
            "partial": "Lists are enclosed in square brackets, like `fruits = ['apple', 'banana']`. To get the first item, we use `fruits[0]`. How would you get the second item?",
            "explanation": "Lists are ordered collections of items written with square brackets. You access elements using their 0-based index (e.g., `list[0]`). Can you explain how you would add a new item to a list?"
        },
        "dictionaries": {
            "reframing": "What do you already know about key-value data structures like dictionaries in Python?",
            "analogy": "Think of a dictionary like a real-world dictionary: you look up a word (the key) to find its definition (the value). How do we write a dictionary in Python?",
            "partial": "Dictionaries use curly braces, like `user = {'name': 'Ada'}`. To look up the name, we write `user['name']`. How would you write a key-value pair for 'age' set to 21?",
            "explanation": "Dictionaries store key-value pairs using curly braces. You retrieve a value by referencing its key in brackets, like `dict['key']`. Can you explain the difference between a list and a dictionary in your own words?"
        },
        "oop": {
            "reframing": "What do you already know about object-oriented programming (OOP) principles like classes and objects in Python?",
            "analogy": "Think of a class like a blueprint for a car, and an object as the physical car built using that blueprint. How would you declare a class?",
            "partial": "We define a class with `class Car:`. To initialize properties when a new car is built, we define a special method `def __init__(self, color):`. What parameter represents the object itself?",
            "explanation": "OOP bundles data (attributes) and actions (methods) into classes, which act as blueprints to create object instances. Now, can you explain the difference between a class and an instance of that class?"
        },
        "object-oriented programming": {
            "reframing": "What do you already know about object-oriented programming (OOP) principles like classes and objects in Python?",
            "analogy": "Think of a class like a blueprint for a car, and an object as the physical car built using that blueprint. How would you declare a class?",
            "partial": "We define a class with `class Car:`. To initialize properties when a new car is built, we define a special method `def __init__(self, color):`. What parameter represents the object itself?",
            "explanation": "OOP bundles data (attributes) and actions (methods) into classes, which act as blueprints to create object instances. Now, can you explain the difference between a class and an instance of that class?"
        },
        "file handling": {
            "reframing": "What do you already know about reading from and writing to files in Python?",
            "analogy": "Think of file handling like opening a filing cabinet drawer, reading or writing a sheet of paper, and then closing the drawer. What keyword ensures the drawer is safely closed?",
            "partial": "We open files with a context manager using `with open('file.txt', 'r') as f:`. What mode string do we pass if we want to write to the file instead of reading?",
            "explanation": "File handling uses `open()` inside a `with` statement (a context manager) to guarantee the file is properly closed. Mode 'r' is for reading and 'w' is for writing. Can you explain why it's important to use a context manager when opening files?"
        },
        "exception handling": {
            "reframing": "What do you already know about catching runtime errors using exception handling in Python?",
            "analogy": "Think of exception handling like a safety net. If a performer slips (an error occurs), the safety net catches them so they don't crash the show. What blocks are used to build this safety net?",
            "partial": "We wrap risky code in a `try` block. If an error occurs, the code in the `except` block runs to handle it. Can you write a basic `try` and `except` block template?",
            "explanation": "Exception handling uses `try` and `except` blocks. If an exception occurs in the `try` block, execution immediately jumps to the `except` block instead of terminating the script. Now, can you explain in your own words when you would use exception handling?"
        },
        "modules and packages": {
            "reframing": "What do you already know about organizing code using modules and packages in Python?",
            "analogy": "Think of modules like individual toolboxes in a workshop. You import a toolbox so you can use the specialized tools inside it. What keyword is used to import a toolbox?",
            "partial": "We import external modules using the `import` keyword, like `import math`. If we want to import only the `sqrt` function from `math`, we write `from math import ...`. What goes in the blank?",
            "explanation": "Modules are Python files containing code that can be reused in other scripts. We use the `import` keyword to bring them into our file. Can you explain why we use modules to organize code?"
        }
    }

    # Match best concept fallback or default
    matched_key = None
    for k in concept_fallbacks:
        if k in concept_lower:
            matched_key = k
            break
            
    if matched_key:
        content = concept_fallbacks[matched_key]
    else:
        content = {
            "reframing": f"What do you already know about {concept}?",
            "analogy": f"Let's think of {concept} like a puzzle. We have different pieces that need to connect to form the whole picture. How do you think we can start connecting these pieces?",
            "partial": f"Let's work through {concept} step-by-step. If we start with its basic definition, what is the first detail we need? Can you complete that part?",
            "explanation": f"To explain {concept}: it is a key concept that helps organize and control logic. Now, in your own words, could you explain how you would describe {concept} to a peer?"
        }

    # Apply Socratic rules
    # Rule 3: If the learner says "I don't know", offer a concrete analogy or a smaller sub-question — not the answer.
    if is_clueless:
        return f"No worries at all! Let's approach this differently. {content['analogy']}"

    # Progressive Hint Escalation
    if attempt_count == 1:
        return content["reframing"]
    elif attempt_count == 2:
        return content["analogy"]
    elif attempt_count == 3:
        return content["partial"]
    else:
        return content["explanation"]

