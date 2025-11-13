from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction

from .models import (
    CustomUser, Category, Product, Cart, CartItem, Order, OrderItem
)
from .serializers import (
    CategorySerializer, ProductSerializer, UserRegistrationSerializer,
    UserProfileSerializer, CartSerializer, OrderSerializer
)


# Celery Tasks-ის იმპორტი
# from .tasks import send_order_confirmation_email, update_order_status


# --- Category Views ---
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


# --- Product Views ---
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    # prefetch_related სურათებისთვის და select_related კატეგორიისთვის
    queryset = Product.objects.filter(is_available=True).select_related('category').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    # ფილტრაცია, ძიება, სორტირება
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__slug', 'color', 'material', 'featured']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']


# --- User & Auth Views ---
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# --- Cart Views ---
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # GET /api/cart/
    def list(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    # POST /api/cart/add/ - პროდუქტის დამატება/რაოდენობის გაზრდა
    @action(detail=False, methods=['post'])
    def add(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id, is_available=True)
        cart, created = Cart.objects.get_or_create(user=request.user)

        if quantity <= 0:
            return Response({"detail": "რაოდენობა უნდა იყოს დადებითი."}, status=status.HTTP_400_BAD_REQUEST)
        if product.stock < quantity:
            return Response({"detail": f"მარაგშია მხოლოდ {product.stock} ერთეული."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product,
                                                                 defaults={'quantity': quantity})

        if not item_created:
            if product.stock < cart_item.quantity + quantity:
                return Response({"detail": f"მარაგის ლიმიტი (სულ {product.stock}) გადაჭარბებულია."},
                                status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity += quantity
            cart_item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    # POST /api/cart/remove/ - პროდუქტის წაშლა ან რაოდენობის შემცირება
    @action(detail=False, methods=['post'])
    def remove(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        if quantity >= cart_item.quantity:
            cart_item.delete()
        elif quantity > 0:
            cart_item.quantity -= quantity
            cart_item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


# --- Order Views ---
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['order_number', 'user__username', 'user__first_name']
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    # POST /api/orders/create/
    @action(detail=False, methods=['post'])
    def create(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.all()

        if not cart_items:
            return Response({"detail": "კალათა ცარიელია."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # 1. შეკვეთის შექმნა (Order)
            total_amount = cart.get_total_price()
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                shipping_address=request.data.get('shipping_address', request.user.address),
                phone=request.data.get('phone', request.user.phone),
                notes=request.data.get('notes')
            )

            # 2. შეკვეთის ერთეულების შექმნა (OrderItem) და მარაგის განახლება
            for item in cart_items:
                if item.product.stock < item.quantity:
                    # აბრუნებს ცვლილებებს, თუ მარაგი არასაკმარისია
                    transaction.set_rollback(True)
                    return Response({"detail": f"პროდუქტის '{item.product.name}' მარაგი არასაკმარისია."},
                                    status=status.HTTP_400_BAD_REQUEST)

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price  # სტატიკური ფასის შენახვა
                )
                item.product.stock -= item.quantity
                item.product.save()

            # 3. კალათის გასუფთავება
            cart_items.delete()

        # 4. Celery Task-ის გამოძახება
        # send_order_confirmation_email.delay(order.id)
        # update_order_status.apply_async((order.id,), countdown=3600)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)



