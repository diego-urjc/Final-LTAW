from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm

def home(request):
    """
    Vista principal de PocketArena
    """
    context = {
        'title': 'PocketArena - Simulador de Combates',
        'description': 'Bienvenido a PocketArena, el simulador web de combates por turnos'
    }
    return render(request, 'home.html', context)

def register(request):
    """
    Vista de registro de nuevos usuarios
    """
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una sesión activa. Si deseas crear otra cuenta, cierra sesión primero.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido a PocketArena, {user.username}! Tu cuenta ha sido creada exitosamente.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'title': 'Registrarse - PocketArena',
        'form': form
    }
    return render(request, 'registration/register.html', context)

@login_required
def profile(request):
    """
    Vista del perfil de usuario (protegida)
    """
    context = {
        'title': f'Perfil de {request.user.username} - PocketArena',
        'user': request.user
    }
    return render(request, 'users/profile.html', context)
