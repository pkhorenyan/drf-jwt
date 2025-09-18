from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from rest_framework.exceptions import APIException
from app.utils.permissions import get_rule_for, can_read_list, can_create

from .models import User, Role
from .utils.jwt_service import create_tokens, decode_token
import jwt



class RegisterView(APIView):
    def post(self, request):
        data = request.data
        if data.get("password") != data.get("password_repeat"):
            return Response({"detail": "Passwords do not match"}, status=400)

        if User.objects.filter(email=data["email"]).exists():
            return Response({"detail": "Email already in use"}, status=400)

        # находим роль user
        user_role = Role.objects.filter(name="user").first()
        if not user_role:
            return Response({"detail": "Default user role not found"}, status=500)

        user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            role=user_role,   # назначаем роль
        )
        user.set_password(data["password"])
        user.save()

        return Response({"detail": "User registered"}, status=201)


class LoginView(APIView):
    def post(self, request):
        data = request.data
        user = User.objects.filter(email=data.get("email")).first()  # Убираем is_active из фильтра

        if not user or not user.check_password(data.get("password", "")):
            return Response({"detail": "Invalid credentials"}, status=401)

        # Проверяем, что аккаунт активен
        if not user.is_active:
            return Response({"detail": "Account is deactivated"}, status=status.HTTP_403_FORBIDDEN)

        access, refresh = create_tokens(user.id, user.token_version)

        return Response({"access": access, "refresh": refresh})


class MeView(APIView):
    def get(self, request):
        if not request.user:
            print(request.user)
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        return Response({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.name if user.role else None,
            "is_active": user.is_active,

        })


class UpdateMeView(APIView):
    def put(self, request):
        if not request.user:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        data = request.data

        # Обновляем поля, если они предоставлены
        if 'first_name' in data:
            user.first_name = data['first_name']

        if 'last_name' in data:
            user.last_name = data['last_name']

        if 'password' in data:
            user.set_password(data['password'])

        if 'email' in data:
            new_email = data['email'].lower().strip()
            # Проверяем, что email не занят другим пользователем
            if new_email != user.email and User.objects.filter(email=new_email).exists():
                return Response({"detail": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)
            # Валидация email
            try:
                validate_email(new_email)
                user.email = new_email
            except ValidationError:
                return Response({"detail": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)


        # обновление роли
        if 'role' in data:
            if user.role and user.role.name != "admin":
                return Response({"detail": "Only admin can change roles"}, status=status.HTTP_403_FORBIDDEN)

            new_role = Role.objects.filter(name=data['role']).first()
            if not new_role:
                return Response({"detail": "Role not found"}, status=status.HTTP_400_BAD_REQUEST)

            user.role = new_role

        user.save()

        return Response({
            "detail": "Profile updated successfully",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role.name if user.role else None,
                "is_active": user.is_active,
            }
        })

class AdminUserUpdateView(APIView):
    def put(self, request):

        data = request.data
        user_id = data['id']

        # Проверяем аутентификацию
        if not request.user:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем, что это админ
        if not request.user.role or request.user.role.name != "admin":
            return Response({"detail": "Only admin can update users"}, status=status.HTTP_403_FORBIDDEN)

        # Ищем пользователя
        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        # Админ может менять роль
        if "role" in data:
            new_role = Role.objects.filter(name=data["role"]).first()
            if not new_role:
                return Response({"detail": "Role not found"}, status=status.HTTP_400_BAD_REQUEST)
            target_user.role = new_role

        # Админ может блокировать пользователя
        if "is_active" in data:
            target_user.is_active = bool(data["is_active"])

        target_user.save()

        return Response({
            "detail": "User updated successfully",
            "user": {
                "id": target_user.id,
                "first_name": target_user.first_name,
                "last_name": target_user.last_name,
                "email": target_user.email,
                "role": target_user.role.name if target_user.role else None,
                "is_active": target_user.is_active,
            }
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "Refresh token required"}, status=400)

        try:
            payload = decode_token(token)
            if payload.get("type") != "refresh":
                return Response({"detail": "Invalid token type"}, status=401)

            user = User.objects.filter(id=payload["user_id"]).first()  # Убираем is_active из фильтра
            if not user:
                return Response({"detail": "User not found"}, status=401)

            # Проверяем, что аккаунт активен
            if not user.is_active:
                return Response({"detail": "Account is deactivated"}, status=status.HTTP_403_FORBIDDEN)

            if user.token_version != payload.get("token_version"):
                return Response({"detail": "Token invalidated"}, status=401)

            access, refresh = create_tokens(user.id, user.token_version)
            return Response({"access": access, "refresh": refresh})
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Refresh token expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token"}, status=401)

class LogoutView(APIView):
    def post(self, request):
        if not request.user:
            return Response({"detail": "Not authenticated"}, status=401)

        # инвалидируем refresh токены
        request.user.token_version += 1
        request.user.save(update_fields=["token_version"])

        return Response({"detail": "Logged out"})


class DeleteAccountView(APIView):
    def delete(self, request):
        if not request.user:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user

        # Выполняем мягкое удаление
        user.is_active = False
        user.token_version += 1  # Инвалидируем все токены
        user.save(update_fields=['is_active', 'token_version'])

        return Response({
            "detail": "Account deleted successfully. You have been logged out."
        }, status=status.HTTP_200_OK)

# Пользователи (доступ только у админа)
class UserListView(APIView):
    def get(self, request):
        # Проверка аутентификации
        if not request.user:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверка, что это админ
        if not request.user.role or request.user.role.name != "admin":
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # Возвращаем список пользователей
        users = User.objects.all().values("id", "first_name", "last_name", "email", "role", "is_active")


        return Response(list(users), status=status.HTTP_200_OK)






# --- Mock-данные ---
MOCK_PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 1200},
    {"id": 2, "name": "Phone", "price": 800},
    {"id": 3, "name": "Monitor", "price": 300},
]

