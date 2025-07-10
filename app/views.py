from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views import View
from .models import Customer, Product, Cart, PriceAlert
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from .forms import CustomerRegistrationForm,LoginForm,  CustomerProfileform
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re
import json
import ast
from datetime import datetime
from rapidfuzz import fuzz
from .models import Category

@csrf_protect
def contact_view(request):
    if request.method == 'POST':
        # handle form submission logic here
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Process form data (save to database or send email)
        return HttpResponse("Message sent successfully!")
    return render(request, 'contact.html')

def get_descendant_categories(category):
    # Category is already imported at the top
    descendants = []
    children = Category.objects.filter(parent=category)
    for child in children:
        descendants.append(child)
        descendants.extend(get_descendant_categories(child))
    return descendants

def home(request):
    # Show latest products as new products
    new_products = Product.objects.order_by('-id')[:8]  # Show latest 8 products
    main_categories = Category.objects.filter(parent=None)
    return render(request, "app/index.html", {
        'new_products': new_products,
        'main_categories': main_categories,
    })
def about(request):
    return render(request, "app/about.html")
def contact(request):
    return render(request, "app/contact.html")

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to home or dashboard
            else:
                messages.error(request, "Invalid login credentials.")
        else:
            messages.error(request, "Form is not valid.")
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})
class CategoryView(View):
    def get(self, request, val=None):
        if not val:
            return redirect('home')
        # Find the selected category by name
        category = Category.objects.filter(name=val).first()
        if not category:
            return render(request, "app/category.html", {"product": [], "pro": val, "title": []})
        # Get children of this category for navigation
        children = Category.objects.filter(parent=category)
        # If the category has children, show products from all descendants
        if children.exists():
            descendant_categories = get_descendant_categories(category)
            if descendant_categories:
                products = Product.objects.filter(category__in=descendant_categories)
            else:
                products = Product.objects.none()
            return render(request, "app/category.html", {"product": products, "pro": category.name, "title": children})
        else:
            # Leaf category: show only products in this category
            products = Product.objects.filter(category=category)
            return render(request, "app/category.html", {"product": products, "pro": category.name, "title": []})

class CategoryTitle(View):
    def get(self,request,val):
        product = Product.objects.filter(title= val)
        title = Product.objects.filter(category=product[0].category).values('title')
        return render(request,"app/category.html",locals())
class ProductDetail(View):
    def get(self, request, pk):
        # Fetch the specific product based on pk
        product = Product.objects.get(pk=pk)
        existing_alert = None
        if request.user.is_authenticated:
            existing_alert = PriceAlert.objects.filter(user=request.user, product=product, fulfilled=False).first()
        return render(request, "app/productdetail.html", {"product": product, "existing_alert": existing_alert})
class CustomerRegistrationView(View):
   def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/rregistration.html', locals())
   def post(self,request):
       form = CustomerRegistrationForm(request.POST)
       if form.is_valid():
           form.save()
           messages.success(request,"congratulation! You are part of chick style community")
       else:
           messages.warning(request,"Invalid data")
       
       return render(request, 'app/rregistration.html', locals())
class ProfileView(View):
    def get(self,request):
       form =  CustomerProfileform()
       return render(request, 'app/profile.html', locals())
    def post(self,request):
        form = CustomerProfileform(request.POST)
        if form.is_valid():
            user =request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']
            
            reg = Customer(
                user=user,
                name=name,
                locality=locality,
                city=city,
                mobile=mobile,
                state=state,
                zipcode=zipcode
            )
            reg.save()
            messages.success(request, 'Your profile has been updated successfully.')
        else:
            # Add error message if form is not valid
            messages.error(request, 'There was an error updating your profile. Please check your inputs.')
        return render(request, 'app/profile.html', locals())
           
def address(request):
    add = Customer.objects.filter(user=request.user)
    return render ( request ,'app/address.html',locals())

class updateAdress(View):
    def get(self,request,pk):
        add = Customer.objects.get(pk=pk)
        form = CustomerProfileform(instance=add)
        return render ( request ,'app/updateaddress.html',locals())
    def post(self,request,pk):
        form = CustomerProfileform(request.POST)
        if form.is_valid():
          add = Customer.objects.get(pk=pk)
          add.name = form.cleaned_data['name']
          add.locality = form.cleaned_data['locality']
          add.city = form.cleaned_data['city']
          add.mobile = form.cleaned_data['mobile']
          add.state = form.cleaned_data['state']
          add.zipcode = form.cleaned_data['zipcode']

          add.save()
          messages.success(request,"Congratulations! profile updated")
        
        else:
          messages.warning(request,"invalid data :)")
        return redirect("address")
