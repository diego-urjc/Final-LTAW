from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import CustomUserCreationForm, TeamForm
from .models import Team, TeamCreature

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


def team_list(request):
    """
    Vista para listar equipos públicos
    """
    search_query = request.GET.get('search', '')
    
    teams = Team.objects.filter(is_public=True).select_related('user').prefetch_related('creatures')
    
    if search_query:
        teams = teams.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    teams = teams.order_by('-updated_at')
    
    context = {
        'title': 'Equipos Públicos - PocketArena',
        'teams': teams,
        'search_query': search_query
    }
    return render(request, 'teams/team_list.html', context)


def team_detail(request, team_id):
    """
    Vista para ver detalle de un equipo
    """
    team = get_object_or_404(
        Team.objects.select_related('user').prefetch_related('creatures'),
        id=team_id
    )
    
    # Obtener las criaturas del equipo con sus posiciones
    team_creatures = TeamCreature.objects.filter(team=team).select_related('creature').order_by('position')
    
    # Verificar si el usuario es el dueño
    is_owner = request.user.is_authenticated and team.user == request.user
    
    context = {
        'title': f'{team.name} - PocketArena',
        'team': team,
        'team_creatures': team_creatures,
        'is_owner': is_owner
    }
    return render(request, 'teams/team_detail.html', context)


@login_required
def team_create(request):
    """
    Vista para crear un nuevo equipo
    """
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.user = request.user
            team.save()
            messages.success(request, f'¡Equipo "{team.name}" creado exitosamente!')
            return redirect('team_detail', team_id=team.id)
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = TeamForm()
    
    context = {
        'title': 'Crear Equipo - PocketArena',
        'form': form
    }
    return render(request, 'teams/team_form.html', context)


@login_required
def team_update(request, team_id):
    """
    Vista para editar un equipo (solo el dueño)
    """
    team = get_object_or_404(Team, id=team_id)
    
    # Verificar permisos: solo el dueño puede editar
    if team.user != request.user:
        messages.error(request, 'No tienes permiso para editar este equipo.')
        return redirect('team_detail', team_id=team.id)
    
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Equipo "{team.name}" actualizado exitosamente!')
            return redirect('team_detail', team_id=team.id)
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = TeamForm(instance=team)
    
    context = {
        'title': f'Editar {team.name} - PocketArena',
        'form': form,
        'team': team
    }
    return render(request, 'teams/team_form.html', context)


@login_required
def team_delete(request, team_id):
    """
    Vista para eliminar un equipo (solo el dueño)
    """
    team = get_object_or_404(Team, id=team_id)
    
    # Verificar permisos: solo el dueño puede eliminar
    if team.user != request.user:
        messages.error(request, 'No tienes permiso para eliminar este equipo.')
        return redirect('team_detail', team_id=team.id)
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'¡Equipo "{team_name}" eliminado exitosamente!')
        return redirect('my_teams')
    
    context = {
        'title': f'Eliminar {team.name} - PocketArena',
        'team': team
    }
    return render(request, 'teams/team_confirm_delete.html', context)


@login_required
def my_teams(request):
    """
    Vista para listar solo los equipos del usuario actual
    """
    search_query = request.GET.get('search', '')
    
    teams = Team.objects.filter(user=request.user).select_related('user').prefetch_related('creatures')
    
    if search_query:
        teams = teams.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    teams = teams.order_by('-updated_at')
    
    context = {
        'title': 'Mis Equipos - PocketArena',
        'teams': teams,
        'search_query': search_query,
        'is_my_teams': True
    }
    return render(request, 'teams/team_list.html', context)
