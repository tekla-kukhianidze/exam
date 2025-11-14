from rest_framework import serializers
from .models import (
    CustomUser, Category, Product, ProductImage,
    Cart, CartItem, Order, OrderItem
)



# --- Category/Product Serializers ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'is_active']
        read_only_fields = ['slug', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_main']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'description',
            'price', 'stock', 'is_available', 'featured', 'color', 'material', 'images'
        ]


# --- User & Auth Serializers ---
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'phone', 'address', 'birth_date']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        Cart.objects.get_or_create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'address', 'birth_date']
        read_only_fields = ['username', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name()


# --- Cart Serializers ---
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    item_total = serializers.SerializerMethodField()
    # მხოლოდ product-ის ID-ს იღებს დასამატებლად
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_available=True))

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'quantity', 'item_total']

    def get_item_total(self, obj):
        return obj.get_item_total()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'total_items_count', 'updated_at']
        read_only_fields = ['user', 'updated_at']

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_total_items_count(self, obj):
        return obj.get_total_items_count()


# --- Order Serializers ---
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price', 'get_total_price']
        read_only_fields = ['price', 'get_total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'total_amount',
            'shipping_address', 'phone', 'notes', 'created_at', 'items'
        ]
        read_only_fields = ['order_number', 'user', 'total_amount', 'created_at', 'updated_at', 'status']


# --- Password Change Serializer ---
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("ახალი პაროლი უნდა იყოს მინიმუმ 8 სიმბოლო.")
        return value