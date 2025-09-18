from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .utils.jwt_service import decode_token
from .models import User
import jwt

class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                return JsonResponse({"detail": "Invalid token type"}, status=401)

            user = User.objects.filter(id=payload["user_id"], is_active=True).first()
            if not user:
                return JsonResponse({"detail": "User not found or inactive"}, status=401)

            token_version = payload.get("token_version")
            if token_version is None or token_version != user.token_version:
                return JsonResponse({"detail": "Token revoked"}, status=401)

            request.user = user
            request._force_auth_user = user
            return None

        except jwt.ExpiredSignatureError:
            return JsonResponse({"detail": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"detail": "Invalid token"}, status=401)