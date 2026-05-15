from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Creature(models.Model):
    """Criatura con estadísticas básicas para combate"""
    
    # Tipos elementales (similar a Pokémon)
    TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('fire', 'Fuego'),
        ('water', 'Agua'),
        ('electric', 'Eléctrico'),
        ('grass', 'Planta'),
        ('ice', 'Hielo'),
        ('fighting', 'Lucha'),
        ('poison', 'Veneno'),
        ('ground', 'Tierra'),
        ('flying', 'Volador'),
        ('psychic', 'Psíquico'),
        ('bug', 'Bicho'),
        ('rock', 'Roca'),
        ('ghost', 'Fantasma'),
        ('dragon', 'Dragón'),
        ('dark', 'Siniestro'),
        ('steel', 'Acero'),
        ('fairy', 'Hada'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    type1 = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Tipo Principal")
    type2 = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, null=True, verbose_name="Tipo Secundario")
    
    # Estadísticas básicas (máximo 255 como en Pokémon)
    hp = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        verbose_name="Puntos de Salud"
    )
    attack = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        verbose_name="Ataque"
    )
    defense = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        verbose_name="Defensa"
    )
    speed = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        verbose_name="Velocidad"
    )
    
    # Estadísticas especiales
    sp_attack = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        default=50,
        verbose_name="Ataque Especial"
    )
    sp_defense = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        default=50,
        verbose_name="Defensa Especial"
    )
    
    description = models.TextField(blank=True, verbose_name="Descripción")
    image_url = models.URLField(blank=True, verbose_name="URL de Imagen")
    
    # Movimientos que puede aprender (Muchos a Muchos)
    moves = models.ManyToManyField('Move', through='CreatureMove', verbose_name="Movimientos")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")
    
    class Meta:
        verbose_name = "Criatura"
        verbose_name_plural = "Criaturas"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_types_display(self):
        """Retorna los tipos formateados para mostrar"""
        if self.type2:
            return f"{self.get_type1_display()} / {self.get_type2_display()}"
        return self.get_type1_display()


class Move(models.Model):
    """Movimiento de ataque con estadísticas de combate"""
    
    # Tipos (mismos que Creature)
    TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('fire', 'Fuego'),
        ('water', 'Agua'),
        ('electric', 'Eléctrico'),
        ('grass', 'Planta'),
        ('ice', 'Hielo'),
        ('fighting', 'Lucha'),
        ('poison', 'Veneno'),
        ('ground', 'Tierra'),
        ('flying', 'Volador'),
        ('psychic', 'Psíquico'),
        ('bug', 'Bicho'),
        ('rock', 'Roca'),
        ('ghost', 'Fantasma'),
        ('dragon', 'Dragón'),
        ('dark', 'Siniestro'),
        ('steel', 'Acero'),
        ('fairy', 'Hada'),
    ]
    
    # Categoría del movimiento
    CATEGORY_CHOICES = [
        ('physical', 'Físico'),
        ('special', 'Especial'),
        ('status', 'Estado'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Tipo")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, verbose_name="Categoría")
    
    # Estadísticas del movimiento
    power = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MaxValueValidator(255)],
        verbose_name="Poder (daño)"
    )
    accuracy = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Precisión (%)"
    )
    pp = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(40)],
        verbose_name="PP (Usos)"
    )
    
    description = models.TextField(verbose_name="Descripción")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")
    
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CreatureMove(models.Model):
    """Modelo intermedio para relación Creature-Move con niveles"""
    
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE, verbose_name="Criatura")
    move = models.ForeignKey(Move, on_delete=models.CASCADE, verbose_name="Movimiento")
    level_learned = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Nivel que aprende"
    )
    
    class Meta:
        verbose_name = "Movimiento de Criatura"
        verbose_name_plural = "Movimientos de Criaturas"
        unique_together = ['creature', 'move']
        ordering = ['level_learned', 'move__name']
    
    def __str__(self):
        return f"{self.creature.name} aprende {self.move.name} al nivel {self.level_learned}"


class Team(models.Model):
    """Equipo de criaturas de un usuario"""
    
    name = models.CharField(max_length=100, verbose_name="Nombre del Equipo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Entrenador")
    
    # Criaturas en el equipo (Muchos a Muchos)
    creatures = models.ManyToManyField(
        Creature, 
        through='TeamCreature',
        verbose_name="Criaturas"
    )
    
    is_public = models.BooleanField(default=False, verbose_name="Público")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")
    
    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def get_creature_count(self):
        """Retorna el número de criaturas en el equipo"""
        return self.creatures.count()


