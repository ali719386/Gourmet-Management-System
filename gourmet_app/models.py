# pyright: reportMissingImports=false, reportMissingModuleSource=false
from django.db import models
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=100, blank=True)
    def __str__(self): return self.name

class Product(models.Model):
    COMPANY_SIZES = [
        ('1L','1 Ltr'),('2L','2 Ltr'),('2.25L','2.25 Ltr'),
        ('1.5L','1.5 Ltr'),('300ml','300 ml'),('500ml','500 ml')
    ]
    name = models.CharField(max_length=200)
    size = models.CharField(max_length=10, choices=COMPANY_SIZES)
    sku = models.CharField(max_length=100, blank=True)
    def __str__(self): return f"{self.name} - {self.size}"

class Party(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    def __str__(self): return self.name

from django.db import models

class Stock(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Rate per unit

    def __str__(self):
        return f"{self.product} : {self.quantity} units @ {self.rate}"

class Purchase(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="purchases", null=True, blank=True) 
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    def __str__(self): return f"Purchase {self.company} {self.product} x{self.qty}"

  

#   yeh b change ho gya hai sale model me


from django.db import models
from django.utils import timezone   # ✅ correct import

class Sale(models.Model):
    party = models.ForeignKey("Party", on_delete=models.CASCADE, related_name="sales")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="sales")
    qty = models.IntegerField(default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date = models.DateField(default=timezone.now)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.party} - {self.product} - {self.amount} on {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically create a transaction when a Sale is made
        Transaction.objects.create(
            party=self.party,
            date=self.date,
            description=f"Sale of {self.product} ({self.qty} units) on {self.date}",
            amount=self.amount,
            transaction_type="credit",  # Party owes money
        )



class CompanyPayment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True)
    def __str__(self): return f"Payment to {self.company} - {self.amount}"

class PartyPayment(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True)
    def __str__(self): return f"Payment from {self.party} - {self.amount}"

class Expense(models.Model):
    EXP_TYPES = [('rent','Rent'),('fuel','Fuel'),('other','Other')]
    title = models.CharField(max_length=200)
    exp_type = models.CharField(max_length=50, choices=EXP_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True)
    def __str__(self): return f"{self.title} - {self.amount}"




from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Sale


def sales_report(request):
    sales = Sale.objects.all()
    return render(request, "sales_report.html", {"sales": sales})


def sales_report_pdf(request):
    sales = Sale.objects.all()
    template_path = "sales_report_pdf.html"
    context = {"sales": sales}
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response




from django.db import models
from django.utils import timezone

# class Party(models.Model):
#     name = models.CharField(max_length=255)
#     phone = models.CharField(max_length=20, blank=True, null=True)
#     address = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ("credit", "Credit"),  # Party owes money
        ("debit", "Debit"),    # Party paid money
    )
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    def __str__(self):
        return f"{self.party} - {self.transaction_type} - {self.amount}"


# class Sale(models.Model):
#     party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="sales")
#     date = models.DateField(default=timezone.now)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     note = models.TextField(blank=True, null=True)

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     # Automatically create a transaction
    #     Transaction.objects.create(
    #         party=self.party,
    #         date=self.date,
    #         description=f"Sale on {self.date}",
    #         amount=self.amount,
    #         transaction_type="credit",  # Sale means party is credited
    #     )





# stock


from django.db import models
class StockTransaction(models.Model):
    TRANSACTION_CHOICES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
    ]

    product_name = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    quantity = models.IntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def total_amount(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        return f"{self.product_name} - {self.transaction_type} - {self.quantity}"








# party data 

# models.py
class Payment(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.party.name} - {self.amount} on {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically log transaction
        Transaction.objects.create(
            party=self.party,
            date=self.date,
            description=f"Payment received from {self.party}",
            amount=self.amount,
            transaction_type="debit",  # Party reduced dues
        )