# Заказы — имеют owner (id пользователя). owner id = 1 (admin), 2 (manager), 3 (user) — пример
MOCK_ORDERS = [
    {"id": 1, "item": "Laptop", "owner": 3},
    {"id": 2, "item": "Phone", "owner": 2},
    {"id": 3, "item": "Monitor", "owner": 1},
    {"id": 4, "item": "Keyboard", "owner": 3},
]


def _unauthenticated_response():
    return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


# ---------- PRODUCTS ----------
class ProductListView(APIView):
    def get(self, request):
        # Проверка аутентификации
        if not request.user:
            return _unauthenticated_response()

        try:
            allowed_all, allowed_owner_only = can_read_list(request.user, "products")
        except APIException as exc:
            return Response({"detail": exc.detail}, status=getattr(exc, "status_code", 403))

        if allowed_all or allowed_owner_only:
            return Response(MOCK_PRODUCTS, status=status.HTTP_200_OK)

        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


class ProductCreateView(APIView):
    def post(self, request):
        if not request.user:
            return _unauthenticated_response()

        try:
            can_create(request.user, "products")
        except APIException as exc:
            return Response({"detail": exc.detail}, status=getattr(exc, "status_code", 403))

        # mock creation — возвращаем фиктивный объект
        created = {"id": 999, "name": request.data.get("name", "New product")}
        return Response({"detail": "Product created (mock)", "product": created}, status=status.HTTP_201_CREATED)


# ---------- ORDERS ----------
class OrderListView(APIView):
    def get(self, request):
        if not request.user:
            return _unauthenticated_response()

        try:
            allowed_all, allowed_owner_only = can_read_list(request.user, "orders")
        except APIException as exc:
            return Response({"detail": exc.detail}, status=getattr(exc, "status_code", 403))

        if allowed_all:
            return Response(MOCK_ORDERS, status=status.HTTP_200_OK)

        if allowed_owner_only:
            user_id = request.user.id
            filtered = [o for o in MOCK_ORDERS if o.get("owner") == user_id]
            return Response(filtered, status=status.HTTP_200_OK)

        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


class OrderCreateView(APIView):
    def post(self, request):
        if not request.user:
            return _unauthenticated_response()

        try:
            can_create(request.user, "orders")
        except APIException as exc:
            return Response({"detail": exc.detail}, status=getattr(exc, "status_code", 403))

        # mock — создаём заказ с owner = current user
        new_order = {
            "id": 999,
            "item": request.data.get("item", "Unknown"),
            "owner": request.user.id,
        }
        return Response({"detail": "Order created (mock)", "order": new_order}, status=status.HTTP_201_CREATED)