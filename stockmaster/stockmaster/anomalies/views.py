# anomalies/views.py

import json
from statistics import mean, stdev
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from prediction.models import UserTransaction  # Adjust this import if your model is in a different app

@require_http_methods(["GET"])
def detect_anomalies(request):
    """
    Detects anomalies in user transactions by category.

    For each category, calculates the average and standard deviation of transaction amounts.
    Any transaction with an amount greater than (average + 2 * std) is flagged as an anomaly.
    """
    categories = [
        "Food",
        "Travel",
        "Investment",
        "Utilities",
        "Entertainment",
        "Medical",
        "Shopping"
    ]
    
    results = []
    
    for cat in categories:
        # Fetch transactions for the current category (using case-insensitive matching)
        transactions = UserTransaction.objects.filter(category__iexact=cat)
        amounts = [float(txn.amount) for txn in transactions]
        
        # Calculate mean and standard deviation if there are at least 2 transactions.
        if len(amounts) >= 2:
            avg_amount = mean(amounts)
            std_amount = stdev(amounts)
            threshold = avg_amount + 2 * std_amount
        else:
            avg_amount = None
            std_amount = None
            threshold = float("inf")  # No transaction will be flagged
        
        anomalies = []
        for txn in transactions:
            txn_amount = float(txn.amount)
            if txn_amount > threshold:
                anomalies.append({
                    "id": txn.id,
                    "amount": txn_amount,
                    "date": txn.date.isoformat() if txn.date else None,
                    "narration": txn.narration,
                    "category": txn.category,
                    "type": txn.type,
                    "balance": float(txn.balance)
                })
        
        results.append({
            "category": cat,
            "average_amount": avg_amount,
            "std_deviation": std_amount,
            "anomaly_threshold": threshold,
            "anomalies": anomalies
        })
    
    return JsonResponse(results, safe=False)
