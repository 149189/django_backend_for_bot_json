# backend/views.py

import os
import re
import json
import requests
import pdfplumber
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv

# Import the generative AI client
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API from your .env file
GEMINI_API_KEY = os.getenv("GEMINI_API")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Define your upload folder (configured in settings)
UPLOAD_FOLDER = settings.UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename(filename):
    # A basic secure_filename replacement.
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()

def categorize_transaction(narration):
    narration_lower = narration.lower()
    categories = {
        "Food": ["restaurant", "cafe", "food", "swiggy", "zomato", "hotel", "dining"],
        "Travel": ["train", "flight", "bus", "uber", "ola", "metro", "taxi", "tours", "trip"],
        "Investment": ["mutual fund", "sip", "groww", "zerodha", "navi", "investment", "stock"],
        "Utilities": ["electricity", "water", "gas", "mobile", "recharge", "rent", "dth", "broadband", "bill"],
        "Entertainment": ["movie", "netflix", "prime video", "steam", "game", "sports", "music", "concert"],
        "Medical": ["hospital", "doctor", "clinic", "medicine", "pharmacy", "health"],
        "Shopping": ["amazon", "flipkart", "myntra", "shopping", "electronics", "fashion", "mall"],
    }
    for category, keywords in categories.items():
        if any(keyword in narration_lower for keyword in keywords):
            return category
    return "Other"

def extract_and_categorize_transactions(pdf_path, password=None):
    transactions = []
    date_pattern = re.compile(r'^\d{2}-\d{2}-\d{4}$')
    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                for line in lines:
                    # Skip header lines (customize as needed)
                    if 'Date' in line and 'Narration' in line and 'Balance' in line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    date_part = parts[0]
                    if not date_pattern.match(date_part):
                        continue
                    date = date_part
                    balance = parts[-1].strip()
                    debit_credit = parts[-2].strip()
                    chq_ref_no = parts[-3].strip() if len(parts) >= 5 else ""
                    narration_parts = parts[1:-3]
                    narration = ' '.join(narration_parts) if narration_parts else "Unknown"
                    category = categorize_transaction(narration)
                    transaction = {
                        "Date": date,
                        "Narration": narration,
                        "Chq/Ref No": chq_ref_no,
                        "Withdrawal(Dr)/ Deposit(Cr)": debit_credit,
                        "Balance": balance,
                        "Category": category
                    }
                    transactions.append(transaction)
    except Exception as e:
        return {"error": str(e)}
    return transactions

def download_pdf_from_url(url, dest_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        return {"error": str(e)}

@csrf_exempt
@require_http_methods(["POST"])
def upload_url(request):
    """
    Endpoint: /upload_url
    Expects JSON:
      {
        "url": "https://example.com/file.pdf",
        "password": ""
      }
    Returns a JSON list of transactions.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    if "url" not in data:
        return JsonResponse({"error": "URL is required"}, status=400)
    
    pdf_url = data["url"]
    password = data.get("password", None)
    
    filename = os.path.basename(pdf_url.split("?")[0])
    if not allowed_file(filename):
        return JsonResponse({"error": "Invalid file format from URL"}, status=400)
    
    filename = secure_filename(filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    download_result = download_pdf_from_url(pdf_url, filepath)
    if isinstance(download_result, dict) and "error" in download_result:
        return JsonResponse(download_result, status=500)
    
    transactions = extract_and_categorize_transactions(filepath, password)
    if isinstance(transactions, dict) and "error" in transactions:
        return JsonResponse(transactions, status=500)
    
    # Optionally, save the JSON to file:
    json_filename = os.path.splitext(filename)[0] + '_categorized.json'
    json_filepath = os.path.join(UPLOAD_FOLDER, json_filename)
    with open(json_filepath, 'w') as json_file:
        json.dump(transactions, json_file, indent=4)
    
    return JsonResponse(transactions, safe=False)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def finance_chat(request):
    """
    Endpoint: /api/finance-chat
    Expects JSON:
      {
        "prompt": "Your question here..."
      }
    Returns a JSON response with the Gemini model's reply.
    """
    # Handle OPTIONS request for CORS preflight
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response
    
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt", "").strip()
        if not user_prompt:
            return JsonResponse({"error": "Empty prompt"}, status=400)
        
        # Generate response using Gemini
        response = model.generate_content(user_prompt)
        result = {
            "user_prompt": user_prompt,
            "bot_response": response.text
        }
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
