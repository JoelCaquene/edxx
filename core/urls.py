from django.urls import path, include, reverse_lazy
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from . import views
from .views import MyPasswordChangeView

urlpatterns = [
    # Redirecionamento para a página de login
    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=False)),
    
    # Rota principal que verifica o status de autenticação
    path('', views.home, name='home'),
    
    path('menu/', views.menu, name='menu'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('deposito/', views.deposito, name='deposito'),
    path('saque/', views.saque, name='saque'),
    path('tarefa/', views.tarefa, name='tarefa'),
    path('process_task/', views.process_task, name='process_task'),
    path('nivel/', views.nivel, name='nivel'),
    path('equipa/', views.equipa, name='equipa'),
    path('sorteio/', views.sorteio_view, name='sorteio'),
    path('validar-sorteio/', views.validar_codigo_sorteio, name='validar_codigo_sorteio'),
    path('sobre/', views.sobre, name='sobre'),
    path('perfil/', views.perfil, name='perfil'),
    path('renda/', views.renda, name='renda'),

    # No seu core/urls.py
    path('sorteio/', views.sorteio_view, name='roleta'), # Adicione o name='roleta' aqui
    
   # URLs para alteração de senha CORRIGIDAS
path('change_password/', MyPasswordChangeView.as_view(), name='change_password'),

    path('change_password_done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='change_password_done'),
]
