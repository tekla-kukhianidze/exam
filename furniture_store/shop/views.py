from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .permissions import AllowAny, IsAuthenticated, IsAdminUser, IsOwnerOrAdmin
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.contrib.auth import update_session_auth_hash

from .models import (
    CustomUser, Category, Product, Cart, CartItem, Order, OrderItem
)
from .serializers import (
    CategorySerializer, ProductSerializer, UserRegistrationSerializer,
    UserProfileSerializer, CartSerializer, OrderSerializer, PasswordChangeSerializer
)

from .tasks import send_order_confirmation_email, update_order_status_to_processing



# --- Category Views ---
class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD ოპერაციები კატეგორიებისთვის (საჯარო GET, ადმინის POST/PUT/DELETE).
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_permissions(self):
        # GET (list, retrieve) ნებადართულია ყველასთვის
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        # POST, PUT, PATCH, DELETE ნებადართულია მხოლოდ ადმინისტრატორებისთვის
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


# --- Product Views ---
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    პროდუქტების კატალოგი (წაკითხვა, ფილტრაცია და ძიება)
    """
    queryset = Product.objects.filter(is_available=True).select_related('category').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

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
    """
    კალათის მართვა: ნახვა, პროდუქტის დამატება/შემცირება/წაშლა.
    """
    permission_classes = [IsAuthenticated]

    # GET /api/cart/ (ნაგულისხმევი list მეთოდი)
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

        # მარაგის საწყისი შემოწმება
        if product.stock < quantity:
            return Response({"detail": f"მარაგშია მხოლოდ {product.stock} ერთეული."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product,
                                                                 defaults={'quantity': quantity})

        if not item_created:
            # თუ პროდუქტი უკვე კალათაშია, ვცდილობთ რაოდენობის გაზრდას
            if product.stock < cart_item.quantity + quantity:
                return Response({"detail": f"მარაგის ლიმიტი (სულ {product.stock}) გადაჭარღულია."},
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
    """
    შეკვეთების ნახვა და შექმნა (შექმნა ხდება კალათიდან).
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    # POST /api/orders/create/ - შეკვეთის შექმნა კალათიდან
    @action(detail=False, methods=['post'], url_path='create')
    def create_order_from_cart(self, request):
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
                # იღებს მისამართს/ტელეფონს request-დან, თუ არადა, იყენებს მომხმარებლის პროფილის მონაცემებს
                shipping_address=request.data.get('shipping_address', request.user.address),
                phone=request.data.get('phone', request.user.phone),
                notes=request.data.get('notes')
            )

            # 2. შეკვეთის ერთეულების შექმნა (OrderItem) და მარაგის განახლება
            for item in cart_items:
                if item.product.stock < item.quantity:
                    transaction.set_rollback(True)
                    return Response({"detail": f"პროდუქტის '{item.product.name}' მარაგი არასაკმარისია."},
                                    status=status.HTTP_400_BAD_REQUEST)

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                item.product.stock -= item.quantity
                item.product.save()

            # 3. კალათის გასუფთავება
            cart_items.delete()

        # 4. Celery Task-ის გამოძახება
        send_order_confirmation_email.delay(order.id)
        update_order_status_to_processing.apply_async((order.id,), countdown=3600)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

# --- Password Change View ---
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # შეამოწმეთ ძველი პაროლი
            if not self.object.check_password(serializer.validated_data.get("old_password")):
                return Response({"old_password": ["არასწორია ძველი პაროლი."]}, status=status.HTTP_400_BAD_REQUEST)

            # პაროლის შეცვლა
            self.object.set_password(serializer.validated_data.get("new_password"))
            self.object.save()

            # სესიის ჰეშის განახლება, რათა მომხმარებელი დარჩეს ავტორიზებული
            update_session_auth_hash(request, self.object)

            return Response({"detail": "პაროლი წარმატებით შეიცვალა."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)