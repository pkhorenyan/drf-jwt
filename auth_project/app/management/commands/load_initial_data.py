from django.core.management.base import BaseCommand
from app.models import Role, BusinessElement, AccessRoleRule, User


class Command(BaseCommand):
    help = "Load initial roles, permissions and default admin"

    def handle(self, *args, **kwargs):
        # Создаём роли
        admin_role, _ = Role.objects.get_or_create(name="admin")
        manager_role, _ = Role.objects.get_or_create(name="manager")
        user_role, _ = Role.objects.get_or_create(name="user")

        # Создаём бизнес-объекты
        users, _ = BusinessElement.objects.get_or_create(name="users")
        products, _ = BusinessElement.objects.get_or_create(name="products")
        orders, _ = BusinessElement.objects.get_or_create(name="orders")

        # Админ имеет полный доступ
        for element in [users, products, orders]:
            AccessRoleRule.objects.get_or_create(
                role=admin_role,
                element=element,
                defaults=dict(
                    read_permission=True,
                    read_all_permission=True,
                    create_permission=True,
                    update_permission=True,
                    update_all_permission=True,
                    delete_permission=True,
                    delete_all_permission=True,
                ),
            )

        # Создаём суперпользователя (если его нет)
        if not User.objects.filter(email="admin@email.com").exists():
            admin_user = User(
                first_name="Admin",
                last_name="Admin",
                email="admin@email.com",
                role=admin_role,
            )
            admin_user.set_password("12345")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Default admin user created."))

        self.stdout.write(self.style.SUCCESS("Initial roles and permissions loaded."))

        # Manager: доступ к products и orders (ко всем)
        AccessRoleRule.objects.get_or_create(
            role=manager_role,
            element=products,
            defaults=dict(
                read_permission=True,
                read_all_permission=True,
                create_permission=True,
                update_permission=True,
                update_all_permission=True,
            ),
        )
        AccessRoleRule.objects.get_or_create(
            role=manager_role,
            element=orders,
            defaults=dict(
                read_permission=True,
                read_all_permission=True,
                create_permission=True,
                update_permission=True,
                update_all_permission=True,
            ),
        )

        # User: доступ только к своим заказам
        AccessRoleRule.objects.get_or_create(
            role=user_role,
            element=orders,
            defaults=dict(
                read_permission=True,  # читать свои
                create_permission=True,  # создавать
                update_permission=True,  # обновлять свои
                delete_permission=True,  # удалять свои
            ),
        )

        # User: доступ к просмотру продуктов
        AccessRoleRule.objects.get_or_create(
            role=user_role,
            element=products,
            defaults=dict(
                read_permission=True,
                create_permission=False,
                update_permission=False,
                delete_permission=False,
            ),
        )
