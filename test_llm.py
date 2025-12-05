#!/usr/bin/env python3
"""
Test script to verify the LLM functionality
"""

import ollama

def test_llm():
    print("Testing LLM...")
    
    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "user", "content": "What is Python?"}
            ]
        )
        
        content = ""
        if isinstance(response, dict):
            content = response.get("message", {}).get("content", "") or response.get("content", "")
        
        print(f"LLM Response: {content}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm()