import json
import re
from typing import Dict, Any, Optional
import requests
from openai import OpenAI
from src.config import (
    LLM_PROVIDER,
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODEL_NAME,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    GEMINI_API_KEY,
    GEMINI_MODEL_NAME
)


def extract_json_from_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON object from raw LLM output text, handling markdown code blocks.
    """
    if not response_text:
        return {}
        
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
        
    # Attempt standard JSON load
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Regex search for first '{' to last '}'
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback return raw dict
    return {"raw_output": text}


def call_llm(prompt: str, system_prompt: str = "You are an expert ESG and Greenwashing analyst.", model_name: Optional[str] = None) -> str:
    """
    Call LLM based on configured LLM_PROVIDER with optional per-agent model_name override.
    """
    provider = LLM_PROVIDER.lower()

    # Safety truncation for local LLM context limits (e.g. 2048/4096 tokens in LM Studio)
    if len(prompt) > 3000:
        prompt = prompt[:3000] + "\n...[Nội dung đã được cắt bớt để vừa Context Size của LM Studio]..."

    if provider == "lm_studio":
        try:
            target_model = model_name or LM_STUDIO_MODEL_NAME
            client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2048
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"⚠️ LM Studio Error ({e}). Ensure LM Studio Local Server is running at {LM_STUDIO_BASE_URL}")
            raise e

    elif provider == "openai":
        target_model = model_name or OPENAI_MODEL_NAME
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content or ""

    elif provider == "gemini":
        from google import genai
        target_model = model_name or GEMINI_MODEL_NAME
        client = genai.Client(api_key=GEMINI_API_KEY)
        full_prompt = f"{system_prompt}\n\n{prompt}"
        response = client.models.generate_content(
            model=target_model,
            contents=full_prompt
        )
        return response.text or ""

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def call_llm_json(prompt: str, system_prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """Call LLM and enforce JSON structure output with per-agent model support."""
    json_instructions = "\n\nCRITICAL: Return ONLY a valid JSON object. Do not include markdown headers or extra conversational text."
    full_system_prompt = system_prompt + json_instructions
    raw_response = call_llm(prompt, full_system_prompt, model_name=model_name)
    return extract_json_from_llm_response(raw_response)


if __name__ == "__main__":
    print(f"Testing LLM Client with Provider: {LLM_PROVIDER}")
    print("LM Studio URL:", LM_STUDIO_BASE_URL)
