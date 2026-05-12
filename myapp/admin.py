from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Creature, Move, CreatureMove, Team, TeamCreature, 
    Battle, BattleTurn
)


@admin.register(Creature)
class CreatureAdmin(admin.ModelAdmin):
    """Administración de Criaturas"""
    
    list_display = [
        'name', 'get_types_display', 'hp', 'attack', 'defense', 
        'speed', 'created_at'
    ]
    list_filter = ['type1', 'type2', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'type1', 'type2', 'description', 'image_url')
        }),
        ('Estadísticas Básicas', {
            'fields': ('hp', 'attack', 'defense', 'speed')
        }),
        ('Estadísticas Especiales', {
            'fields': ('sp_attack', 'sp_defense')
        }),
        ('Información de Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related('moves')


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    """Administración de Movimientos"""
    
    list_display = [
        'name', 'get_type_display', 'category', 'power', 
        'accuracy', 'pp', 'created_at'
    ]
    list_filter = ['type', 'category', 'power', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'type', 'category', 'description')
        }),
        ('Estadísticas de Combate', {
            'fields': ('power', 'accuracy', 'pp')
        }),
        ('Información de Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CreatureMove)
class CreatureMoveAdmin(admin.ModelAdmin):
    """Administración de Movimientos de Criaturas"""
    
    list_display = ['creature', 'move', 'level_learned']
    list_filter = ['level_learned', 'creature__type1', 'move__type']
    search_fields = ['creature__name', 'move__name']
    ordering = ['creature', 'level_learned']
    
    autocomplete_fields = ['creature', 'move']


class TeamCreatureInline(admin.TabularInline):
    """Inline para gestionar criaturas en equipos"""
    
    model = TeamCreature
    extra = 1
    min_num = 1
    max_num = 6
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creature')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Administración de Equipos"""
    
    list_display = ['name', 'user', 'get_creature_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'user']
    search_fields = ['name', 'description', 'user__username']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'user', 'description', 'is_public')
        }),
        ('Información de Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [TeamCreatureInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('creatures')


class BattleTurnInline(admin.TabularInline):
    """Inline para gestionar turnos de combate"""
    
    model = BattleTurn
    extra = 0
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('turn_number')


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    """Administración de Combates"""
    
    list_display = [
        'get_battle_display', 'status', 'current_turn', 
        'winner', 'created_at', 'get_duration'
    ]
    list_filter = ['status', 'winner', 'created_at']
    search_fields = [
        'player1__username', 'player2__username', 
        'team1__name', 'team2__name'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información del Combate', {
            'fields': ('status', 'current_turn', 'winner')
        }),
        ('Jugadores', {
            'fields': ('player1', 'player2')
        }),
        ('Equipos', {
            'fields': ('team1', 'team2')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'finished_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'started_at', 'finished_at']
    
    inlines = [BattleTurnInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'player1', 'player2', 'team1', 'team2'
        )
    
    def get_battle_display(self, obj):
        """Muestra el combate de forma legible"""
        player1 = obj.player1.username if obj.player1 else "Desconocido"
        player2 = obj.player2.username if obj.player2 else "Esperando"
        return f"{player1} vs {player2}"
    get_battle_display.short_description = "Combate"
    
    def get_duration(self, obj):
        """Calcula la duración del combate"""
        if obj.started_at and obj.finished_at:
            duration = obj.finished_at - obj.started_at
            return str(duration).split('.')[0]  # Elimina microsegundos
        elif obj.started_at:
            return "En curso"
        return "No iniciado"
    get_duration.short_description = "Duración"


@admin.register(BattleTurn)
class BattleTurnAdmin(admin.ModelAdmin):
    """Administración de Turnos de Combate"""
    
    list_display = [
        'battle', 'turn_number', 'player1_action', 
        'player2_action', 'damage_dealt_p1', 'damage_dealt_p2', 'created_at'
    ]
    list_filter = ['turn_number', 'created_at', 'battle__status']
    search_fields = [
        'battle__player1__username', 'battle__player2__username',
        'player1_action', 'player2_action', 'turn_result'
    ]
    ordering = ['-battle', '-turn_number']
    
    fieldsets = (
        ('Información del Turno', {
            'fields': ('battle', 'turn_number')
        }),
        ('Acciones Jugador 1', {
            'fields': ('player1_action', 'player1_target')
        }),
        ('Acciones Jugador 2', {
            'fields': ('player2_action', 'player2_target')
        }),
        ('Resultados', {
            'fields': (
                'turn_result', 'damage_dealt_p1', 'damage_dealt_p2',
                'p1_creature_hp', 'p2_creature_hp'
            )
        }),
        ('Información de Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('battle')


# Personalización del admin general
admin.site.site_header = "PocketArena Administración"
admin.site.site_title = "PocketArena"
admin.site.index_title = "Panel de Control de PocketArena"
