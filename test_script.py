import time
import base64
import io
import requests
from PIL import Image

# Apni Groq API key yahan enter karein
API_KEY = ""
URL = "https://api.groq.com/openai/v1/chat/completions"

def send_test_request(index):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test ke liye ek choti dummy image generate kar rahe hain
    img = Image.new("RGB", (200, 200), color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=70)
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this MCQ test image. Provide ultra-concise breakdown: 1. Flaw, 2. Rule, 3. Hint."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 150,
        "temperature": 0.1
    }
    
    try:
        print(f"Request {index} bhej rahe hain...")
        response = requests.post(URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"[SUCCESS] Request {index} Successful! HTTP 200")
        else:
            print(f"[ERROR] Request {index} Failed: HTTP {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] Request {index} mein error aaya: {e}")

if __name__ == "__main__":
    print("Test loop shuru ho gaya hai (60 requests, har 1 minute ke gap se)...")
    for i in range(1, 61):
        send_test_request(i)
        if i < 60:
            print("Agli request ke liye 60 seconds ka wait kar rahe hain...\n")
            time.sleep(60)
            
    print("Test mukammal ho gaya!")