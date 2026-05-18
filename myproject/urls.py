"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from myapp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    
    # Rutas de Equipos (CRUD)
    path("teams/", views.team_list, name="team_list"),
    path("teams/my/", views.my_teams, name="my_teams"),
    path("teams/<int:team_id>/", views.team_detail, name="team_detail"),
    path("teams/create/", views.team_create, name="team_create"),
    path("teams/<int:team_id>/edit/", views.team_update, name="team_update"),
    path("teams/<int:team_id>/delete/", views.team_delete, name="team_delete"),
    path("teams/<int:team_id>/creatures/add/", views.team_add_creature, name="team_add_creature"),
    path("teams/<int:team_id>/creatures/<int:tc_id>/remove/", views.team_remove_creature, name="team_remove_creature"),
    
    # Rutas de Combates
    path("battle/", views.battle_setup, name="battle_setup"),
    path("battle/normal/", views.battle_normal_setup, name="battle_normal_setup"),
    path("battle/random/", views.battle_random_start, name="battle_random_start"),
    path("battle/turn/", views.battle_turn, name="battle_turn"),
    path("battle/result/", views.battle_result, name="battle_result"),

    # Rutas de Pokémon
    path("creatures/", views.creature_list, name="creature_list"),
    
    # Rutas de IA
    path("ai/recommendation/", views.get_ai_recommendation, name="ai_recommendation"),
    path("ai/history/", views.ai_history, name="ai_history"),

    # API REST (JsonResponse, sin DRF)
    path("api/creatures/", views.api_creatures_list, name="api_creatures_list"),
    path("api/creatures/<int:creature_id>/", views.api_creature_detail, name="api_creature_detail"),
    path("api/teams/", views.api_teams_list, name="api_teams_list"),
]
