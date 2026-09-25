# Backend API

Это только Django backend. Фронтенд разрабатывается отдельно.

## Запуск

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Панель администратора: `http://127.0.0.1:8000/admin/`
Swagger: `http://127.0.0.1:8000/api/docs/`
Схема OpenAPI: `http://127.0.0.1:8000/api/schema/`

## Вход

Отправьте `{"username":"...","password":"..."}` на `POST /api/token/`. Передавайте полученный токен в последующих запросах в заголовке `Authorization: Token <token>`. `POST /api/logout/` удаляет токен. После смены пароля прежний токен также становится недействительным.

Обычный пользователь создаёт заявку через `/api/orders/`. Сервер заполняет поле `created_by` по токену пользователя. Когда пользователь добавляет файл к своей заявке, автоматически устанавливается `source=shop`.

## API

| Адрес | Метод | Доступ |
| --- | --- | --- |
| `/api/me/` | GET, PATCH | Авторизованный пользователь: свой профиль |
| `/api/me/password/` | POST | Смена своего пароля |
| `/api/orders/` | GET | Менеджер: свои заявки; администратор: все заявки |
| `/api/orders/` | POST | Авторизованный пользователь |
| `/api/orders/{id}/` | GET | Своя заявка или доступ администратора |
| `/api/orders/{id}/` | PATCH, PUT, DELETE | Только администратор |
| `/api/order-files/` | POST multipart | Администратор или создатель заявки |
| `/api/order-files/{id}/download/` | GET | Участник заявки или администратор |
| `/api/notifications/` | GET | Свои уведомления |
| `/api/notifications/{id}/mark-read/` | POST | Своё уведомление |

## API администратора

Для учётной записи администратора требуется `is_staff=True`.

| Адрес | Метод | Назначение |
| --- | --- | --- |
| `/api/admin/dashboard/` | GET | Количество заявок по статусам и последние заявки |
| `/api/admin/orders/` | GET | Все заявки |
| `/api/admin/orders/{id}/` | GET, PATCH, DELETE | Управление заявкой |
| `/api/admin/orders/{id}/comment/` | POST | Добавление комментария |
| `/api/admin/orders/{id}/history/` | GET | История статусов |
| `/api/admin/employees/?role=manager` | GET | Менеджеры |
| `/api/admin/employees/?role=installer` | GET | Монтажники |

Добавляйте сотрудников в группы `Managers` и `Installers` через Django Admin.

Списки содержат `count`, `next`, `previous`, `results`. `GET /api/orders/?status=waiting_call` фильтрует заявки по статусу, а `?search=АД00000001` ищет по номеру или данным клиента. Статусы: `new`, `waiting_call`, `waiting_service`, `in_progress`, `paused`, `completed`, `cancelled`. Номер заявки формируется сервером автоматически.

Администратор создаёт менеджера через `/admin/auth/user/add/`: для обычного менеджера `is_staff` остаётся выключенным. Для входа в панель администратора требуется `is_staff`. Новую заявку можно создать через панель администратора или API администратора и назначить менеджеру.

Файлы недоступны через общий URL `media/`. API проверяет токен при скачивании; в панели администратора есть отдельная защищённая ссылка «Скачать файл».

## Проверка

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test app
.\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn
.\.venv\Scripts\python.exe -m pytest
```
