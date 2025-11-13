from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, DecimalField
import uuid


# --- 1. Custom User Model ---
class CustomUser(AbstractUser):
    # გაფართოებული ველები
    first_name = models.CharField(max_length=30, verbose_name="სახელი")
    last_name = models.CharField(max_length=30, verbose_name="გვარი")
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="ტელეფონის ნომერი")
    address = models.CharField(max_length=255, verbose_name="მისამართი", blank=True)
    birth_date = models.DateField(null=True, blank=True, verbose_name="დაბადების თარიღი")

    class Meta:
        verbose_name = "მომხმარებელი"
        verbose_name_plural = "მომხმარებლები"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.username


# --- 2. Category Model ---
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="კატეგორიის სახელი")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="URL Slug")
    description = models.TextField(max_length=500, verbose_name="აღწერა")
    image = models.ImageField(upload_to='categories/images/', null=True, blank=True, verbose_name="ბანერის სურათი")
    is_active = models.BooleanField(default=True, verbose_name="აქტიურია")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="შექმნის თარიღი")

    class Meta:
        verbose_name = "კატეგორია"
        verbose_name_plural = "კატეგორიები"
        ordering = ('name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# --- 3. Product Model ---
class Product(models.Model):
    COLOR_CHOICES = [
        ('WHITE', 'თეთრი'), ('BLACK', 'შავი'), ('BROWN', 'ყავისფერი'),
        ('GREY', 'ნაცრისფერი'), ('BEIGE', 'ბეჟი')
    ]
    MATERIAL_CHOICES = [
        ('WOOD', 'ხე'), ('METAL', 'ლითონი'), ('GLASS', 'მინა'),
        ('LEATHER', 'ტყავი'), ('TEXTILE', 'ტექსტილი'), ('PLASTIC', 'პლასტიკი')
    ]

    name = models.CharField(max_length=200, verbose_name="პროდუქტის სახელი")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="პროდუქტის Slug")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="კატეგორია")
    description = models.TextField(verbose_name="დეტალური აღწერა")

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ფასი")
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="მარაგის რაოდენობა")

    is_available = models.BooleanField(default=True, verbose_name="ხელმისაწვდომობა")
    featured = models.BooleanField(default=False, verbose_name="გამორჩეული პროდუქტი")

    color = models.CharField(max_length=10, choices=COLOR_CHOICES, verbose_name="ფერი")
    material = models.CharField(max_length=10, choices=MATERIAL_CHOICES, verbose_name="მასალა")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "პროდუქტი"
        verbose_name_plural = "პროდუქტები"
        ordering = ('-created_at',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# დამატებითი ფოტოები
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="პროდუქტი")
    image = models.ImageField(upload_to='products/images/', verbose_name="დამატებითი სურათი")
    is_main = models.BooleanField(default=False, verbose_name="მთავარი სურათი")

    class Meta:
        verbose_name = "პროდუქტის სურათი"
        verbose_name_plural = "პროდუქტის სურათები"

    def __str__(self):
        return f"სურათი {self.product.name}-ისთვის"


# --- 4. Cart & CartItem Models ---
class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart', verbose_name="მომხმარებელი")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="განახლების თარიღი")

    class Meta:
        verbose_name = "კალათა"
        verbose_name_plural = "კალათები"

    def get_total_price(self):
        """ჯამური ფასი"""
        return self.items.aggregate(
            total=Sum(F('quantity') * F('product__price'), output_field=DecimalField())
        )['total'] or 0

    def get_total_items(self):
        """კალათაში არსებული CartItem-ების სია"""
        return self.items.all()

    def get_total_items_count(self):
        """კალათაში არსებული პროდუქტების რაოდენობა"""
        return self.items.aggregate(total_count=Sum('quantity'))['total_count'] or 0

    def __str__(self):
        return f"კალათა {self.user.username}-ისთვის"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="კალათა")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="პროდუქტი")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="რაოდენობა")

    class Meta:
        verbose_name = "კალათის ერთეული"
        verbose_name_plural = "კალათის ერთეულები"
        unique_together = ('cart', 'product')

    def get_item_total(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} კალათაში"


# --- 5. Order & OrderItem Models ---
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'დასამუშავებელი'),
        ('PROCESSING', 'მუშავდება'),
        ('SHIPPED', 'გაგზავნილია'),
        ('DELIVERED', 'მიწოდებულია'),
        ('CANCELLED', 'გაუქმებულია'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='orders',
                             verbose_name="მომხმარებელი")
    order_number = models.CharField(max_length=32, unique=True, default=uuid.uuid4().hex[:10].upper(),
                                    verbose_name="შეკვეთის უნიკალური ნომერი")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', verbose_name="სტატუსი")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ჯამური თანხა")

    shipping_address = models.CharField(max_length=255, verbose_name="მიწოდების მისამართი")
    phone = models.CharField(max_length=15, verbose_name="საკონტაქტო ტელეფონი")
    notes = models.TextField(blank=True, null=True, verbose_name="შენიშვნები")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "შეკვეთა"
        verbose_name_plural = "შეკვეთები"
        ordering = ('-created_at',)

    def __str__(self):
        return f"შეკვეთა #{self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="შეკვეთა")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="პროდუქტი")
    quantity = models.IntegerField(verbose_name="რაოდენობა")
    # სტატიკური ფასი შეკვეთის მომენტში
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ფასი ერთეულზე")

    class Meta:
        verbose_name = "შეკვეთის ერთეული"
        verbose_name_plural = "შეკვეთის ერთეულები"

    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} შეკვეთა #{self.order.order_number}-ში"


from django.db import models

# Create your models here.
