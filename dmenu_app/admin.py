from django.contrib import admin

# Register your models here.

from .models import Table, MenuItem, Order, OrderItem, Category

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'qr_code')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available','category','image')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user_order_id', 'table', 'created_at', 'total','customer_name','customer_phone','status')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity')
