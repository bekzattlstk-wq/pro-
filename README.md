# PRO Монтаж — пользовательская часть (личный кабинет магазина)

Django-проект сервиса по монтажу дверей. Эта часть — кабинет магазина:
регистрация, заявки, файлы, прайс-лист, уведомления.
Админская часть (её делает второй разработчик) подключается к тем же моделям.

---

## Быстрый запуск

```bash
cd pro_montazh

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt

python manage.py migrate
python manage.py runserver
```

Открыть http://127.0.0.1:8000/

### Готовые аккаунты (база `db.sqlite3` уже с демо-данными)

| Кто | Логин | Пароль |
|---|---|---|
| Магазин «Академия дверей» | `demo` (или `ivan@gmail.com`) | `Montazh2026` |
| Администратор (`/admin/`) | `admin` | `Admin2026!` |

Если нужна чистая база: удалить `db.sqlite3`, выполнить `python manage.py migrate`,
затем `python manage.py seed_demo` — создаст магазин и 9 тестовых заявок.

---

## Что где лежит

```
pro_montazh/
├── core/            настройки и корневые urls
├── users/           модель User (магазин/админ), регистрация, вход, личный кабинет
├── orders/          заявки, файлы заявок, уведомления, сигналы
├── services/        прайс-лист и страница уведомлений
├── templates/       все страницы (base.html + app_base.html с боковым меню)
├── static/          css (Tailwind собран локально) и js
└── media/           файлы, которые загружают магазин и менеджер
```

## Страницы

| Адрес | Что это |
|---|---|
| `/login/`, `/register/` | авторизация и регистрация магазина |
| `/profile/` | личный кабинет: данные магазина, активные заявки |
| `/orders/` | список заявок (`?all=1` — включая завершённые) |
| `/orders/create/` | создание заявки с календарём и загрузкой файлов |
| `/orders/<номер>/` | карточка заявки, файлы, статус |
| `/orders/search/` | поиск по номеру заявки |
| `/services/price/` | прайс-лист + выгрузка в CSV |
| `/services/notifications/` | уведомления по заявкам |
| `/admin/` | Django-админка |

---

## Для админской части (второму разработчику)

Все модели уже зарегистрированы в Django-админке, менять фронт кабинета не нужно.

* `orders.models.Order` — поля `status`, `scheduled_date`, `manager_name`,
  `manager_phone`, `specialist_name`, `specialist_phone`, `manager_comment`.
* `orders.models.OrderFile` — при загрузке файла со стороны сервиса ставить
  `uploaded_by_role = OrderFile.Role.MANAGER`.
* `services.models.PriceItem` — прайс-лист, редактируется прямо в админке.

Уведомления магазину создаются **автоматически** (`orders/signals.py`), когда:
заявка создана, изменён статус, назначена дата монтажа, менеджер прикрепил файл.
Важно: менять статус через `order.save()`, а не через `queryset.update()` —
иначе сигналы не сработают.

---

## Тесты

```bash
cd pro_montazh
python manage.py test
```

16 тестов: регистрация и вход по логину/email, генерация номеров заявок,
валидация дат, запрет доступа к чужим заявкам, загрузка файлов и скачивание
архивом, поиск, прайс-лист, уведомления.

---

## Стили

Tailwind собран локально в `static/css/tailwind.css` — интернет для стилей не нужен.
Если добавите новые классы Tailwind в шаблоны, пересоберите файл:

```bash
cd pro_montazh
npx tailwindcss -c tailwind.config.js -i tailwind-input.css -o static/css/tailwind.css --minify
```

Классы, которые приходят из Python (цвета статусов), перечислены в `safelist`
внутри `tailwind.config.js`.

---

## Перед публикацией на реальном сервере

В `core/settings.py`: поставить `DEBUG = False`, заменить `SECRET_KEY`,
заполнить `ALLOWED_HOSTS`, настроить раздачу `media/` и `static/` через nginx.
