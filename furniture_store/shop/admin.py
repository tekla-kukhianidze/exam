from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Category, Product, ProductImage,
    Cart, CartItem, Order, OrderItem
)


# --- Inline Classes ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class CartItemInline(admin.TabularInline):
    model = CartItem
    readonly_fields = ('product', 'quantity')
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price', 'get_total_price')
    fields = ('product', 'quantity', 'price', 'get_total_price')
    extra = 0
    # get_total_price არის მოდელზე არსებული მეთოდი, რომელიც გამოჩნდება ადმინში


# --- Admin Classes ---
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('პერსონალური ინფორმაცია', {'fields': ('phone', 'address', 'birth_date')}),
    )
    list_display = ('username', 'email', 'get_full_name', 'phone', 'is_staff', 'is_active')
    search_fields = ('username', 'phone', 'first_name', 'last_name')
    list_filter = ('address', 'is_staff', 'is_active')

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = 'სრული სახელი'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_available', 'featured', 'color', 'material')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('category', 'color', 'material', 'is_available', 'featured')
    list_editable = ('price', 'stock', 'is_available', 'featured')
    inlines = [ProductImageInline]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_total_price', 'get_total_items_count', 'updated_at')
    search_fields = ('user__username', 'user__first_name')
    list_filter = ('user',)
    inlines = [CartItemInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'shipping_address', 'created_at')
    search_fields = ('order_number', 'user__username', 'phone')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]


from django.contrib import admin

# Register your models here.
