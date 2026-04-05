# pyright: reportMissingImports=false, reportMissingModuleSource=false
from decimal import Decimal

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import (
    CompanyForm, ProductForm, PartyForm, PurchaseForm, SaleForm,
    CompanyPaymentForm, PartyPaymentForm, ExpenseForm,
)
from .models import (
    Company, Product, Party, Stock, Purchase, Sale,
    CompanyPayment, PartyPayment, Expense,
    StockTransaction, Payment, Transaction,
)



def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")  # successful login -> dashboard
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "accounts/login.html")


@login_required


def dashboard(request):
    # Total purchases (all purchases)
    total_purchases = Purchase.objects.aggregate(
        total=Sum(ExpressionWrapper(F('qty') * F('rate'), output_field=DecimalField()))
    )['total'] or 0

    # Total sales (all sales)
    total_sales = Sale.objects.aggregate(
        total=Sum(ExpressionWrapper(F('qty') * F('rate'), output_field=DecimalField()))
    )['total'] or 0

    # Total expenses
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

    # Profit calculation: sold items only (FIFO method)
    profit = 0
    for sale in Sale.objects.all():
        purchase_items = Purchase.objects.filter(product=sale.product).order_by('id')  # FIFO
        remaining_qty = sale.qty
        for p in purchase_items:
            if remaining_qty == 0:
                break
            qty_taken = min(p.qty, remaining_qty)
            profit += qty_taken * (sale.rate - p.rate)
            remaining_qty -= qty_taken

    # Stocks with last purchase rate
    stocks = []
    for stock in Stock.objects.select_related('product').all():
        last_purchase = Purchase.objects.filter(product=stock.product).order_by('-date').first()
        last_rate = last_purchase.rate if last_purchase else None

        stocks.append({
            'product': str(stock.product),
            'quantity': stock.quantity,
            'last_rate': last_rate
        })

    # 👇 Parties add karna zaroori hai
    parties = Party.objects.all()

    context = {
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'profit': profit,
        'stocks': stocks,
        'parties': parties,  # 👈 now available for template
    }

    return render(request, 'dashboard.html', context)

@login_required
def company_list(request):
    companies = Company.objects.all()
    return render(request, 'company/list.html', {'companies': companies})

@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    purchases = Purchase.objects.filter(company=company)
    payments = CompanyPayment.objects.filter(company=company)

    # --- Total purchase (qty × rate) ---
    total_purchase = purchases.aggregate(
        total=Sum(F('qty') * F('rate'))
    )['total'] or 0

    # --- Total payment given to this company ---
    total_payment = payments.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # --- Pending payment ---
    pending_payment = total_purchase - total_payment

    # --- Add Payment Form ---
    if request.method == 'POST':
        form = CompanyPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_detail', pk=pk)
    else:
        form = CompanyPaymentForm(initial={'company': company})

    context = {
        'company': company,
        'purchases': purchases,
        'payments': payments,
        'form': form,
        'total_purchase': total_purchase,
        'total_payment': total_payment,
        'pending_payment': pending_payment,
    }
    return render(request, 'company/detail.html', context)

@login_required
def company_payment_pdf(request, pk):
    company = get_object_or_404(Company, pk=pk)
    payments = CompanyPayment.objects.filter(company=company)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{company.name}_payments.pdf"'
    p = canvas.Canvas(response, pagesize=A4)
    y = 800
    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, y, f'Payments to {company.name}')
    y -= 30
    p.setFont('Helvetica', 11)
    for pay in payments:
        p.drawString(40, y, f'{pay.date}  |  {pay.amount}  |  {pay.note or ""}')
        y -= 20
        if y < 80:
            p.showPage(); y = 800
    p.showPage()
    p.save()
    return response

@login_required
def product_list(request):
    products = Product.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'product/list.html', {'products': products, 'form': form})

@login_required
def party_list(request):
    parties = Party.objects.all()
    if request.method == 'POST':
        form = PartyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('party_list')
    else:
        form = PartyForm()
    return render(request, 'party/list.html', {'parties': parties, 'form': form})


