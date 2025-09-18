from django.db import models
import bcrypt

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)  # admin, manager, user

class User(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    token_version = models.IntegerField(default=0)  # для logout всех refresh токенов
    created_at = models.DateTimeField(auto_now_add=True)

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def set_password(self, raw_password: str):
        self.password_hash = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode(), self.password_hash.encode())


class BusinessElement(models.Model):
    name = models.CharField(max_length=100, unique=True)  # users, products, orders, permissions

class AccessRoleRule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE)

    # Права
    read_permission = models.BooleanField(default=False)          # читать только свои
    read_all_permission = models.BooleanField(default=False)      # читать все
    create_permission = models.BooleanField(default=False)
    update_permission = models.BooleanField(default=False)        # обновлять только свои
    update_all_permission = models.BooleanField(default=False)    # обновлять все
    delete_permission = models.BooleanField(default=False)        # удалять только свои
    delete_all_permission = models.BooleanField(default=False)    # удалять все

    class Meta:
        unique_together = ("role", "element")
