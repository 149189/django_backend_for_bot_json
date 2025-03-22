import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Define the path to the JSON file relative to this views.py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVESTMENT_PLANS_FILE = os.path.join(BASE_DIR, 'data', 'plan.json')

def load_investment_plans():
    """Load investment plans from the JSON file."""
    with open(INVESTMENT_PLANS_FILE, 'r') as f:
        data = json.load(f)
    return data.get("investment_plans", [])

def parse_salary_range(salary_range_str):
    """
    Convert a salary range string into a numeric tuple (low, high).
    Supported formats:
      - "Below 30k": returns (0, 30000)
      - "Above 300k": returns (300000, inf)
      - "30k-50k": returns (30000, 50000)
    """
    salary_range_str = salary_range_str.strip()
    if salary_range_str.lower().startswith("below"):
        # Example: "Below 30k" means salary < 30000
        num_str = salary_range_str.split()[1]
        threshold = int(num_str.replace("k", "")) * 1000
        return (0, threshold)
    elif salary_range_str.lower().startswith("above"):
        # Example: "Above 300k" means salary >= 300000
        num_str = salary_range_str.split()[1]
        threshold = int(num_str.replace("k", "")) * 1000
        return (threshold, float('inf'))
    else:
        # Format "30k-50k"
        parts = salary_range_str.split("-")
        if len(parts) == 2:
            low = int(parts[0].replace("k", "")) * 1000
            high = int(parts[1].replace("k", "")) * 1000
            return (low, high)
    # Fallback if format is not recognized
    return (0, 0)

@csrf_exempt
@require_http_methods(["POST"])
def recommend_investment_plan(request):
    """
    Accepts a POST request with JSON body { "salary": <number> } and returns a recommended investment plan.
    """
    try:
        data = json.loads(request.body)
        salary = data.get("salary")
        if salary is None:
            return JsonResponse({"error": "Salary not provided"}, status=400)
        
        try:
            salary = float(salary)
        except ValueError:
            return JsonResponse({"error": "Invalid salary value"}, status=400)
        
        plans = load_investment_plans()
        
        recommended_plan = None
        for plan in plans:
            salary_range_str = plan.get("salary_range", "")
            low, high = parse_salary_range(salary_range_str)
            if low <= salary < high:
                recommended_plan = plan
                break
        
        if recommended_plan:
            return JsonResponse({"recommended_plan": recommended_plan})
        else:
            return JsonResponse({"error": "No suitable plan found for the given salary"}, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON input"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
