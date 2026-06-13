import json
import boto3
from typing import Any

from app.core.config import settings

def get_bedrock_client():
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        raise ValueError("AWS credentials not fully configured for Bedrock")

    return boto3.client(
        service_name="bedrock-runtime",
        region_name=settings.aws_default_region or "us-east-1",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

class LLMService:
    @staticmethod
    def generate_json(system_prompt: str, user_prompt: str, model_id: str = "amazon.nova-pro-v1:0", max_retries: int = 3) -> dict[str, Any]:
        """
        Calls AWS Bedrock and expects a JSON response, with robust retry logic.
        """
        import re
        client = get_bedrock_client()
        
        # Bedrock Converse API format
        messages = [
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ]
        
        system = [{"text": system_prompt}]
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = client.converse(
                    modelId=model_id,
                    messages=messages,
                    system=system,
                    inferenceConfig={
                        "temperature": 0.3 + (attempt * 0.1), # slightly increase temp on retries
                        "maxTokens": 4000,
                    }
                )
                
                output_text = response["output"]["message"]["content"][0]["text"]
                
                # Attempt to extract JSON if it's wrapped in a code block
                match = re.search(r'```json\s*([\s\S]*?)\s*```', output_text)
                if match:
                    json_str = match.group(1)
                else:
                    json_str = output_text.strip()
                    if json_str.startswith("```"):
                        json_str = json_str[3:]
                    if json_str.endswith("```"):
                        json_str = json_str[:-3]
                    json_str = json_str.strip()
                    
                return json.loads(json_str)
                
            except json.JSONDecodeError as e:
                print(f"JSON Parse Attempt {attempt + 1} failed. Retrying...")
                last_exception = e
                # Tell the model it failed
                messages.append({"role": "assistant", "content": [{"text": output_text}]})
                messages.append({"role": "user", "content": [{"text": "Your previous response was invalid JSON. Ensure all braces are closed and it is strictly valid JSON."}]})
                
        print("Failed to decode JSON from LLM after retries.")
        raise last_exception
            
    @staticmethod
    def generate_text(system_prompt: str, messages: list[dict], model_id: str = "amazon.nova-lite-v1:0") -> str:
        """
        Calls AWS Bedrock for text generation (e.g. Chat).
        Messages should be in Bedrock converse format: [{"role": "user"|"assistant", "content": [{"text": "..."}]}]
        """
        client = get_bedrock_client()
        
        system = [{"text": system_prompt}]
        
        response = client.converse(
            modelId=model_id,
            messages=messages,
            system=system,
            inferenceConfig={
                "temperature": 0.7,
                "maxTokens": 1000,
            }
        )
        
        return response["output"]["message"]["content"][0]["text"]
