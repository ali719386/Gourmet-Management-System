# pyright: reportMissingImports=false, reportMissingModuleSource=false
from django import forms
from .models import Company, Product, Party, Purchase, Sale, CompanyPayment, PartyPayment, Expense

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = '__all__'

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['company','product','qty','rate']

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["party", "product", "qty", "rate", "discount", "amount", "date", "note"]


class CompanyPaymentForm(forms.ModelForm):
    class Meta:
        model = CompanyPayment
        fields = ['company','amount','note']

class PartyPaymentForm(forms.ModelForm):
    class Meta:
        model = PartyPayment
        fields = ['party','amount','note']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title','exp_type','amount','note']







class SalesReportFilterForm(forms.Form):
    party = forms.ModelChoiceField(
        queryset=Party.objects.all(),
        required=False,
        label="Select Party"
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        label="Select Product"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
from django import forms
from .models import Party, Product

class SalesFilterForm(forms.Form):
    party = forms.ModelChoiceField(
        queryset=Party.objects.all(), required=False, label="Party"
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(), required=False, label="Product"
    )
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date"
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="End Date"
    )





from django import forms
from .models import Party, Transaction, Company, Product, Purchase, Sale, CompanyPayment, PartyPayment, Expense

class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = ["name"] 




class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ['date']   # date field form me nahi ayegi




from django import forms
from .models import StockTransaction

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product_name', 'transaction_type', 'quantity', 'price_per_unit']


from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'rate']   # 👈 rate add karna zaroori hai
