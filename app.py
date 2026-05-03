from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def fetch_website_text(url: str):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        lines = [line.strip() for line in text.splitlines()]
        text = " ".join(line for line in lines if line)

        return text[:2000]  # keep small (cost control)

    except Exception as e:
        return f"Error: {str(e)}"


def generate_brochure(content: str, tone: str):
    prompt = f"""
Create a website brochure in a {tone} tone.

IMPORTANT:
- Return ONLY in MARKDOWN (not HTML)
- Do NOT use <h1>, <p>, <ul> etc

Format:
# Title

## Summary
(text)

## Key Highlights
- point 1
- point 2
- point 3

Website content:
{content}
"""
    

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # cheap model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )

    return response.choices[0].message.content


@app.get("/")
def home():
    return {"message": "Server running"}


@app.get("/generate")
def generate(url: str, tone: str = "professional"):
    content = fetch_website_text(url)

    if content.startswith("Error"):
        return {"error": content}

    brochure = generate_brochure(content, tone)

    return {"brochure": brochure}