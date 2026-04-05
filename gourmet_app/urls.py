# pyright: reportMissingImports=false, reportMissingModuleSource=false
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Login & Logout
    path('', auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Company URLs
    path('companies/', views.company_list, name='company_list'),
    path('company/<int:pk>/', views.company_detail, name='company_detail'),
    path('company/<int:pk>/payment_pdf/', views.company_payment_pdf, name='company_payment_pdf'),

    # Product & Party
    path('products/', views.product_list, name='product_list'),
    path('parties/', views.party_list, name='party_list'),

    # Transactions
    path('purchase/add/', views.add_purchase, name='add_purchase'),
    path('sale/add/', views.add_sale, name='add_sale'),
    path('expense/add/', views.add_expense, name='add_expense'),

    # Quick Sale
    path('quick-sale/', views.quick_sale, name='quick_sale'),
    path("sales-report/", views.sales_report, name="sales_report"),
    path('sales_report/', views.sales_report),  # optional alias
    path("sale-report-pdf/", views.sales_report_pdf, name="sales_report_pdf"),
    path("report/", views.sales_report, name="sales_report"),
    path('company-summary/', views.company_purchase_summary, name='company_purchase_summary'),
    path('party/<int:party_id>/ledger/', views.party_ledger, name='party_ledger'),
    path("stock/", views.stock_dashboard, name="stock_dashboard"),
    path("grand_summary/", views.grand_summary, name="grand_summary"),
]

 
