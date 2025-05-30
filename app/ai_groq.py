def call_groq_api(prompt):
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": "Bearer YOUR_GROQ_API_KEY"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    res = requests.post(url, json=payload, headers=headers)
    return res.json()['choices'][0]['message']['content']
