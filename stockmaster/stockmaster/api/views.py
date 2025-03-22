import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

SYSTEM_PROMPT = """
You are a financial expert assistant for personal banking and budget management. 
Your responses must:
1. Only answer questions related to user's expenses, budgets, and financial predictions.
2. Use the provided prediction data, manual historical spending data, and anomaly detection insights if available.
3. Format responses as concise financial advice with numbers.
4. Always respond in JSON format: {"response": "your_answer"}

Available Data:
- Next week's category-wise predictions (7-day forecast)
- Historical spending data for the current month (manually provided)

If asked about historical spending patterns, use the historical data.
For future spending predictions, reference the prediction data.
"""

def get_financial_data():
    """Fetch prediction data and provide manual historical spending data."""
    try:
        # Get prediction data from internal API
        predictions = requests.get("http://127.0.0.1:8000/api/predict-spends/").json()
        # Manual historical spending data
        historical = {
            "Food": 500.00,
            "Travel": 300.00,
            "Investment": 200.00,
            "Utilities": 150.00,
            "Entertainment": 400.00,
            "Medical": 250.00,
            "Shopping": 350.00
        }
        return {
            "predictions": predictions,
            "historical": historical
        }
    except requests.RequestException as e:
        return {"error": f"Data fetch failed: {str(e)}"}

@csrf_exempt
@require_http_methods(["POST"])
def financial_query(request):
    """Endpoint that sends the financial query response to AdvancedChatbot.jsx."""
    try:
        data = json.loads(request.body)
        user_query = data.get("prompt", "").strip()
        if not user_query:
            return JsonResponse({"error": "Empty prompt"}, status=400)

        financial_data = get_financial_data()
        if "error" in financial_data:
            return JsonResponse(financial_data, status=500)

        # Construct the AI prompt using both prediction and manual historical data
        ai_prompt = f"""
User Query: {user_query}

Available Data:
1. Predictions (Next 7 Days):
{json.dumps(financial_data['predictions'], indent=2)}
2. Historical Spending (Current Month):
{json.dumps(financial_data['historical'], indent=2)}

Required Response Format:
{{
  "response": "Your financial insight using relevant data points"
}}
"""

        # Generate response from the Gemini model
        response = model.generate_content(ai_prompt)
        try:
            parsed = json.loads(response.text)
            if "response" not in parsed:
                raise ValueError("Invalid response format")
        except json.JSONDecodeError:
            parsed = {"response": response.text}

        # Wrap the response in a markdown code block with a JSON language tag
        final_response = f"```json\n{json.dumps(parsed, indent=2)}\n```"
        return JsonResponse({"response": final_response})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON input"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
