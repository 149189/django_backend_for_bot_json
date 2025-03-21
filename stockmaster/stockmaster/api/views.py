import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

SYSTEM_PROMPT = """
You are a financial expert assistant for personal banking and budget management. 
Your responses must:
1. Only answer questions related to user's expenses, budgets, and financial predictions
2. Use the provided prediction data and anomaly detection insights
3. Format responses as concise financial advice with numbers
4. Always respond in JSON format: {"response": "your_answer"}

Available Data:
- Next week's category-wise predictions (7-day forecast)
- Anomaly detection (10-day average spends)
- Historical transaction categorization

If asked about future spending patterns, use the prediction data.
For unusual spending patterns, reference the anomaly detection.
For category-specific queries, use all available data.
"""

def get_financial_data():
    """Fetch prediction and anomaly data from internal APIs"""
    try:
        # Get prediction data
        predictions = requests.get("http://127.0.0.1:8000/api/predict-spends/").json()
        
        # Get anomaly data
        anomalies = requests.get("http://127.0.0.1:8000/api/anamoly-detect/").json()
        
        return {
            "predictions": predictions,
            "anomalies": anomalies
        }
    except requests.RequestException as e:
        return {"error": f"Data fetch failed: {str(e)}"}

@csrf_exempt
@require_http_methods(["POST"])
def financial_insight(request):
    """Handle financial queries with predictive insights"""
    try:
        # Parse request
        data = json.loads(request.body)
        user_query = data.get("prompt", "").strip()
        if not user_query:
            return JsonResponse({"error": "Empty prompt"}, status=400)

        # Get financial data
        financial_data = get_financial_data()
        if "error" in financial_data:
            return JsonResponse(financial_data, status=500)

        # Construct AI prompt
        ai_prompt = f"""
        User Query: {user_query}
        
        Available Data:
        1. Predictions (Next 7 Days):
        {json.dumps(financial_data['predictions'], indent=2)}
        
        2. Anomaly Detection (10-day Averages):
        {json.dumps(financial_data['anomalies'], indent=2)}
        
        Required Response Format:
        {{
          "response": "Your financial insight using relevant data points"
        }}
        """

        # Generate response
        response = model.generate_content(ai_prompt)
        
        # Parse and validate response
        try:
            parsed = json.loads(response.text)
            if "response" not in parsed:
                raise ValueError("Invalid response format")
        except json.JSONDecodeError:
            parsed = {"response": response.text}

        return JsonResponse(parsed)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON input"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)