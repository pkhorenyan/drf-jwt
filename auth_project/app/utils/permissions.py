from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError
from app.models import BusinessElement, AccessRoleRule

OWNERABLE = {
    "orders": True,
    "users": True,
    "products": False,  # считаем продукты как глобальные (нет owner)
}


def get_rule_for(user, element_name):
    """
    Возвращает AccessRoleRule для роли пользователя и заданного элемента.
    Бросает NotAuthenticated / PermissionDenied / ValidationError (DRF exceptions).
    """
    if not user or getattr(user, "is_active", False) is False:
        raise NotAuthenticated("Not authenticated")

    if not getattr(user, "role", None):
        raise PermissionDenied("User has no role assigned")

    element = BusinessElement.objects.filter(name=element_name).first()
    if not element:
        raise ValidationError(f"Unknown element: {element_name}")

    rule = AccessRoleRule.objects.filter(role=user.role, element=element).first()
    if not rule:
        # Нет правила — доступ запрещён
        raise PermissionDenied("Forbidden")

    return rule, element


def can_read_list(user, element_name):
    """
    Для операций list (GET /<element>/) — решаем, возвращать все или подмножество.
    Возвращает кортеж (allowed_all: bool, allowed_owner_only: bool)
    - allowed_all == True -> можно видеть ВСЕ объекты
    - allowed_owner_only == True -> можно видеть свои объекты (только для ownerable elements)
    """
    rule, _ = get_rule_for(user, element_name)

    # Если есть глобальное право на чтение всех — всё ясно
    if getattr(rule, "read_all_permission", False):
        return True, False

    # Если есть только право читать "свои" (read_permission)
    if getattr(rule, "read_permission", False):
        # если элемент ownerable -> вернуть флаг owner_only
        if OWNERABLE.get(element_name, False):
            return False, True
        # если элемент без owner — read_permission трактуем как право читать всё
        return True, False

    # нет ни того, ни другого
    raise PermissionDenied("Forbidden")


def can_create(user, element_name):
    rule, _ = get_rule_for(user, element_name)
    if getattr(rule, "create_permission", False):
        return True
    raise PermissionDenied("Forbidden")


def can_update(user, element_name, is_owner=False):
    rule, _ = get_rule_for(user, element_name)
    if getattr(rule, "update_all_permission", False):
        return True
    if is_owner and getattr(rule, "update_permission", False):
        return True
    raise PermissionDenied("Forbidden")


def can_delete(user, element_name, is_owner=False):
    rule, _ = get_rule_for(user, element_name)
    if getattr(rule, "delete_all_permission", False):
        return True
    if is_owner and getattr(rule, "delete_permission", False):
        return True
    raise PermissionDenied("Forbidden")
