import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .forms import CustomUserCreationForm, TeamForm
from .models import Team, TeamCreature, Battle, Creature, CreatureMove, AIMessage
from .services.nvidia_service import NVIDIABuildService, NVIDIAServiceError

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
    Muestra estadísticas del usuario usando relaciones Django
    """
    user = request.user
    
    # Equipos creados por el usuario
    teams_count = Team.objects.filter(user=user).count()
    
    # Combates donde el usuario participó (como player1 o player2)
    battles_as_p1 = user.battles_as_player1.all()
    battles_as_p2 = user.battles_as_player2.all()
    battles_count = battles_as_p1.count() + battles_as_p2.count()
    
    # Victorias: ganó como player1 o como player2
    victories = battles_as_p1.filter(winner='player1').count() + \
               battles_as_p2.filter(winner='player2').count()
    
    # Derrotas: perdió como player1 o como player2
    defeats = battles_as_p1.filter(winner='player2').count() + \
             battles_as_p2.filter(winner='player1').count()
    
    context = {
        'title': f'Perfil de {user.username} - PocketArena',
        'user': user,
        'teams_count': teams_count,
        'battles_count': battles_count,
        'victories': victories,
        'defeats': defeats
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


MAX_TEAM_SIZE = 6


@login_required
def team_add_creature(request, team_id):
    """Vista para añadir una criatura a un equipo (solo el dueño)."""
    team = get_object_or_404(Team, id=team_id)

    if team.user != request.user:
        messages.error(request, 'No tienes permiso para modificar este equipo.')
        return redirect('team_detail', team_id=team.id)

    current_members = TeamCreature.objects.filter(team=team).select_related('creature')
    used_positions = set(current_members.values_list('position', flat=True))
    used_creature_ids = set(current_members.values_list('creature_id', flat=True))

    if len(used_positions) >= MAX_TEAM_SIZE:
        messages.warning(request, f'El equipo ya tiene el máximo de {MAX_TEAM_SIZE} criaturas.')
        return redirect('team_detail', team_id=team.id)

    available_creatures = Creature.objects.exclude(id__in=used_creature_ids).order_by('name')
    available_positions = [p for p in range(1, MAX_TEAM_SIZE + 1) if p not in used_positions]

    if request.method == 'POST':
        creature_id = request.POST.get('creature')
        position_raw = request.POST.get('position')

        try:
            position = int(position_raw)
        except (TypeError, ValueError):
            position = None

        if not creature_id or position not in available_positions:
            messages.error(request, 'Selecciona una criatura y una posición válida.')
            return redirect('team_add_creature', team_id=team.id)

        creature = get_object_or_404(Creature, id=creature_id)

        if creature.id in used_creature_ids:
            messages.error(request, 'Esa criatura ya está en el equipo.')
            return redirect('team_add_creature', team_id=team.id)

        TeamCreature.objects.create(team=team, creature=creature, position=position)
        messages.success(
            request,
            f'Se ha añadido "{creature.name}" al equipo en la posición {position}.'
        )
        return redirect('team_detail', team_id=team.id)

    context = {
        'title': f'Añadir criatura a {team.name} - PocketArena',
        'team': team,
        'available_creatures': available_creatures,
        'available_positions': available_positions,
        'current_members': current_members,
    }
    return render(request, 'teams/team_add_creature.html', context)


@login_required
def team_remove_creature(request, team_id, tc_id):
    """Vista para quitar una criatura del equipo (solo el dueño, POST)."""
    team = get_object_or_404(Team, id=team_id)

    if team.user != request.user:
        messages.error(request, 'No tienes permiso para modificar este equipo.')
        return redirect('team_detail', team_id=team.id)

    if request.method != 'POST':
        return redirect('team_detail', team_id=team.id)

    team_creature = get_object_or_404(TeamCreature, id=tc_id, team=team)
    creature_name = team_creature.creature.name
    team_creature.delete()
    messages.success(request, f'Se ha quitado "{creature_name}" del equipo.')
    return redirect('team_detail', team_id=team.id)


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


RANDOM_BATTLE_SIZE = 6


def _build_random_team(size, exclude_ids=None):
    """Devuelve una lista de IDs aleatorios de criaturas."""
    qs = Creature.objects.all()
    if exclude_ids:
        qs = qs.exclude(id__in=exclude_ids)
    pool = list(qs.values_list('id', flat=True))
    random.shuffle(pool)
    return pool[:size]


def _init_battle_session(request, mode, team1_ids, team2_ids):
    """Crea la estructura de combate en la sesión a partir de dos listas de ids."""
    by_id = {c.id: c for c in Creature.objects.filter(id__in=set(team1_ids) | set(team2_ids))}
    hp1 = [by_id[cid].hp for cid in team1_ids if cid in by_id]
    hp2 = [by_id[cid].hp for cid in team2_ids if cid in by_id]
    request.session['battle'] = {
        'mode': mode,
        'team1': list(team1_ids),
        'team2': list(team2_ids),
        'hp1': hp1,
        'hp2': hp2,
        'active1': 0,
        'active2': 0,
        'turn': 1,
        'log': [],
        'finished': False,
        'winner': None,
    }


@login_required
def battle_setup(request):
    """Menú de combate: elegir formato (Normal o Random)."""
    user_teams_count = Team.objects.filter(user=request.user).count()
    creatures_total = Creature.objects.count()
    context = {
        'title': 'Combates - PocketArena',
        'user_teams_count': user_teams_count,
        'creatures_total': creatures_total,
        'random_size': RANDOM_BATTLE_SIZE,
    }
    return render(request, 'battles/battle_menu.html', context)


@login_required
def battle_normal_setup(request):
    """Combate normal: el usuario elige uno de sus equipos."""
    user_teams = (
        Team.objects.filter(user=request.user)
        .annotate(num_creatures=Count('creatures'))
        .filter(num_creatures__gt=0)
        .order_by('-updated_at')
    )

    if request.method == 'POST':
        team_id = request.POST.get('team')
        if not team_id:
            messages.error(request, 'Debes seleccionar un equipo.')
            return redirect('battle_normal_setup')

        team = get_object_or_404(Team, id=team_id, user=request.user)
        team_creatures = (
            TeamCreature.objects.filter(team=team)
            .select_related('creature')
            .order_by('position')
        )
        team1_ids = [tc.creature_id for tc in team_creatures]

        if not team1_ids:
            messages.error(request, 'El equipo seleccionado no tiene criaturas.')
            return redirect('team_detail', team_id=team.id)

        if Creature.objects.count() < len(team1_ids):
            messages.error(request, 'No hay suficientes criaturas en el sistema para generar un rival.')
            return redirect('battle_setup')

        team2_ids = _build_random_team(len(team1_ids))
        _init_battle_session(request, mode='normal', team1_ids=team1_ids, team2_ids=team2_ids)
        messages.success(request, f'¡Combate normal iniciado con el equipo "{team.name}"!')
        return redirect('battle_turn')

    context = {
        'title': 'Combate Normal - PocketArena',
        'user_teams': user_teams,
    }
    return render(request, 'battles/battle_normal_setup.html', context)


@login_required
def battle_random_start(request):
    """Combate random 6v6: genera dos equipos aleatorios y arranca el combate."""
    if Creature.objects.count() < RANDOM_BATTLE_SIZE * 2:
        messages.error(
            request,
            f'Se necesitan al menos {RANDOM_BATTLE_SIZE * 2} criaturas en el sistema para un combate random.'
        )
        return redirect('battle_setup')

    team1_ids = _build_random_team(RANDOM_BATTLE_SIZE)
    team2_ids = _build_random_team(RANDOM_BATTLE_SIZE, exclude_ids=team1_ids)
    _init_battle_session(request, mode='random', team1_ids=team1_ids, team2_ids=team2_ids)
    messages.success(request, f'¡Combate random {RANDOM_BATTLE_SIZE}vs{RANDOM_BATTLE_SIZE} iniciado!')
    return redirect('battle_turn')


def _hp_color(percent):
    if percent > 50:
        return 'bg-success'
    if percent > 25:
        return 'bg-warning'
    return 'bg-danger'


def _team_view(team_ids, hps, active_idx):
    """Devuelve una lista de dicts para representar un equipo en plantilla."""
    by_id = {c.id: c for c in Creature.objects.filter(id__in=team_ids)}
    slots = []
    for idx, cid in enumerate(team_ids):
        creature = by_id.get(cid)
        if not creature:
            continue
        current_hp = hps[idx] if idx < len(hps) else 0
        slots.append({
            'creature': creature,
            'index': idx,
            'hp_current': max(current_hp, 0),
            'hp_max': creature.hp,
            'fainted': current_hp <= 0,
            'is_active': idx == active_idx,
            'percent': max(0, min(100, (current_hp / creature.hp) * 100)) if creature.hp else 0,
        })
    return slots


def _team_finished(hps):
    return all(h <= 0 for h in hps)


@login_required
def battle_turn(request):
    """Procesa cada turno del combate estilo Pokémon (formato team-based)."""
    battle = request.session.get('battle')

    if not battle:
        messages.error(request, 'No hay ningún combate activo.')
        return redirect('battle_setup')

    if battle.get('finished'):
        return redirect('battle_result')

    if _team_finished(battle['hp1']) or _team_finished(battle['hp2']):
        battle['finished'] = True
        battle['winner'] = 2 if _team_finished(battle['hp1']) else 1
        request.session['battle'] = battle
        return redirect('battle_result')

    creature1 = get_object_or_404(Creature, id=battle['team1'][battle['active1']])
    creature2 = get_object_or_404(Creature, id=battle['team2'][battle['active2']])

    player_moves = (
        CreatureMove.objects.filter(creature=creature1)
        .select_related('move')
        .order_by('level_learned')
    )
    ai_moves = (
        CreatureMove.objects.filter(creature=creature2)
        .select_related('move')
        .order_by('level_learned')
    )

    if request.method == 'POST':
        move_id = request.POST.get('move')
        if not move_id:
            messages.error(request, 'Debes seleccionar un movimiento.')
            return redirect('battle_turn')

        player_cm = get_object_or_404(player_moves, move_id=move_id)
        player_move_obj = player_cm.move

        ai_cm = random.choice(list(ai_moves)) if ai_moves.exists() else None
        ai_move_obj = ai_cm.move if ai_cm else None

        if creature1.speed > creature2.speed:
            order = [1, 2]
        elif creature2.speed > creature1.speed:
            order = [2, 1]
        else:
            order = random.choice([[1, 2], [2, 1]])

        attacks = []
        for attacker in order:
            if attacker == 1:
                if battle['hp1'][battle['active1']] <= 0:
                    continue
                dmg = player_move_obj.power if player_move_obj.power else 20
                battle['hp2'][battle['active2']] -= dmg
                battle['log'].append({
                    'turn': battle['turn'],
                    'player': 1,
                    'creature': creature1.name,
                    'move': player_move_obj.name,
                    'damage': dmg,
                    'target': creature2.name,
                    'target_hp': max(battle['hp2'][battle['active2']], 0),
                })
                attacks.append(f'{creature1.name} usó {player_move_obj.name} y causó {dmg} de daño.')
            else:
                if not ai_move_obj or battle['hp2'][battle['active2']] <= 0:
                    continue
                dmg = ai_move_obj.power if ai_move_obj.power else 20
                battle['hp1'][battle['active1']] -= dmg
                battle['log'].append({
                    'turn': battle['turn'],
                    'player': 2,
                    'creature': creature2.name,
                    'move': ai_move_obj.name,
                    'damage': dmg,
                    'target': creature1.name,
                    'target_hp': max(battle['hp1'][battle['active1']], 0),
                })
                attacks.append(f'{creature2.name} (IA) usó {ai_move_obj.name} y causó {dmg} de daño.')

        # Relevos automáticos al final del turno
        if battle['hp1'][battle['active1']] <= 0:
            attacks.append(f'¡{creature1.name} ha caído!')
            next_idx = next(
                (i for i, hp in enumerate(battle['hp1']) if hp > 0 and i > battle['active1']),
                None,
            )
            if next_idx is None:
                next_idx = next((i for i, hp in enumerate(battle['hp1']) if hp > 0), None)
            if next_idx is not None:
                battle['active1'] = next_idx
                next_creature = Creature.objects.get(id=battle['team1'][next_idx])
                attacks.append(f'¡Adelante, {next_creature.name}!')

        if battle['hp2'][battle['active2']] <= 0:
            attacks.append(f'¡{creature2.name} (IA) ha caído!')
            next_idx = next(
                (i for i, hp in enumerate(battle['hp2']) if hp > 0 and i > battle['active2']),
                None,
            )
            if next_idx is None:
                next_idx = next((i for i, hp in enumerate(battle['hp2']) if hp > 0), None)
            if next_idx is not None:
                battle['active2'] = next_idx
                next_creature = Creature.objects.get(id=battle['team2'][next_idx])
                attacks.append(f'El rival envía a {next_creature.name}.')

        battle['turn'] += 1

        if _team_finished(battle['hp1']) or _team_finished(battle['hp2']):
            battle['finished'] = True
            battle['winner'] = 2 if _team_finished(battle['hp1']) else 1
            request.session['battle'] = battle
            for msg in attacks:
                messages.info(request, msg)
            return redirect('battle_result')

        request.session['battle'] = battle
        for msg in attacks:
            messages.info(request, msg)
        return redirect('battle_turn')

    hp1_current = battle['hp1'][battle['active1']]
    hp2_current = battle['hp2'][battle['active2']]
    hp1_percent = (hp1_current / creature1.hp) * 100 if creature1.hp else 0
    hp2_percent = (hp2_current / creature2.hp) * 100 if creature2.hp else 0

    context = {
        'title': 'Combate en Curso - PocketArena',
        'mode': battle.get('mode'),
        'turn': battle['turn'],
        'log': battle['log'][-15:],
        'creature1': creature1,
        'creature2': creature2,
        'creature1_hp': max(hp1_current, 0),
        'creature2_hp': max(hp2_current, 0),
        'hp1_percent': hp1_percent,
        'hp2_percent': hp2_percent,
        'hp1_color': _hp_color(hp1_percent),
        'hp2_color': _hp_color(hp2_percent),
        'creature_moves': player_moves,
        'team1_slots': _team_view(battle['team1'], battle['hp1'], battle['active1']),
        'team2_slots': _team_view(battle['team2'], battle['hp2'], battle['active2']),
    }
    return render(request, 'battles/battle_arena.html', context)


@login_required
def battle_result(request):
    """Resultado final del combate (formato team-based)."""
    battle = request.session.get('battle')

    if not battle:
        messages.error(request, 'No hay ningún combate activo.')
        return redirect('battle_setup')

    winner = battle.get('winner')
    if winner is None:
        if _team_finished(battle['hp1']) and not _team_finished(battle['hp2']):
            winner = 2
        elif _team_finished(battle['hp2']) and not _team_finished(battle['hp1']):
            winner = 1
        else:
            winner = 0

    winner_name = (
        'Tu equipo' if winner == 1 else ('El rival' if winner == 2 else 'Nadie')
    )

    team1_slots = _team_view(battle['team1'], battle['hp1'], battle['active1'])
    team2_slots = _team_view(battle['team2'], battle['hp2'], battle['active2'])

    context = {
        'title': 'Resultado del Combate - PocketArena',
        'mode': battle.get('mode'),
        'winner': winner,
        'winner_name': winner_name,
        'log': battle['log'],
        'total_turns': battle['turn'],
        'team1_slots': team1_slots,
        'team2_slots': team2_slots,
        'survivors_1': sum(1 for s in team1_slots if not s['fainted']),
        'survivors_2': sum(1 for s in team2_slots if not s['fainted']),
    }

    if 'battle' in request.session:
        del request.session['battle']

    return render(request, 'battles/battle_result.html', context)


@login_required
def creature_list(request):
    """Lista todas las criaturas con nombre y descripción."""
    creatures = Creature.objects.all().order_by('name')
    context = {
        'title': 'Criaturas - PocketArena',
        'creatures': creatures,
        'total': creatures.count(),
    }
    return render(request, 'creatures/creature_list.html', context)


@login_required
def get_ai_recommendation(request):
    """
    Vista para obtener recomendaciones estratégicas de la IA
    """
    nvidia_service = NVIDIABuildService()

    if not nvidia_service.is_configured():
        messages.error(
            request,
            'La API de NVIDIA Build no está configurada. Define NVIDIA_API_KEY en el archivo .env.'
        )
        return redirect('home')

    if request.method == 'POST':
        context_type = request.POST.get('context', 'battle')

        try:
            
            if context_type == 'battle':
                # Recomendación para combate específico
                creature1_id = request.POST.get('creature1')
                creature2_id = request.POST.get('creature2')
                
                if not creature1_id or not creature2_id:
                    messages.error(request, 'Debes seleccionar dos criaturas para obtener recomendación.')
                    return redirect('battle_setup')
                
                creature1 = get_object_or_404(Creature, id=creature1_id)
                creature2 = get_object_or_404(Creature, id=creature2_id)
                
                # Obtener movimientos de cada criatura
                creature1_moves = list(CreatureMove.objects.filter(
                    creature=creature1
                ).select_related('move').values_list('move__name', flat=True))
                
                creature2_moves = list(CreatureMove.objects.filter(
                    creature=creature2
                ).select_related('move').values_list('move__name', flat=True))
                
                # Preparar datos para la IA
                player_creature = {
                    'name': creature1.name,
                    'type': creature1.get_types_display(),
                    'hp': creature1.hp,
                    'attack': creature1.attack,
                    'defense': creature1.defense,
                    'speed': creature1.speed,
                    'moves': creature1_moves if creature1_moves else ['Sin movimientos']
                }
                
                enemy_creature = {
                    'name': creature2.name,
                    'type': creature2.get_types_display(),
                    'hp': creature2.hp,
                    'attack': creature2.attack,
                    'defense': creature2.defense,
                    'speed': creature2.speed,
                    'moves': creature2_moves if creature2_moves else ['Sin movimientos']
                }
                
                # Obtener recomendación
                recommendation = nvidia_service.get_battle_recommendation(
                    player_creature, enemy_creature
                )
                
                if recommendation:
                    # Guardar en base de datos
                    AIMessage.objects.create(
                        user=request.user,
                        context='battle',
                        input_data={
                            'player_creature': player_creature,
                            'enemy_creature': enemy_creature
                        },
                        recommendation=recommendation,
                        creature=creature1
                    )
                    
                    messages.success(request, '¡Recomendación obtenida exitosamente!')
                    return render(request, 'ai/recommendation.html', {
                        'title': 'Recomendación de IA - PocketArena',
                        'recommendation': recommendation,
                        'creature1': creature1,
                        'creature2': creature2
                    })
                else:
                    messages.error(request, 'No se pudo obtener la recomendación. Inténtalo más tarde.')
                    return redirect('battle_setup')
                    
            elif context_type == 'team':
                # Recomendación para equipo completo
                team_id = request.POST.get('team')
                
                if not team_id:
                    messages.error(request, 'Debes seleccionar un equipo.')
                    return redirect('my_teams')
                
                team = get_object_or_404(Team, id=team_id, user=request.user)
                
                # Obtener criaturas del equipo
                team_creatures = TeamCreature.objects.filter(
                    team=team
                ).select_related('creature').prefetch_related('creature__moves')
                
                creature_data = []
                for tc in team_creatures:
                    c = tc.creature
                    moves = list(CreatureMove.objects.filter(
                        creature=c
                    ).select_related('move').values_list('move__name', flat=True))
                    
                    creature_data.append({
                        'name': c.name,
                        'type': c.get_types_display(),
                        'hp': c.hp,
                        'attack': c.attack,
                        'defense': c.defense,
                        'speed': c.speed,
                        'sp_attack': c.sp_attack,
                        'sp_defense': c.sp_defense,
                        'moves': moves if moves else ['Sin movimientos']
                    })
                
                # Obtener recomendación
                recommendation = nvidia_service.get_team_recommendations(creature_data)
                
                if recommendation:
                    # Guardar en base de datos
                    AIMessage.objects.create(
                        user=request.user,
                        context='team',
                        input_data={'creatures': creature_data},
                        recommendation=recommendation,
                        team=team
                    )
                    
                    messages.success(request, '¡Análisis de equipo obtenido exitosamente!')
                    return render(request, 'ai/recommendation.html', {
                        'title': 'Análisis de Equipo - PocketArena',
                        'recommendation': recommendation,
                        'team': team
                    })
                else:
                    messages.error(request, 'No se pudo obtener el análisis. Inténtalo más tarde.')
                    return redirect('my_teams')
                    
        except NVIDIAServiceError as e:
            messages.error(request, f'Error de configuración de IA: {e}')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Error al obtener recomendación: {str(e)}')
            return redirect('home')

    # Si es GET, mostrar formulario
    preselected_team_id = request.GET.get('team')
    preselected_context = 'team' if preselected_team_id else request.GET.get('context', 'battle')
    context = {
        'title': 'Obtener Recomendación IA - PocketArena',
        'user_teams': Team.objects.filter(user=request.user),
        'creatures': Creature.objects.all(),
        'preselected_team_id': preselected_team_id,
        'preselected_context': preselected_context,
    }
    return render(request, 'ai/recommendation_form.html', context)


@login_required
def ai_history(request):
    """Lista el historial de recomendaciones de IA del usuario."""
    history = (
        AIMessage.objects
        .filter(user=request.user)
        .select_related('team', 'creature')
        .order_by('-created_at')
    )
    context = {
        'title': 'Historial de IA - PocketArena',
        'history': history,
    }
    return render(request, 'ai/history.html', context)
