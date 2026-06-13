import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))


def predict_health(full_name: str, date_of_birth: str, glucose: float, haemoglobin: float, cholesterol: float) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return _rule_based_assessment(glucose, haemoglobin, cholesterol)

    prompt = (
        f"You are a medical assistant. Analyse these blood test results for patient {full_name} "
        f"(Date of Birth: {date_of_birth}) and provide a concise 2-3 sentence health assessment.\n\n"
        f"Blood Test Results:\n"
        f"- Glucose: {glucose} mg/dL  (Normal fasting: 70-99 mg/dL)\n"
        f"- Haemoglobin: {haemoglobin} g/dL  (Normal: Men 13.5-17.5, Women 12-15.5 g/dL)\n"
        f"- Cholesterol: {cholesterol} mg/dL  (Desirable: <200, Borderline: 200-239, High: ≥240)\n\n"
        f"In your response: state whether each value is normal, low, or high; mention possible health "
        f"risks or conditions these values may indicate; give a brief recommendation. "
        f"Use language like 'may indicate' or 'suggests possible'. Keep it under 100 words. "
        f"End with: 'Please consult a healthcare professional for proper diagnosis.'"
    )

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return _rule_based_assessment(glucose, haemoglobin, cholesterol)


def _rule_based_assessment(glucose: float, haemoglobin: float, cholesterol: float) -> str:
    parts = []

    if glucose < 70:
        parts.append(f"Glucose is low at {glucose} mg/dL, which may suggest hypoglycaemia")
    elif glucose <= 99:
        parts.append(f"Glucose is normal at {glucose} mg/dL")
    elif glucose <= 125:
        parts.append(f"Glucose is elevated at {glucose} mg/dL, suggesting pre-diabetic range")
    else:
        parts.append(f"Glucose is high at {glucose} mg/dL, which may indicate diabetes mellitus")

    if haemoglobin < 12:
        parts.append(f"haemoglobin is low at {haemoglobin} g/dL, possibly indicating anaemia")
    elif haemoglobin <= 17.5:
        parts.append(f"haemoglobin is normal at {haemoglobin} g/dL")
    else:
        parts.append(f"haemoglobin is elevated at {haemoglobin} g/dL, which warrants further evaluation")

    if cholesterol < 200:
        parts.append(f"cholesterol is desirable at {cholesterol} mg/dL")
    elif cholesterol < 240:
        parts.append(f"cholesterol is borderline high at {cholesterol} mg/dL, suggesting dietary review")
    else:
        parts.append(f"cholesterol is high at {cholesterol} mg/dL, indicating increased cardiovascular risk")

    sentence = "; ".join(parts).capitalize() + ". "
    sentence += "Please consult a healthcare professional for proper diagnosis."
    return sentence
