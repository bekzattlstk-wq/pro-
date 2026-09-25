# Orders backend

API на Python 3.14 и Django REST Framework.

## Установка

```powershell
git clone https://github.com/bekzattlstk-wq/pro-.git
cd pro-
py -3.14 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Swagger: `http://127.0.0.1:8000/api/docs/`

Получите токен через `POST /api/token/`. Для запросов к API добавляйте заголовок:

```text
Authorization: Token <token>
```

Группы `Managers` и `Installers` создаются автоматически при миграции. Добавляйте пользователей в соответствующую группу через Django Admin.

Разрешённые адреса фронтенда задаются переменной `CORS_ALLOWED_ORIGINS` в файле `.env`.

## Проверка

```powershell
python manage.py check
python manage.py test app
python manage.py spectacular --validate --fail-on-warn
python -m pytest
```

Для production используйте `DEBUG=False`, надёжный `SECRET_KEY`, корректный `ALLOWED_HOSTS` и HTTPS. Включайте `SECURE_HSTS_INCLUDE_SUBDOMAINS` и `SECURE_HSTS_PRELOAD`, только если все поддомены поддерживают HTTPS.
