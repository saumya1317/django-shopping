from django.contrib import admin
from .models import Product, Customer, Cart, PriceAlert, Category, Order, OrderItem

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(PriceAlert)
admin.site.register(Order)
admin.site.register(OrderItem)