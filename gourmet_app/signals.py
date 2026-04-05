# gourmet_app/signals.py
# pyright: reportMissingImports=false, reportMissingModuleSource=false
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Party, Client, Transaction

# Sync Party to Client
@receiver(post_save, sender=Party)
def create_or_update_client(sender, instance, created, **kwargs):
    Client.objects.update_or_create(
        name=instance.name,
        defaults={
            'address': getattr(instance, 'address', ''),
            'phone': getattr(instance, 'phone', ''),
        }
    )

# Optional: sync Party Transaction to Client Transaction
@receiver(post_save, sender=Transaction)
def sync_transaction_to_client(sender, instance, created, **kwargs):
    if created and hasattr(instance, 'party'):
        client = Client.objects.filter(name=instance.party.name).first()
        if client:
            # Create a corresponding Client transaction
            from .models import Transaction as ClientTransaction
            ClientTransaction.objects.create(
                client=client,
                amount=instance.amount,
                transaction_type=instance.transaction_type,
                date=instance.date,
            )