@login_required
def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()

            # stock update
            stock, _ = Stock.objects.get_or_create(product=purchase.product)
            stock.quantity += purchase.qty
            stock.rate = purchase.rate 
            stock.save()

            # transaction save
            StockTransaction.objects.create(
                product_name=str(purchase.product),   # "Pepsi - 1L"
                transaction_type='PURCHASE',
                quantity=purchase.qty,
                price_per_unit=purchase.rate
            )

            return redirect('dashboard')
    else:
        form = PurchaseForm()
    return render(request, 'purchase/form.html', {'form': form})

@login_required
def add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()

            # stock update
            stock, _ = Stock.objects.get_or_create(product=sale.product)
            stock.quantity -= sale.qty
            stock.save()

            # transaction save
            StockTransaction.objects.create(
                product_name=str(sale.product),   # "Pepsi - 1L"
                transaction_type='SALE',
                quantity=sale.qty,
                price_per_unit=sale.rate
            )

            return redirect('dashboard')
    else:
        form = SaleForm()
    return render(request, 'sale/form.html', {'form': form})

@login_required
def add_expense(request):
    # list of expenses
    expenses = Expense.objects.order_by('-date')

    # total expenses ka sum
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # save ke baad dashboard
    else:
        form = ExpenseForm()

    return render(request, 'expense/form.html', {
        'form': form,
        'expenses': expenses,
        'total_expenses': total_expenses,
    })

@login_required

def quick_sale(request):
    products = Product.objects.all()
    parties = Party.objects.all()
    

    if request.method == 'POST':
        party_id = request.POST.get('party')
        if not party_id:
            messages.error(request, "Please select a party.")
            return redirect("quick_sale")

        party = Party.objects.get(pk=party_id)

        product_ids = request.POST.getlist('product')
        qtys = request.POST.getlist('qty')
        rates = request.POST.getlist('rate')
        discounts = request.POST.getlist('discount')

        sales = []
        gross_total = Decimal(0)
        total_discount = Decimal(0)
        net_total = Decimal(0)

        # --- Safe loop with zip ---
        for pid, q, r, d in zip(product_ids, qtys, rates, discounts):
            if not pid or not q:  # agar product ya qty empty hai to skip
                continue

            product = Product.objects.get(pk=pid)
            qty = Decimal(q or 0)
            discount = Decimal(d or 0)

            # --- Agar rate empty hai to stock ka rate uthao ---
            if r:
                rate = Decimal(r)
            else:
                stock = Stock.objects.filter(product=product).first()
                rate = Decimal(stock.rate) if stock and stock.rate else Decimal(0)

            amount = (qty * rate) - discount
            gross_total += qty * rate
            total_discount += discount
            net_total += amount

            sale = Sale.objects.create(
                product=product,
                party=party,
                qty=qty,
                rate=rate,
                discount=discount,
                amount=amount,
                date=timezone.now()
            )
            sales.append(sale)

            # Stock update
            stock, _ = Stock.objects.get_or_create(product=product)
            stock.quantity -= int(qty)
            stock.save()

            # Discount as Expense
            if discount > 0:
                Expense.objects.create(
                    title=f"Discount on {product.name}",
                    amount=discount,
                    exp_type="other",
                )

        # --- PDF Generate ---
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{party.id}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        y = 800
        p.setFont("Helvetica-Bold", 16)
        p.drawString(40, y, f"Invoice - Party: {party.name}")
        y -= 40
        p.setFont("Helvetica", 12)
        p.drawString(40, y, f"Date: {timezone.now().strftime('%d-%m-%Y')}")
        y -= 30

        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, "Product")
        p.drawString(200, y, "Qty")
        p.drawString(260, y, "Rate")
        p.drawString(330, y, "Discount")
        p.drawString(420, y, "Amount")
        y -= 20
        p.line(40, y, 500, y)
        y -= 20

        p.setFont("Helvetica", 11)
        for s in sales:
            p.drawString(40, y, f"{s.product.name} - {s.product.size}")
            p.drawString(200, y, str(s.qty))
            p.drawString(260, y, str(s.rate))
            p.drawString(330, y, str(s.discount))
            p.drawString(420, y, str(s.amount))
            y -= 20

        y -= 20
        p.line(40, y, 500, y)
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(260, y, "Gross Total:")
        p.drawString(420, y, str(gross_total))
        y -= 20
        p.drawString(260, y, "Discount:")
        p.drawString(420, y, str(total_discount))
        y -= 20
        p.drawString(260, y, "Net Total:")
        p.drawString(420, y, str(net_total))

        p.showPage()
        p.save()
        return response

    return render(request, 'quick_sale.html', {'products': products, 'parties': parties})


