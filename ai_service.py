import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def predict_health(full_name: str, date_of_birth: str, glucose: float, haemoglobin: float, cholesterol: float) -> str:
    prompt = f"""You are a medical AI assistant. Analyze the following patient blood test results and provide a brief health assessment.

Patient: {full_name}
Date of Birth: {date_of_birth}
Blood Test Results:
- Glucose: {glucose} mg/dL (Normal: 70-99 fasting)
- Haemoglobin: {haemoglobin} g/dL (Normal: Men 13.5-17.5, Women 12-15.5)
- Cholesterol: {cholesterol} mg/dL (Desirable: <200, Borderline: 200-239, High: ≥240)

Provide a concise health assessment (2-3 sentences) covering:
1. Whether each value is normal, low, or high
2. Potential health risks or conditions indicated
3. A brief recommendation

Keep the response professional, factual, and under 100 words. Do not diagnose — use language like "may indicate" or "suggests possible". End with "Please consult a healthcare professional for proper diagnosis."
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
