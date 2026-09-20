from django.urls import path
from django.views.generic import RedirectView

from .views import login_view, logout_view, profile_view, register_view

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='profile', permanent=False), name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]
