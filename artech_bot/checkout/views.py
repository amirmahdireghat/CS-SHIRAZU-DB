import requests
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from checkout.models import invoices, token_price
from admin_panel.models import user_data
from django.utils import timezone
import os

def payment_request(request, id):
    website = os.getenv("WEBSITE_URL")
    merchent = os.getenv("ZARINPAL_MERCHANT_ID")
    
    try:
        # Fetch the invoice by order_id and update status
        invoice = invoices.objects.get(id=id)
        amount = invoice.amount
        # Get the related user object (assuming user_data is the related model)
        user = invoice.user_id
    except invoices.DoesNotExist:
        return HttpResponse("invoice not found")
    
    url = 'https://payment.zarinpal.com/pg/v4/payment/request.json'  # Updated URL
    start_pay_url = 'https://payment.zarinpal.com/pg/StartPay/'  # Corrected URL for StartPay
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    # Build description with user name, phone number
    description = (
        f"Purchase for token, artech bot. "
        f"User: {user.first_name}, Phone: {user.number}"
    )
    data = {
        "merchant_id": merchent,
        "amount": amount,  # Ensure this matches exactly
        "callback_url": f"{website}/checkout/verify/{id}/",
        "description": description,
        "metadata": {
            "order_id": id
        }
    }
    
    # Make the POST request
    response = requests.post(url, json=data, headers=headers)
    # Check if response is valid and handle errors
    try:
        response_data = response.json()
        if 'data' in response_data and 'authority' in response_data['data']:
            authority = response_data['data']["authority"]
            redirect_url = f"{start_pay_url}{authority}"
            return redirect(redirect_url)
        else:
            # Log the error details and return a message
            error_message = response_data.get('errors', 'Unexpected response format from Zarinpal')
            return HttpResponse(f"Payment request failed: {error_message}", status=500)
    except (ValueError, KeyError) as e:
        # Handle JSON decoding errors or missing fields
        return HttpResponse(f"Failed to process payment request: {str(e)}", status=500)

from checkout.models import UserTokenPlan

def payment_verify(request, invoice_id):
    merchent = os.getenv("ZARINPAL_MERCHANT_ID")
    authority = request.GET.get('Authority')
    verify_url = 'https://payment.zarinpal.com/pg/v4/payment/verify.json'
    
    try:
        invoice = invoices.objects.get(id=invoice_id)
        amount = invoice.amount
    except invoices.DoesNotExist:
        return HttpResponse("فاکتور پیدا نشد. در صورتی که پرداخت کرده اید به پشتیبانی آرتک تماس بگیرید.")

    response = requests.post(verify_url, json={
        "merchant_id": merchent,
        "amount": amount,
        "authority": authority
    }, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })

    response_data = response.json()
    data = response_data.get("data", {})

    if data.get("code") == 100:
        try:
            invoice = invoices.objects.get(id=invoice_id)
            user = invoice.user_id  # Related user_data instance

            if invoice.token_plan:
                # Instead of directly updating user.token, create a new UserTokenPlan record.
                UserTokenPlan.objects.create(
                    user=user,
                    token_plan=invoice.token_plan,
                    tokens_remaining=invoice.token_plan.token,
                    expires_at=invoice.expires_at,
                    invoice=invoice
                )
            else:
                return HttpResponse("Token package information missing for this invoice.", status=500)

            invoice.status = "OK"
            invoice.save()
            return HttpResponse(f"Payment successful. Your token plan is now active.")
        except user_data.DoesNotExist:
            return HttpResponse("کاربر پیدا نشد. در صورتی که مبلغی از حساب شما کم شده است با پشتیبانی آرتک تماس بگیرید.")
    else:
        invoice.status = "NOK"
        invoice.save()
        return HttpResponse("پرداخت شما موفقیت آمیز نبوده است. در صورتی که مبلغی از حساب شما کم شده است بعد از ۴۸ ساعت به حساب شما بازمی‌گردد.")