# Web report with filter
@login_required
def sales_report(request):
    parties = Party.objects.all()
    products = Product.objects.all()
    sales = Sale.objects.all()

    party_id = request.GET.get("party")
    product_id = request.GET.get("product")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if party_id:
        sales = sales.filter(party_id=party_id)
    if product_id:
        sales = sales.filter(product_id=product_id)
    if start_date and end_date:
        sales = sales.filter(date__range=[start_date, end_date])

    return render(request, "sales_report.html", {
        "sales": sales,
        "parties": parties,
        "products": products,
    })


# PDF report with same filters
@login_required
def sales_report_pdf(request):
    sales = Sale.objects.all()

    party_id = request.GET.get("party")
    product_id = request.GET.get("product")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if party_id:
        sales = sales.filter(party_id=party_id)
    if product_id:
        sales = sales.filter(product_id=product_id)
    if start_date and end_date:
        sales = sales.filter(date__range=[start_date, end_date])

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'

    # Create PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Sales Report")

    # Table Header
    y = height - 100
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Date")
    p.drawString(120, y, "Party")
    p.drawString(250, y, "Product")
    p.drawString(400, y, "Qty")
    p.drawString(460, y, "Total")

    # Table Rows
    p.setFont("Helvetica", 11)
    y -= 20
    for sale in sales:
        p.drawString(50, y, str(sale.date))
        p.drawString(120, y, str(sale.party.name))
        p.drawString(250, y, str(sale.product.name))
        p.drawString(400, y, str(sale.qty))
        p.drawString(460, y, str(sale.amount))
        y -= 20

        if y < 50:  # New page if space finishes
            p.showPage()
            y = height - 100

    p.save()
    return response


@login_required
def company_purchase_summary(request):
    company_summary = []

    companies = Company.objects.all()
    for c in companies:
        # Get all purchases for this company
        purchases = Purchase.objects.filter(company=c).order_by('date')

        # Add current stock + pending for each purchase
        purchase_data = []
        for p in purchases:
            # --- current stock ---
            try:
                current_stock = Stock.objects.get(product=p.product).quantity
            except Stock.DoesNotExist:
                current_stock = 0

            # --- pending amount for this purchase (if you store it) ---
            # Agar aap Purchase model me 'paid' ya 'payment' store karte ho:
            paid = getattr(p, 'paid', 0) or 0   # agar p.paid field hai
            pending = (p.qty * p.rate) - paid   # pending amount per purchase

            purchase_data.append({
                'date': p.date,
                'product': str(p.product),   # product ka naam show ho
                'qty': p.qty,
                'rate': p.rate,
                'amount': p.qty * p.rate,
                'current_stock': current_stock,
                'pending': pending,          # template me use ke liye
            })

        # --- Total purchase amount ---
        total_purchase = sum([item['amount'] for item in purchase_data])

        # --- Total payments made to company ---
        total_payment = CompanyPayment.objects.filter(company=c).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # --- Pending payment for the company ---
        pending_payment = total_purchase - total_payment

        company_summary.append({
            'company': c,
            'purchases': purchase_data,
            'total_purchase': total_purchase,
            'total_payment': total_payment,
            'pending_payment': pending_payment,
        })

    context = {
        'company_summary': company_summary
    }

    return render(request, 'company_purchase_summary.html', context)





