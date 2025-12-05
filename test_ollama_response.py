#!/usr/bin/env python3
"""
Test script to check the Ollama response structure
"""

import ollama

def test_ollama_response():
    print("Testing Ollama response structure...")
    
    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "user", "content": "What is Python?"}
            ]
        )
        
        print(f"Full response: {response}")
        print(f"Response type: {type(response)}")
        
        if isinstance(response, dict):
            print(f"Keys in response: {response.keys()}")
            message = response.get("message", {})
            if isinstance(message, dict):
                print(f"Message keys: {message.keys()}")
                content = message.get("content", "")
                print(f"Content: '{content}'")
                print(f"Content type: {type(content)}")
            else:
                print(f"Message is not a dict: {message}")
        else:
            print(f"Response is not a dict: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ollama_response()