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

def home(request):
    clothes_products = Product.objects.exclude(category='F')
    food_products = Product.objects.filter(category='F')
    return render(request, "app/index.html", {
        'clothes_products': clothes_products,
        'food_products': food_products,
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
        # If no category is provided, redirect to the homepage (or any other page)
        if not val:
            return redirect('home')  # Redirects to the homepage (or use the name of any view you want)
        
        # If a category ('val') is provided, show products for that category
        
        product = Product.objects.filter(category=val)
        title = Product.objects.filter(category=val).values('title').annotate(total=Count('title'))
        return render(request, "app/category.html", locals())

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

