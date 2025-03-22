import os
import json
import requests
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

# System Prompt to ensure financial and budget-related responses
SYSTEM_PROMPT = """
You are a financial assistant specialized in personal banking and budget management. 
Your role is to:
1. Answer ONLY finance-related questions about budgets, expenses, predictions.
2. Use available prediction data and historical spending data for insights.
3. Provide responses in JSON format like this:
   {"response": "your financial insight"}

If asked about past expenses, use historical data.
For future expenses, use predictive financial insights.
"""

def get_financial_data():
    """Fetch user’s financial prediction and historical spending data."""
    try:
        # Fetch predictions from internal API
        predictions = requests.get("http://127.0.0.1:8000/api/predict-spends/").json()
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

        # Construct prompt with available data
        ai_prompt = f"""
{SYSTEM_PROMPT}

User Query: {user_query}

Available Data:
- Predictions (Next 7 Days): {json.dumps(financial_data['predictions'], indent=2)}
- Historical Spending (Current Month): {json.dumps(financial_data['historical'], indent=2)}

Provide response in this exact format:
{{"response": "Your financial insight"}}
"""

        # Generate response from Gemini API
        gemini_response = model.generate_content(ai_prompt)

        # Extract text response from Gemini API
        model_output = gemini_response.text.strip()

        # Ensure response is JSON
        try:
            parsed_response = json.loads(model_output)
            if "response" not in parsed_response:
                parsed_response = {"response": model_output}
        except json.JSONDecodeError:
            parsed_response = {"response": model_output}

        # Return structured JSON response
        return JsonResponse(parsed_response)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON input"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
