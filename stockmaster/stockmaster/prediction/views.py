# prediction/views.py

import random
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import UserTransaction

@require_http_methods(["GET"])
def predict_next_week_spends(request):
    """
    Predicts next week's spend for each category by fetching the latest transaction data from the database.
    
    This view now prints the count of transactions per category for debugging purposes.
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
    
    predictions_output = []
    
    for cat in categories:
        # Fetch transactions for the given category from the database.
        transactions = UserTransaction.objects.filter(category=cat)
        
        # Debugging: print the count of transactions fetched for the category.
        print(f"Category: {cat}, Transaction Count: {transactions.count()}")
        
        # Optionally, print a sample transaction record if available.
        sample_txn = transactions.first()
        if sample_txn:
            print(f"Sample Transaction for {cat}: {sample_txn}")
        
        # Compute daily totals for each transaction date.
        daily_totals = {}
        for txn in transactions:
            txn_date = txn.date  # assuming this is a date object
            daily_totals[txn_date] = daily_totals.get(txn_date, 0) + float(txn.amount)
        
        # Calculate the historical daily average spend.
        if daily_totals:
            average_daily = sum(daily_totals.values()) / len(daily_totals)
        else:
            average_daily = 0.0
        
        # Generate a naïve forecast for the next 7 days using random variation.
        next_week_predictions = []
        for _ in range(7):
            variation = random.uniform(0.95, 1.05)  # variation factor between -5% and +5%
            pred = round(average_daily * variation, 2)
            next_week_predictions.append(pred)
        
        total_predicted = round(sum(next_week_predictions), 2)
        
        predictions_output.append({
            "category": cat,
            "next_week_predictions": next_week_predictions,
            "total_predicted_next_week": total_predicted
        })
    
    # Debugging: print overall predictions
    print("Predictions Output:", predictions_output)
    
    return JsonResponse(predictions_output, safe=False)
