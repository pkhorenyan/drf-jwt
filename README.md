Это backend-приложение на Django REST Framework, реализующее собственную систему аутентификации и авторизации пользователей без использования стандартных решений «из коробки».

Написана кастомная JWT Middleware для проверки access-токенов.
Реализован механизм refresh-токенов с отзывом через token_version.
Настроена ролевая модель (admin, manager, user) с хранением правил доступа в базе данных.
Доступ к бизнес-объектам (products, orders, users) регулируется через систему прав.

## Технологии

* Django + Django REST Framework
* PostgreSQL
* JWT (pyjwt)
* Docker + docker-compose

## Функционал

* Регистрация, логин, логаут, обновление и удаление аккаунта (мягкое удаление).
* Аутентификация по JWT (access/refresh токены).
* Роли пользователей (admin, manager, user).
* Mock-объекты для демонстрации (products, orders, users).
* Система разграничения прав доступа:
  * admin может управлять пользователями и видеть всё;
  * manager может работать с продуктами и заказами;
  * user может просматривать и создавать заказы, а также просматривать продукты.

## Установка

```bash
git clone https://github.com/pkhorenyan/drf-jwt.git
cd drf-jwt
```
## Запуск
```bash
docker compose up --build
```
Команда запустит докер контейнер, поднимет базу данных, установит зависимости и загрузит тестовые данные.

Будет создан юзер admin с правами администратора.
* email: admin@email.com
* password: 12345


## API эндпоинты

Аутентификация

* POST `/auth/register/` – регистрация
* POST `/auth/login/` – вход
* POST `/auth/logout/` – выход
* POST `/auth/refresh/` – обновление access-токена
* GET `/auth/me/` – профиль текущего пользователя
* PUT `/auth/updateme/` – обновление своего профиля
* DELETE `/auth/delete-account/` – мягкое удаление аккаунта

Управление пользователями (только админ)

* GET `/users/` – список пользователей
* PUT `/auth/admin/updateuser/` – обновление пользователя (роль, статус и т.п.)

Mock бизнес-объекты

* GET `/products/` – просмотр продуктов
* POST `/products/create/` – создать продукт
* GET `/orders/` – список заказов
* POST `/orders/create/` – создать заказ

## Тестирование

### Примеры Postman запросов

Все запросы идут к http://localhost:8000/.<br>

#### Регистрация пользователя

POST `/auth/register/`

```json lines
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "johnsmith@email.com",
  "password": "12345",
  "password_repeat": "12345"
}
```

#### Логин пользователя

POST `/auth/login/`

```json lines
{
  "email": "johnsmith@email.com",
  "password": "12345"
}
```
Ответ:

```json lines
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
Это Access и Refresh токены соответственно.

#### Обновление токена

POST `/auth/refresh/`

```json lines
{
  "refresh": "<REFRESH_TOKEN>"
}

```

#### Обновить пользователя (только админ)

PUT `/auth/admin/updateuser/`

```json lines
{
  "id": 2,
  "role": "manager"
}
```
<br>
<br>
В запросах, где требуется авторизация, добавляйте заголовок:

```
Authorization: Bearer <ACCESS_TOKEN>
```

#### Получить профиль текущего пользователя

GET `/auth/me/`

#### Логаут

POST `/auth/logout/`

### Бизнес-объекты (Mock API)

#### Продукты

GET `/products/` – просмотр списка продуктов<br>
POST `/products/create/` – создать продукт (доступно admin, manager)

#### Заказы

GET `/orders/` – список заказов<br>
POST `/orders/create/` – создать заказ (admin, manager, user)