# stock
@login_required
def stock_dashboard(request):
    # --- Total Investment (all purchases) ---
    total_investment = Purchase.objects.aggregate(
        total=Sum(F('qty') * F('rate'))
    )['total'] or Decimal('0.00')

    # --- Total Sales (all sales) ---
    total_sales = Sale.objects.aggregate(
        total=Sum(F('qty') * F('rate'))
    )['total'] or Decimal('0.00')

    # --- Profit Calculation ---
    profit = Decimal('0.00')
    sales = Sale.objects.select_related('product')

    for sale in sales:
        sold_qty = sale.qty

        # Calculate total cost & qty for this product
        purchase_agg = Purchase.objects.filter(product=sale.product).aggregate(
            total_cost=Sum(F('qty') * F('rate')),
            total_qty=Sum('qty')
        )

        total_cost = purchase_agg['total_cost'] or Decimal('0.00')
        total_qty = purchase_agg['total_qty'] or Decimal('0.00')

        if total_qty > 0:
            avg_purchase_rate = total_cost / total_qty
        else:
            avg_purchase_rate = Decimal('0.00')

        profit += (sale.rate * sold_qty) - (avg_purchase_rate * sold_qty)

    # --- Stock Summary (with last purchase rate) ---
    stock_summary = []
    for stock in Stock.objects.select_related('product'):
        last_purchase = Purchase.objects.filter(product=stock.product).order_by('-id').first()
        last_rate = last_purchase.rate if last_purchase else Decimal('0.00')

        worth = stock.quantity * last_rate

        stock_summary.append({
            "product": stock.product,
            "quantity": stock.quantity,
            "rate": last_rate,   # last rate of purchase
            "worth": worth,
        })

    # --- Recent Transactions (last 10) ---
    transactions = StockTransaction.objects.order_by('-date')[:10]

    # --- Context for Template ---
    context = {
        'total_investment': total_investment,
        'total_sales': total_sales,
        'profit': profit,
        'stock_summary': stock_summary,
        'transactions': transactions,
    }
    return render(request, 'stock_dashboard.html', context)


# ------------------------
# Party Ledger
# ------------------------
@login_required
def party_ledger(request, party_id):
    """Show ledger details of a specific party."""
    party = get_object_or_404(Party, pk=party_id)

    # --- Sales ---
    sales = Sale.objects.filter(party=party).order_by("-date")

    # --- Product-wise summary ---
    sales_summary = (
        sales.values("product__name", "product__size")
        .annotate(total_qty=Sum("qty"), total_amount=Sum("amount"))
        .order_by("product__name", "product__size")
    )

    # --- Payments ---
    payments = Payment.objects.filter(party=party).order_by("-date")

    # --- Transactions ---
    transactions = Transaction.objects.filter(party=party).order_by("-date")

    # --- Totals ---
    total_sales = sales.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    balance = total_sales - total_paid

    # --- Add / Update Payment ---
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")   # hidden field for update
        amount = request.POST.get("amount")
        date = request.POST.get("date") or timezone.now().date()

        if amount:
            try:
                amount = Decimal(amount)  # Convert to Decimal
            except (ValueError, TypeError):
                amount = Decimal("0.00")

            if payment_id:  # Update existing payment
                payment = get_object_or_404(Payment, id=payment_id, party=party)
                payment.amount = amount
                payment.date = date
                payment.save()
            else:  # Create new payment
                Payment.objects.create(
                    party=party,
                    amount=amount,
                    date=date
                )

        return redirect("party_ledger", party_id=party.id)

    context = {
        "party": party,
        "sales": sales,
        "sales_summary": sales_summary,
        "payments": payments,
        "transactions": transactions,
        "total_sales": total_sales,
        "total_paid": total_paid,
        "balance": balance,
    }

    return render(request, "party_ledger.html", context)