@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = Product.objects.get(id=product_id)
    Cart.objects.create(user=user, product=product)
    return redirect("showcart")

@login_required
def show_cart(request):
    user=request.user
    cart = Cart.objects.filter(user=user)
    amount = 0
    for p in cart:
        value = p.quantity * p.product.discounted_price
        amount = amount + value
    totalamount = amount + 40

    return render (request ,'app/addtocart.html',locals())
from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        # Allow GET request for logout
        return super().get(request, *args, **kwargs)
def logout_view(request):
   

    logout(request)  # This function clears the session and logs out the user.
    return redirect('login')     

def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity +=1
        c.save()
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount = amount + value
        totalamount = amount + 40
        data= {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount':totalamount

        }
        return JsonResponse(data)

def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity -=1
        c.save()
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount = amount + value
        totalamount = amount + 40
        data= {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount':totalamount

        }
        return JsonResponse(data)

    
def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity -=1
        c.delete()
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount = amount + value
        totalamount = amount + 40
        data= {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount':totalamount

        }
        return JsonResponse(data)

# ---------------------------------------------------------------------------
#  PRICE ALERTS
# ---------------------------------------------------------------------------

@login_required
@require_POST
def set_price_alert(request, pk):
    """Handle the form submission coming from the product-detail page."""
    product = Product.objects.get(pk=pk)

    try:
        target_price = float(request.POST.get('target_price'))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid price value.")
        return redirect('product-detail', pk=pk)

    buy_when_drop = bool(request.POST.get('buy_when_drop'))

    alert, created = PriceAlert.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={
            'target_price': target_price,
            'buy_when_drop': buy_when_drop,
            'fulfilled': False,
        }
    )

    if created:
        msg = f"Alert set at ₹{target_price}. We'll notify you when the price drops!"
    else:
        msg = f"Alert updated to ₹{target_price}."
    if buy_when_drop:
        msg += " We'll automatically buy at that price."
    messages.success(request, msg)

    return redirect('product-detail', pk=pk)

@login_required
def buy_now(request):
    """Add item to cart (if not already) and go straight to checkout."""
    user = request.user
    product_id = request.GET.get('prod_id')
    product = Product.objects.get(id=product_id)
    Cart.objects.get_or_create(user=user, product=product, defaults={'quantity': 1})
    return redirect('checkout')

def search(request):
    query = request.GET.get('query', '')
    results = []
    if query:
        results = Product.objects.filter(Q(title__icontains=query) | Q(category__icontains=query))
    return render(request, 'app/search_results.html', {'query': query, 'results': results})

