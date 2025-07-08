from django.contrib import admin
from .models import Product, Customer,Cart, PriceAlert

# Register your models here.
@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'selling_price', 'discounted_price', 'category']
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'locality', 'city', 'state','zipcode']
@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display= ['id','user','product','quantity']
@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'target_price', 'buy_when_drop', 'fulfilled']