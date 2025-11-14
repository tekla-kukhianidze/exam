from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser


class IsOwnerOrAdmin(BasePermission):
    """
    ობიექტის დონის ნებართვა:
    ნებადართულია წაკითხვა (GET, HEAD, OPTIONS) ყველასთვის (თუ ავტორიზებულია).
    ნებადართულია რედაქტირება (PUT/PATCH/DELETE) მხოლოდ ობიექტის მფლობელისთვის ან ადმინისტრატორისთვის.
    """
    message = "თქვენ არ გაქვთ ამ ოპერაციის შესრულების ნებართვა."  # მორგებული შეტყობინება

    def has_object_permission(self, request, view, obj):
        # 1. ნებადართულია მხოლოდ წაკითხვის (GET, HEAD, OPTIONS) ოპერაციები
        # (მაგრამ მომხმარებელი მაინც IsAuthenticated უნდა იყოს OrderViewSet-ში)
        if request.method in SAFE_METHODS:
            return True

        # 2. ნებადართულია, თუ მომხმარებელი არის ადმინი (პრიორიტეტი)
        if request.user.is_staff:
            return True

        # 3. ნებადართულია, თუ მომხმარებელი არის ობიექტის მფლობელი
        return obj.user == request.user

    __all__ = [
        'AllowAny',
        'IsAuthenticated',
        'IsAdminUser',
        'IsOwnerOrAdmin',
    ]