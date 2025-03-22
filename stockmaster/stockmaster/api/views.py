import os
import json
import requests
import re
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# System Prompt for AI Behavior
SYSTEM_PROMPT = """
You are a financial assistant specialized in personal banking and budget management. 
Your role is to:
1. Answer ONLY finance-related questions about budgets, expenses, and predictions.
2. Use available prediction data and historical spending data for insights.
3. Always provide responses in this JSON format:
   {"response": "your financial insight"}

Use historical data for past expenses and predictive insights for future expenses.
"""

def get_financial_data():
    """Fetch user’s financial prediction and historical spending data."""
    try:
        # Fetch predictions from internal API
        response = requests.get("http://127.0.0.1:8000/api/predict-spends/")
        response.raise_for_status()  # Raise error for bad responses
        predictions = response.json()

        # Example historical spending data (this can come from a database)
        historical = {
            "Food": 500.00,
            "Travel": 300.00,
            "Investment": 200.00,
            "Utilities": 150.00,
            "Entertainment": 400.00,
            "Medical": 250.00,
            "Shopping": 350.00
        }
        return {"predictions": predictions, "historical": historical}
    except requests.RequestException as e:
        return {"error": f"Data fetch failed: {str(e)}"}

def clean_gemini_response(raw_text):
    """
    Cleans Gemini's response, ensuring it returns valid JSON.
    Uses Gemini API itself to correct malformed responses.
    """
    # Remove markdown-style code block formatting
    cleaned_text = re.sub(r"```json\n(.*?)\n```", r"\1", raw_text, flags=re.DOTALL).strip()

    try:
        parsed_response = json.loads(cleaned_text)
        if "response" in parsed_response:
            return {"response": parsed_response["response"]}
        else:
            raise ValueError("Missing 'response' key")
    except (json.JSONDecodeError, ValueError):
        # Ask Gemini to fix the malformed JSON
        correction_prompt = f"""
        The following response is improperly formatted JSON:
        
        {cleaned_text}
        
        Correct it and return only valid JSON in this format:
        {{"response": "your financial insight"}}
        """
        corrected_response = model.generate_content(correction_prompt)
        
        try:
            return json.loads(corrected_response.text.strip())
        except json.JSONDecodeError:
            return {"response": "Error processing AI response"}

@csrf_exempt
@require_http_methods(["POST"])
def financial_query(request):
    """Handles user financial queries and returns Gemini AI response in JSON format."""
    try:
        # Parse user input
        data = json.loads(request.body)
        user_query = data.get("prompt", "").strip()
        if not user_query:
            return JsonResponse({"error": "Empty prompt"}, status=400)

        # Fetch financial data
        financial_data = get_financial_data()
        if "error" in financial_data:
            return JsonResponse(financial_data, status=500)

        # Construct AI prompt
        ai_prompt = f"""
        {SYSTEM_PROMPT}

        User Query: {user_query}

        Available Data:
        - Predictions (Next 7 Days): {json.dumps(financial_data['predictions'], indent=2)}
        - Historical Spending (Current Month): {json.dumps(financial_data['historical'], indent=2)}

        Provide response in this format:
        {{"response": "Your financial insight"}}
        """

        # Generate response from Gemini API
        gemini_response = model.generate_content(ai_prompt)
        cleaned_response = clean_gemini_response(gemini_response.text)

        return JsonResponse(cleaned_response)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON input"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
