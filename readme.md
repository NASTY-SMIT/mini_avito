1. Архитектура проекта (как всё будет организовано)
Мы используем стандартную DRF-архитектуру, которая идеально подходит для таких проектов:
textmini_avito/                  ← корень репозитория
├── manage.py
├── mini_avito/              ← основное приложение Django (settings, urls)
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py, wsgi.py
│   └── __init__.py
├── apps/                    ← сюда кладём все наши приложения
│   ├── accounts/            ← профиль, регистрация, /api/me/
│   ├── categories/          ← Категории
│   ├── listings/            ← Объявления + Favorite + Offers (основное приложение)
│   └── core/                ← общие утилиты (permissions, pagination)
├── requirements.txt
├── .env                     ← позже (секреты)
└── README.md
Почему так?

accounts — отдельно, потому что вся аутентификация и профиль.
listings — самое большое приложение, там будут ViewSet’ы, actions (offers/, favorite/).
core — для переиспользуемых вещей (CustomPermission, pagination).
DRF любит ViewSet + Router вместо отдельных классов — это сократит код в 2 раза.
Все модели будут в своих apps, но User — встроенный (мы его расширим через accounts).


2. Установка всего необходимого (сразу)
Создай виртуальное окружение (если ещё нет):
Bashpython -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
Установи все пакеты сразу (я выбрал самые популярные и актуальные на 2026 год):
Bashpip install django djangorestframework djangorestframework-simplejwt drf-spectacular django-filter pillow
pip freeze > requirements.txt
Зачем эти пакеты:

djangorestframework-simplejwt — JWT-токены (логин/регистрация)
drf-spectacular — автоматический Swagger (красивая документация)
django-filter — фильтры по category, status, поиск по title
pillow — на будущее (если захочешь добавить фото к объявлению)


3. Инициализация Django-проекта
Bashdjango-admin startproject mini_avito .
python manage.py startapp accounts
python manage.py startapp categories
python manage.py startapp listings
python manage.py startapp core
Перемести accounts, categories, listings, core в папку apps/ (чтобы было красиво).
В mini_avito/settings.py добавь пути:
Pythonimport os
BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    
    # наши приложения
    'apps.accounts',
    'apps.categories',
    'apps.listings',
    'apps.core',
]

4. Базовая настройка settings.py (обязательно!)
Python# REST_FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# SIMPLE_JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# SPECTACULAR (Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Mini-Avito API',
    'DESCRIPTION': 'Мини-Avito с предложениями цены и избранным',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

5. Этап 1 — Аутентификация (самое важное для новичка)
Что делаем:

В apps/accounts/models.py создай UserProfile (OneToOne с User) — туда потом можно добавить аватар, телефон и т.д.
Сериализаторы:
UserSerializer (для /api/me/)
RegisterSerializer (с write_only для пароля)

Views:
RegisterView (APIView или generics.CreateAPIView)
/api/me/ — RetrieveUpdateAPIView с permission_classes = [IsAuthenticated]

URLs:
token/obtain/, token/refresh/ — от simplejwt
api/me/


Ключевые моменты, которые ты изучишь:

write_only=True для password
request.user везде
perform_create для установки user = self.request.user

Коммит: git commit -m "Этап 1: JWT аутентификация + /api/me/"

6. Этап 2 — Объявления (CRUD + права)
Модели:

Category в apps/categories/models.py
Listing в apps/listings/models.py (status: choices ACTIVE, SOLD, ARCHIVED)

ViewSet:

ListingViewSet (ModelViewSet)
get_queryset() — очень важная логика:Pythonif self.request.user.is_authenticated:
    return Listing.objects.filter(
        Q(seller=self.request.user) | Q(status='active')
    )
return Listing.objects.filter(status='active')

Permissions:

Создай в apps/core/permissions.py:Pythonclass IsSellerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.seller == request.user

perform_destroy:
Pythondef perform_destroy(self, instance):
    instance.status = 'archived'
    instance.save()
Два сериализатора:

ListingListSerializer (короткий)
ListingDetailSerializer (полный)
В ViewSet:Pythondef get_serializer_class(self):
    if self.action == 'retrieve':
        return ListingDetailSerializer
    return ListingListSerializer

Оптимизация N+1:
Pythonqueryset = queryset.select_related('seller', 'category').prefetch_related('offers')
Коммит: git commit -m "Этап 2: CRUD объявлений + мягкое удаление"

7. Этап 3 — Предложения цены (@action + транзакция)
В ListingViewSet добавь:
Python@action(detail=True, methods=['post'])
def offers(self, request, pk=None):
    # создание Offer
Отдельный OfferViewSet для PATCH /api/offers/{id}/
Валидация:

В OfferSerializer.validate() проверяй:
нельзя предлагать себе
нельзя на sold/archived


Принятие оффера (самое сложное):
Python@action(detail=True, methods=['patch'])
@transaction.atomic
def accept(self, request, pk=None):
    offer = self.get_object()
    offer.status = 'accepted'
    offer.listing.status = 'sold'
    # все остальные офферы → rejected
    Offer.objects.filter(listing=offer.listing).exclude(id=offer.id).update(status='rejected')
    offer.save()
    offer.listing.save()
Коммит: git commit -m "Этап 3: Предложения цены + атомарная транзакция"

8. Этап 4 — Избранное + фильтры
В ListingViewSet:
Python@action(detail=True, methods=['post', 'delete'])
def favorite(self, request, pk=None):
    # get_or_create + delete
Отдельный эндпоинт /api/me/favorites/ — просто ListingViewSet с фильтром favorite__user=request.user
Фильтры:
В listings/filters.py:
Pythonclass ListingFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(...)
    status = ...
    price = django_filters.NumberFilter(lookup_expr='gte')
В ViewSet:
Pythonfilterset_class = ListingFilter
search_fields = ['title']
ordering_fields = ['price', 'created_at']
Коммит: git commit -m "Этап 4: Избранное + фильтры и поиск"

9. Этап 5 — Финал (Swagger + пагинация + оптимизация)

Добавь в urls.py:Pythonfrom drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
Проверь пагинацию (уже настроена в settings).
Проверь все select_related/prefetch_related — запусти проект и посмотри SQL через django-debug-toolbar (по желанию).

Запуск:
Bashpython manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
Открой http://127.0.0.1:8000/api/docs/ — увидишь красивый Swagger.

Рекомендуемый порядок работы (чтобы не запутаться)

Архитектура + пакеты + settings (сегодня)
Этап 1 (аутентификация) — 1–2 дня
Модели + Category + Listing (Этап 2 начало)
ListingViewSet + права + мягкое удаление
Этап 3 (offers) — самый сложный
Этап 4 (favorite + фильтры)
Этап 5 (два сериализатора + оптимизация + Swagger)


Полезные советы новичку:

Всегда смотри официальную документацию DRF: https://www.django-rest-framework.org/
python manage.py shell — лучший друг для тестирования моделей
После каждого этапа тестируй через Postman или Swagger
Если застряла на каком-то моменте (например, на @action или transaction.atomic) — пиши мне конкретный кусок кода, разберём вместе.