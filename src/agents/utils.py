import os
from langchain_core.runnables import RunnableLambda
from ..Utils_initializingLLM import (
    gpt_completion_xty,
    openai_style_completion,
    deepseek_local_completion,
    llama_completion,
    gemini_completion,
    claude_completion,
    mistral_completion,
    qwen_completion
)

# Configuration Keys (As provided by USER)
KEYS = {
    "deepseek": "sk-941d68a6421e4c3cb2bb17f4e53d258a",
    "gpt": "sk-ZygjjY0B4v0O2NbcB12f266dC07d47748130C30f2d82F566",
    "mistral": "VHvSVlvkWXs3m12PA51mLyZFD1QwTGjk",
}

def call_llm(prompt: str, model_family: str, model_name: str, api_key: str, **kwargs):
    """
    Unified function that uses the CORRECT API format for each model family.
    Wrapper to call specific implementation functions.
    """
    if model_family == "openai" or model_family == "gpt":
        return gpt_completion_xty(prompt=prompt, model=model_name, api_key=api_key, **kwargs)
    
    elif model_family == "deepseek":
        return openai_style_completion(
            prompt=prompt,
            model=model_name, 
            base_url="https://api.deepseek.com/v1",
            api_key=api_key,
            **kwargs
        )
    
    elif model_family == "deepseek_local":
        return deepseek_local_completion(prompt=prompt, model_name=model_name, **kwargs)
    
    elif model_family == "llama" or model_family == "llama_openrouter":
         return llama_completion(prompt=prompt, model=model_name, api_key=api_key, **kwargs)
    
    elif model_family == "gemini":
         return gemini_completion(prompt=prompt, model_name=model_name, api_key=api_key, **kwargs)
         
    elif model_family == "claude":
         return claude_completion(prompt=prompt, model=model_name, api_key=api_key, **kwargs)
    
    elif model_family == "mistral":
         return mistral_completion(prompt=prompt, model=model_name, api_key=api_key, **kwargs)
         
    elif model_family == "qwen" or model_family == "qwen_openrouter":
         return qwen_completion(prompt=prompt, model=model_name, api_key=api_key, **kwargs)
    
    else:
        # Fallback
        return f"Error: Unknown model family {model_family}"

class UnifiedLLM:
    """
    LangChain-compatible wrapper for our custom unified call_llm.
    """
    def __init__(self, model_family="deepseek", model_name="deepseek-chat", api_key=None, temperature=0):
        self.model_family = model_family
        self.model_name = model_name
        self.api_key = api_key or KEYS.get("deepseek") # Default to DeepSeek key
        self.temperature = temperature

    def invoke(self, input_val):
        prompt = str(input_val)
        response = call_llm(
            prompt=prompt,
            model_family=self.model_family,
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature
        )
        return response

def get_llm(model_family: str = "deepseek", model_name="deepseek-chat", temperature: float = 0):
    """
    Methods to get the Council Member LLM.
    For this user request, we FORCE DeepSeek usage for testing.
    """
    # Force DeepSeek for now as requested
    actual_family = "deepseek"
    actual_model = "deepseek-chat"
    actual_key = KEYS["deepseek"]
    
    # Create a runnable lambda that wraps the UnifiedLLM class logic
    # But simpler: just return the RunnableLambda of the function call
    
    def _run(input_val):
        # Unwrap PromptValue to string
        if hasattr(input_val, "to_string"):
            text = input_val.to_string()
        else:
            text = str(input_val)
            
        return call_llm(
            prompt=text,
            model_family=actual_family,
            model_name=actual_model,
            api_key=actual_key,
            temperature=temperature
        )

    return RunnableLambda(_run)
