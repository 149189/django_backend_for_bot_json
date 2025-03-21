# prediction/models.py

from django.db import models

class UserTransaction(models.Model):
    # The id field is automatically created as a primary key if not specified,
    # but you can define it explicitly if desired.
    id = models.AutoField(primary_key=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    date = models.DateField()
    narration = models.TextField(blank=True, null=True)
    # For 'type', you might want to use choices if you have a fixed set of transaction types.
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.category} - {self.amount}"