class TeamCreature(models.Model):
    """Modelo intermedio para relación Team-Creature con posición"""
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Equipo")
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE, verbose_name="Criatura")
    position = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name="Posición en el equipo"
    )
    
    class Meta:
        verbose_name = "Criatura en Equipo"
        verbose_name_plural = "Criaturas en Equipos"
        unique_together = ['team', 'position']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.team.name} - Pos {self.position}: {self.creature.name}"


class Battle(models.Model):
    """Registro de un combate entre dos usuarios"""
    
    STATUS_CHOICES = [
        ('waiting', 'Esperando Oponente'),
        ('active', 'En Combate'),
        ('finished', 'Finalizado'),
        ('abandoned', 'Abandonado'),
    ]
    
    WINNER_CHOICES = [
        ('player1', 'Jugador 1'),
        ('player2', 'Jugador 2'),
        ('draw', 'Empate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Jugadores
    player1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='battles_as_player1',
        verbose_name="Jugador 1"
    )
    player2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='battles_as_player2',
        null=True, blank=True,
        verbose_name="Jugador 2"
    )
    
    # Equipos utilizados
    team1 = models.ForeignKey(
        Team, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='battles_as_team1',
        verbose_name="Equipo Jugador 1"
    )
    team2 = models.ForeignKey(
        Team, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='battles_as_team2',
        verbose_name="Equipo Jugador 2"
    )
    
    # Estado del combate
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name="Estado")
    current_turn = models.PositiveIntegerField(default=1, verbose_name="Turno Actual")
    winner = models.CharField(max_length=10, choices=WINNER_CHOICES, null=True, blank=True, verbose_name="Ganador")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Iniciado")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Finalizado")
    
    class Meta:
        verbose_name = "Combate"
        verbose_name_plural = "Combates"
        ordering = ['-created_at']
    
    def __str__(self):
        player1_name = self.player1.username if self.player1 else "Desconocido"
        player2_name = self.player2.username if self.player2 else "Esperando"
        return f"Combate: {player1_name} vs {player2_name}"


class BattleTurn(models.Model):
    """Registro de cada turno en un combate"""
    
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, verbose_name="Combate")
    turn_number = models.PositiveIntegerField(verbose_name="Número de Turno")
    
    # Acciones de cada jugador
    player1_action = models.CharField(max_length=200, verbose_name="Acción Jugador 1")
    player1_target = models.CharField(max_length=100, blank=True, verbose_name="Objetivo Jugador 1")
    
    player2_action = models.CharField(max_length=200, blank=True, verbose_name="Acción Jugador 2")
    player2_target = models.CharField(max_length=100, blank=True, verbose_name="Objetivo Jugador 2")
    
    # Resultados del turno
    turn_result = models.TextField(verbose_name="Resultado del Turno")
    damage_dealt_p1 = models.PositiveIntegerField(null=True, blank=True, verbose_name="Daño Causado por P1")
    damage_dealt_p2 = models.PositiveIntegerField(null=True, blank=True, verbose_name="Daño Causado por P2")
    
    # Estado de las criaturas después del turno
    p1_creature_hp = models.PositiveIntegerField(null=True, blank=True, verbose_name="HP Criatura P1")
    p2_creature_hp = models.PositiveIntegerField(null=True, blank=True, verbose_name="HP Criatura P2")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    
    class Meta:
        verbose_name = "Turno de Combate"
        verbose_name_plural = "Turnos de Combate"
        unique_together = ['battle', 'turn_number']
        ordering = ['battle', 'turn_number']
    
    def __str__(self):
        return f"Turno {self.turn_number} - {self.battle}"


class AIMessage(models.Model):
    """Almacenamiento de mensajes y recomendaciones de la IA"""
    
    CONTEXT_CHOICES = [
        ('team', 'Análisis de Equipo'),
        ('battle', 'Recomendación de Combate'),
        ('general', 'Consejo General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    context = models.CharField(max_length=20, choices=CONTEXT_CHOICES, verbose_name="Contexto")
    
    # Datos enviados a la IA (JSON)
    input_data = models.JSONField(verbose_name="Datos de Entrada")
    
    # Respuesta de la IA
    recommendation = models.TextField(verbose_name="Recomendación")
    
    # Metadatos
    creature = models.ForeignKey(Creature, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Criatura Relacionada")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Equipo Relacionado")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    
    class Meta:
        verbose_name = "Mensaje de IA"
        verbose_name_plural = "Mensajes de IA"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"IA - {self.user.username} - {self.get_context_display()}"
