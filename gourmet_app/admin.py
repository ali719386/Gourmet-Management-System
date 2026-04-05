# pyright: reportMissingImports=false, reportMissingModuleSource=false
from django.contrib import admin
from .models import Company, Product, Party, Stock, Purchase, Sale, CompanyPayment, PartyPayment, Expense
admin.site.register([Company, Product, Party, Stock, Purchase, Sale, CompanyPayment, PartyPayment, Expense,])

class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'rate')   # 👈 Rate field visible hoga
