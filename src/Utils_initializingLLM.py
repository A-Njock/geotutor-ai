import os
import requests
import json
from openai import OpenAI

# ---------------------------------------------------------
# DEEPSEEK (Standard OpenAI-compatible)
# ---------------------------------------------------------
def openai_style_completion(prompt: str, model: str, base_url: str, api_key: str, **kwargs):
    """
    Generic wrapper for OpenAI-compatible APIs (DeepSeek, etc.)
    """
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Map kwargs to OpenAI params or set defaults
    temperature = kwargs.get('temperature', 0.0)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling {model}: {e}"

# ---------------------------------------------------------
# GPT / OPENROUTER style (using requests or openai client)
# ---------------------------------------------------------
def gpt_completion_xty(prompt: str, model: str, api_key: str, **kwargs):
    # XTY.app uses OpenAI-compatible endpoint
    return openai_style_completion(
        prompt=prompt, 
        model=model, 
        base_url="https://api.xty.app/v1", 
        api_key=api_key, 
        **kwargs
    )

def llama_completion(prompt: str, model: str, api_key: str, **kwargs):
    return openai_style_completion(
        prompt=prompt, 
        model=model, 
        base_url="https://api.xty.app/v1", 
        api_key=api_key, 
        **kwargs
    )

def qwen_completion(prompt: str, model: str, api_key: str, **kwargs):
    return openai_style_completion(
        prompt=prompt, 
        model=model, 
        base_url="https://api.xty.app/v1", 
        api_key=api_key, 
        **kwargs
    )

def claude_completion(prompt: str, model: str, api_key: str, **kwargs):
    # Assuming XTY supports Claude via same endpoint, otherwise implement Anthropic SDK
    return openai_style_completion(
        prompt=prompt, 
        model=model, 
        base_url="https://api.xty.app/v1", 
        api_key=api_key, 
        **kwargs
    )

def gemini_completion(prompt: str, model_name: str, api_key: str, **kwargs):
     return openai_style_completion(
        prompt=prompt, 
        model=model_name, 
        base_url="https://api.xty.app/v1", 
        api_key=api_key, 
        **kwargs
    )

# ---------------------------------------------------------
# MISTRAL
# ---------------------------------------------------------
def mistral_completion(prompt: str, model: str, api_key: str, **kwargs):
    # Mistral SDK or direct API
    # For now, using Requests to https://api.mistral.ai/v1/chat/completions
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": kwargs.get('temperature', 0.0)
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error calling Mistral: {e}"

# ---------------------------------------------------------
# LOCAL DEEPSEEK
# ---------------------------------------------------------
def deepseek_local_completion(prompt: str, model_name: str, **kwargs):
    # Placeholder for Ollama or local setup
    return "DeepSeek Local not configured. Please use remote."