@login_required
def grand_summary(request):
    # 🟩 STOCK summary (products & stock-in-hand)
    stocks = []
    all_products = Stock.objects.values_list('product', flat=True).distinct()

    total_profit = 0  # for sold items only

    for product_id in all_products:
        # purchased
        purchased_qty = Purchase.objects.filter(product_id=product_id).aggregate(
            total=Sum('qty')
        )['total'] or 0

        purchased_amount = Purchase.objects.filter(product_id=product_id).aggregate(
            total=Sum(ExpressionWrapper(F('qty') * F('rate'), output_field=DecimalField()))
        )['total'] or 0

        # sold
        sold_qty = Sale.objects.filter(product_id=product_id).aggregate(
            total=Sum('qty')
        )['total'] or 0

        sold_amount = Sale.objects.filter(product_id=product_id).aggregate(
            total=Sum(ExpressionWrapper(F('qty') * F('rate'), output_field=DecimalField()))
        )['total'] or 0

        # stock in hand
        stock_in_hand = purchased_qty - sold_qty

        # get last rate (or any rate from stock)
        stock_obj = Stock.objects.filter(product_id=product_id).first()
        rate = stock_obj.rate if stock_obj else 0

        total_price = stock_in_hand * rate

        # 🟩 Profit per product (sold only)
        purchase_unit_cost = (purchased_amount / purchased_qty) if purchased_qty else 0
        cogs = sold_qty * purchase_unit_cost  # cost of goods sold
        profit_per_product = sold_amount - cogs
        total_profit += profit_per_product

        stocks.append({
            'product_name': stock_obj.product.name if stock_obj else '',
'product_size': stock_obj.product.size if stock_obj and hasattr(stock_obj.product, 'size') else '',  # 👈 add this
'rate': rate,
'stock_in_hand': stock_in_hand,
'total_price': total_price,
'sold_qty': sold_qty,
'profit_per_product': profit_per_product,

        })

    grand_total_stock = sum(item['total_price'] for item in stocks)

    # 🟩 EXPENSE total
    total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

    # 🟩 GRAND PROFIT (sold products profit - expenses)
    grand_profit = total_profit - total_expense

    # 🟩 COMPANY-WISE SUMMARY + Total Investment / Pending
    company_summary = []
    total_investment = 0  # total paid to companies
    total_pending_payment = 0
    for c in Company.objects.all():
        # total purchase per company
        company_purchase = Purchase.objects.filter(company=c).aggregate(
            total=Sum(ExpressionWrapper(F('qty') * F('rate'), output_field=DecimalField()))
        )['total'] or 0

        # total payment per company
        company_payment = CompanyPayment.objects.filter(company=c).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # pending
        pending_payment = company_purchase - company_payment

        total_investment += company_payment
        total_pending_payment += pending_payment

        company_summary.append({
            'company': c.name,
            'total_purchase': company_purchase,
            'total_payment': company_payment,
            'pending_payment': pending_payment
        })

    # 🟩 NET WORTH calculation (Investment + Stock Worth + Profit - Expenses)
    # yahan aap apna initial investment bhi include kar sakte ho:
    initial_investment = 5000000  # yahan aap default value ya form se le sakte ho

    net_worth = (
        initial_investment +            # jo aapne lagaya
        grand_total_stock +             # abhi jo stock ki worth hai
        grand_profit                    # sold ka profit – expenses already minus hai
    ) - total_pending_payment          # jo abhi companies ko dena hai woh minus karna

    context = {
        'stocks': stocks,
        'grand_total_stock': grand_total_stock,
        'total_profit_sold_items': total_profit,
        'total_expense': total_expense,
        'grand_profit': grand_profit,
        'company_summary': company_summary,
        'total_investment': total_investment,
        'total_pending_payment': total_pending_payment,
        'initial_investment': initial_investment,
        'net_worth': net_worth,
    }

    return render(request, 'grand_summary.html', context)
