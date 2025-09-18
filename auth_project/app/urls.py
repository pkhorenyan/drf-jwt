from django.urls import path
from .views import RegisterView, LoginView, LogoutView, RefreshTokenView, MeView, UpdateMeView, DeleteAccountView, \
    AdminUserUpdateView, ProductListView, ProductCreateView, OrderListView, UserListView, OrderCreateView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/refresh/", RefreshTokenView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/updateme/", UpdateMeView.as_view()),
    path('auth/delete-account/', DeleteAccountView.as_view()),
    path("auth/admin/updateuser/", AdminUserUpdateView.as_view()),

    path("products/", ProductListView.as_view()),
    path("products/create/", ProductCreateView.as_view()),
    path("orders/", OrderListView.as_view()),
    path("orders/create/", OrderCreateView.as_view()),

    path("users/", UserListView.as_view()),
]
