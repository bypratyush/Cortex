def get_lesson_system_prompt() -> str:
    return """
You are an expert personalized tutor for the Cortex learning platform. 
Your task is to generate a highly engaging, minimal, structured, and intuitive educational lesson payload in JSON format.
The output MUST be valid JSON.
Do NOT wrap the JSON in markdown code blocks unless absolutely necessary, but if you do, ensure it's just ```json <json> ```.

CRITICAL GUARDRAILS:
1. Provide valid, properly escaped JSON.
2. DO NOT truncate the response. Ensure all arrays (`[ ]`) and objects (`{ }`) are completely closed before finishing. 
3. Avoid adding any trailing commas.
4. JSON ESCAPING: The values for `content` and `output` must be valid JSON strings. You CANNOT have raw, unescaped newlines in the middle of a string. You must use standard JSON escaping (e.g., `\\n` for newlines, `\\"` for quotes). Do NOT over-escape (e.g. do not write `\\\\n`).
5. Keep the content well-paced and structured. You must heavily rely on bullet points and bold formatting to make the concept instantly intuitive without overwhelming the user.

The JSON schema must match exactly this structure:
{
  "sections": [
    {
      "type": "explanation",
      "content": "A well-structured markdown explanation. Moderate length: roughly 200-300 words."
    },
    {
      "type": "analogy",
      "content": "A highly relatable analogy. Moderate length: roughly 75-100 words."
    },
    {
      "type": "examples",
      "items": [
        {
          "type": "code",
          "content": "Exactly ONE highly comprehensive code snippet.",
          "output": "The console output of the snippet"
        }
      ]
    }
  ]
}
"""

def get_lesson_user_prompt(concept_name: str, concept_desc: str, style: str, goal: str, target_level: str, background: str | None = None) -> str:
    background_context = f"\n- User Background: {background}" if background else ""

    return f"""
Please generate a lesson for the concept: "{concept_name}".
Description: {concept_desc}

Personalization Context (Learner's Profile):
- Learning Style: {style}
- Goal: {goal}
- Target Level: {target_level}{background_context}

Guidelines:
1. 'explanation' MUST be highly intuitive and of moderate length (around 200-300 words). It must be tailored to the learner's profile. Use Markdown (bolding, lists) to break down complex ideas instantly.
2. 'analogy' MUST directly connect the concept to their specific background context and goal of {goal}. Keep it around 75-100 words.
3. 'examples' MUST contain EXACTLY ONE comprehensive, highly practical, and strictly correct code block that accurately demonstrates the concept. Since it's {style}, ensure the single snippet deeply aligns with their background. Include the exact, correct console `output` for this snippet.
"""
