import os
from dotenv import load_dotenv
import google.generativeai as genai
import re  # <--- MAKE SURE THIS IS HERE, AT THE TOP!
import json
import ast
from datetime import datetime

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '0')) if os.getenv('EMAIL_PORT') else None
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '') == 'True'
DEFAULT_FROM_EMAIL = "no-reply@chickstyle.local"


genai.configure(api_key="AIzaSyBwcwV_uM4Zpo1zNMlirR-tFmABeY57Igg")

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product  # Adjust import as needed


@csrf_exempt
def llm_query(request):
    if request.method == "POST":
        user_query = request.POST.get("query", "")

        # 1. Extract budget (e.g., "under 300")
        budget_match = re.search(r'under\s*₹?\s*(\d+)', user_query, re.IGNORECASE)
        budget = int(budget_match.group(1)) if budget_match else None

        # 2. Extract category/type (e.g., "outfit", "dress", etc.)
        # You can improve this with more NLP or Gemini if needed
        category_keywords = ['outfit', 'dress', 'shirt', 'lehenga', 'jeans', 'wedding', ...]  # Add as needed
        category = next((word for word in category_keywords if word in user_query.lower()), None)

        # 3. Query the database
        products = Product.objects.all()
        if budget:
            products = products.filter(discounted_price__lte=budget)
        if category:
            products = products.filter(category__icontains=category)  # Adjust field as needed

        # 4. Prepare response
        product_list = [
            {
                "name": p.title,
                "price": p.discounted_price,
                "image": p.product_image.url if p.product_image else "",
                "description": p.description,
            }
            for p in products
        ]

        return JsonResponse({"products": product_list})