def assistant(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    chat_history = request.session['chat_history']
    response = None
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if request.method == "POST":
        if 'clear_chat' in request.POST or request.POST.get('clear_chat') is not None:
            request.session['chat_history'] = []
            return render(request, 'app/assistant.html', {'chat_history': []})
        user_query = request.POST.get("query", "")
        # Always try to get the Gemini API key from the environment
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            from dotenv import load_dotenv
            load_dotenv()
            GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            response = "<div class='text-danger'>Gemini API key is missing. Please set GEMINI_API_KEY in your .env file or environment variables.</div>"
            chat_history.append({'user': user_query, 'assistant': response, 'timestamp': now, 'type': 'current'})
            request.session['chat_history'] = chat_history
            return render(request, 'app/assistant.html', {'chat_history': chat_history})
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Detect if the query is a recipe/cooking request
        is_recipe = any(word in user_query.lower() for word in ['cook', 'make', 'prepare', 'recipe', 'how to'])
        if is_recipe:
            # 1. Get recipe and ingredients under budget
            recipe_prompt = f"""
            Give me a simple recipe for: {user_query}. List the ingredients and their approximate prices in INR, total cost under the mentioned budget if possible. Format as:
            Recipe: ...\nIngredients:\n- item1 (price)\n- item2 (price)\n...\nInstructions: ...
            """
            recipe_response = model.generate_content(recipe_prompt)
            recipe_text = recipe_response.text.strip()
            # 2. Extract keywords for product matching
            keyword_prompt = f"""
            From this recipe and ingredient list, extract keywords that could match products in an online grocery or general store. Return as a Python list of strings.\n\n{recipe_text}
            """
            keyword_response = model.generate_content(keyword_prompt)
            import ast
            try:
                keywords = ast.literal_eval(keyword_response.text.strip().split('```')[-1] if '```' in keyword_response.text else keyword_response.text)
                if not isinstance(keywords, list):
                    keywords = []
            except Exception:
                keywords = []
            import re
            budget_match = re.search(r'under\s*₹?\s*(\d+)', user_query, re.IGNORECASE)
            budget = int(budget_match.group(1)) if budget_match else 100  # Default to 100 if not found
            # Build product list under budget
            available_products = Product.objects.filter(discounted_price__lte=budget)
            product_list = [
                f"{p.title} - ₹{p.discounted_price}: {p.description[:50]}" for p in available_products
            ]
            product_list_str = "\n".join(product_list)
            gemini_match_prompt = f"""
User query: {user_query}
Here is a list of products available (title, price, short description):

{product_list_str}

Which of these products best match the user's request? Only return a valid Python list of product titles. Do not include any explanation or summary.
"""
            gemini_match_response = model.generate_content(gemini_match_prompt)
            try:
                selected_titles = ast.literal_eval(gemini_match_response.text.strip().split('```')[-1] if '```' in gemini_match_response.text else gemini_match_response.text)
                if not isinstance(selected_titles, list):
                    selected_titles = []
            except Exception:
                selected_titles = []
            matched_products = Product.objects.filter(title__in=selected_titles)
            # Fallback: If Gemini returns no matches, use keyword matching for all ingredients
            if not matched_products.exists() and keywords:
                print("Fallback keyword matching triggered. Keywords:", keywords)  # Debug print
                matched_products = Product.objects.none()
                for kw in keywords:
                    # --- NEW LOGIC: hierarchical category matching ---
                    cat_qs = Category.objects.filter(name__icontains=kw)
                    if cat_qs.exists():
                        all_cats = []
                        for cat in cat_qs:
                            all_cats.append(cat)
                            all_cats.extend(get_descendant_categories(cat))
                        matched_products = matched_products | Product.objects.filter(
                            discounted_price__lte=budget,
                            category__in=all_cats
                        )
                    # --- End new logic ---
                    matched_products = matched_products | Product.objects.filter(
                        discounted_price__lte=budget,
                        title__icontains=kw
                    )
                    matched_products = matched_products | Product.objects.filter(
                        discounted_price__lte=budget,
                        description__icontains=kw
                    )
                matched_products = matched_products.distinct()
                print("Matched products after fallback:", list(matched_products))  # Debug print
            # Final fallback: fuzzy match user query words to product title/description words if still no products
            if not matched_products.exists() and budget:
                print("Final fallback: fuzzy matching user query to product words.")
                from rapidfuzz import fuzz
                user_words = re.findall(r'\b\w+\b', user_query)
                all_titles = Product.objects.values_list('title', flat=True)
                all_descriptions = Product.objects.values_list('description', flat=True)
                combined_text = " ".join(list(all_titles) + list(all_descriptions)).lower()
                db_keywords = list(set(re.findall(r'\b\w+\b', combined_text)))
                matched_keywords = []
                for user_word in user_words:
                    for db_word in db_keywords:
                        if fuzz.partial_ratio(user_word, db_word) > 85:
                            matched_keywords.append(db_word)
                from django.db.models import Q
                keyword_filter = Q()
                for kw in matched_keywords:
                    keyword_filter |= Q(title__icontains=kw) | Q(description__icontains=kw)
                matched_products = Product.objects.filter(
                    discounted_price__lte=budget
                ).filter(keyword_filter)
                matched_products = matched_products.distinct()
                print("Matched products after fuzzy fallback:", list(matched_products))
            # 4. Prepare product cards
            product_cards = []
            for p in matched_products:
                detail_url = f"/product-detail/{p.pk}/"
                add_to_cart_url = f"/add-to-cart/?prod_id={p.pk}"
                card = f"""
                <div class='card mb-3' style='max-width: 500px;'>
                    <div class='row g-0'>
                        <div class='col-md-4'>
                            <img src='{p.product_image.url if p.product_image else ''}' class='img-fluid rounded-start' alt='{p.title}'>
                        </div>
                        <div class='col-md-8'>
                            <div class='card-body'>
                                <h5 class='card-title'>{p.title}</h5>
                                <p class='card-text'><b>₹{p.discounted_price}</b></p>
                                <p class='card-text'><small class='text-muted'>{p.description}</small></p>
                                <a href='{detail_url}' class='btn btn-outline-primary btn-sm' target='_blank'>View Product</a>
                                <a href='{add_to_cart_url}' class='btn btn-success btn-sm ms-2'>Add to Cart</a>
                            </div>
                        </div>
                    </div>
                </div>
                """
                product_cards.append(card)
            # 5. Compose the response
            summary = f"<div class='mb-2'><b>Recipe & Ingredients:</b><br>{recipe_text.replace('\n','<br>')}</div>"
            if matched_products.exists():
                summary += "<div class='mb-2'><b>Recommended products from our store under your budget:</b></div>"
                summary += ''.join(product_cards)
            else:
                summary += "<div class='mb-2 text-muted'>No matching products found in our store under your budget, but here's a recipe you can try!" + "</div>"
            response = summary
        else:
            # --- Product recommendation logic ---
            prompt = f"""
            Extract the shopping category and budget from this query: '{user_query}'. 
            Return as JSON with keys 'category' and 'budget'. If no budget is mentioned, set budget to null. If no category, set category to null.
            """
            try:
                gemini_response = model.generate_content(prompt)
                import json
                parsed = json.loads(gemini_response.text.strip().split('```')[-1] if '```' in gemini_response.text else gemini_response.text)
                category = parsed.get('category')
                budget = parsed.get('budget')
                if budget:
                    try:
                        budget = int(budget)
                    except Exception:
                        budget = None
            except Exception:
                import re
                budget_match = re.search(r'under\s*₹?\s*(\d+)', user_query, re.IGNORECASE)
                budget = int(budget_match.group(1)) if budget_match else None
                category_keywords = ['outfit', 'dress', 'shirt', 'lehenga', 'jeans', 'wedding', 'kurta', 'saree', 'top', 'skirt', 'pant', 'tshirt', 'gown', 'suit', 'blouse', 'jacket', 'coat', 'trouser', 'salwar', 'choli', 'dupatta', 'ethnic', 'western', 'party', 'casual', 'formal']
                category = next((word for word in category_keywords if word in user_query.lower()), None)
            # --- Improved strict category and budget matching logic ---
            matched_products = Product.objects.none()
            response = None
            if category:
                cat_qs = Category.objects.filter(name__icontains=category)
                if cat_qs.exists():
                    all_cats = []
                    for cat in cat_qs:
                        all_cats.append(cat)
                        all_cats.extend(get_descendant_categories(cat))
                    if budget:
                        matched_products = Product.objects.filter(
                            category__in=all_cats,
                            discounted_price__lte=budget
                        )
                    else:
                        response = f"Please specify your budget for {category}."
                else:
                    response = f"Sorry, I couldn't find a matching category for '{category}'. Please clarify."
            else:
                response = "Please specify what category or type of product you are looking for."
            # If we have matching products, build product cards
            if matched_products.exists():
                product_cards = []
                for p in matched_products:
                    detail_url = f"/product-detail/{p.pk}/"
                    add_to_cart_url = f"/add-to-cart/?prod_id={p.pk}"
                    card = f"""
                    <div class='card mb-3' style='max-width: 500px;'>
                        <div class='row g-0'>
                            <div class='col-md-4'>
                                <img src='{p.product_image.url if p.product_image else ''}' class='img-fluid rounded-start' alt='{p.title}'>
                            </div>
                            <div class='col-md-8'>
                                <div class='card-body'>
                                    <h5 class='card-title'>{p.title}</h5>
                                    <p class='card-text'><b>₹{p.discounted_price}</b></p>
                                    <p class='card-text'><small class='text-muted'>{p.description}</small></p>
                                    <a href='{detail_url}' class='btn btn-outline-primary btn-sm' target='_blank'>View Product</a>
                                    <a href='{add_to_cart_url}' class='btn btn-success btn-sm ms-2'>Add to Cart</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                    product_cards.append(card)
                response = f"<div class='mb-2'><b>Recommended products in {category} under your budget:</b></div>"
                response += ''.join(product_cards)
            elif response is None:
                response = f"No matching products found in {category} under your budget."
            chat_history.append({'user': user_query, 'assistant': response, 'timestamp': now, 'type': 'current'})
            request.session['chat_history'] = chat_history
            return render(request, 'app/assistant.html', {'chat_history': chat_history})
    return render(request, 'app/assistant.html', {'chat_history': chat_history})

