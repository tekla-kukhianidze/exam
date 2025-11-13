from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CategoryViewSet, ProductViewSet, RegisterView, UserProfileView,
    CartViewSet, OrderViewSet
)
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static


router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Custom Auth URLs
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # JWT Login/Token URLs
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),

    # აქ ვრთავთ shop აპლიკაციის URL-ებს /api/ მისამართზე
    path('api/', include('shop.urls')),

]

# furniture_store/furniture_store/urls.py (პროექტის მთავარი urls.py)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)