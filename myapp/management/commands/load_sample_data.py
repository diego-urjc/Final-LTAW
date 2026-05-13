from django.core.management.base import BaseCommand
from myapp.models import Creature, Move, CreatureMove


class Command(BaseCommand):
    help = 'Carga datos de ejemplo para PocketArena (criaturas y movimientos)'

    def handle(self, *args, **options):
        self.stdout.write('Cargando datos de ejemplo...')
        
        # Limpiar datos existentes
        CreatureMove.objects.all().delete()
        Creature.objects.all().delete()
        Move.objects.all().delete()
        
        # Crear movimientos primero
        moves_data = [
            # Movimientos de tipo Fuego
            {'name': 'Lanzallamas', 'type': 'fire', 'category': 'special', 'power': 90, 'accuracy': 100, 'pp': 15, 'description': 'Potente ataque de fuego que puede quemar al objetivo.'},
            {'name': 'Ascuas', 'type': 'fire', 'category': 'special', 'power': 40, 'accuracy': 100, 'pp': 25, 'description': 'Pequeñas llamas que atacan al objetivo.'},
            
            # Movimientos de tipo Agua
            {'name': 'Hidrobomba', 'type': 'water', 'category': 'special', 'power': 110, 'accuracy': 80, 'pp': 5, 'description': 'Potente chorro de agua con alta potencia pero baja precisión.'},
            {'name': 'Burbuja', 'type': 'water', 'category': 'special', 'power': 40, 'accuracy': 100, 'pp': 30, 'description': 'Ataque con burbujas de agua.'},
            
            # Movimientos de tipo Planta
            {'name': 'Rayo Solar', 'type': 'grass', 'category': 'special', 'power': 120, 'accuracy': 100, 'pp': 10, 'description': 'Potente ataque solar que requiere un turno de carga.'},
            {'name': 'Látigo Cepa', 'type': 'grass', 'category': 'physical', 'power': 45, 'accuracy': 100, 'pp': 25, 'description': 'Golpe con una liana flexible.'},
            
            # Movimientos de tipo Eléctrico
            {'name': 'Trueno', 'type': 'electric', 'category': 'special', 'power': 110, 'accuracy': 70, 'pp': 10, 'description': 'Potente rayo que puede paralizar al objetivo.'},
            {'name': 'Impactrueno', 'type': 'electric', 'category': 'physical', 'power': 40, 'accuracy': 100, 'pp': 30, 'description': 'Choque eléctrico de baja potencia.'},
            
            # Movimientos de tipo Normal
            {'name': 'Placaje', 'type': 'normal', 'category': 'physical', 'power': 40, 'accuracy': 100, 'pp': 35, 'description': 'Golpe con todo el cuerpo.'},
            {'name': 'Hiper Rayo', 'type': 'normal', 'category': 'special', 'power': 150, 'accuracy': 90, 'pp': 5, 'description': 'Extremadamente potente pero deja al usuario agotado.'},
            
            # Movimientos de tipo Psíquico
            {'name': 'Psíquico', 'type': 'psychic', 'category': 'special', 'power': 90, 'accuracy': 100, 'pp': 10, 'description': 'Ataque con poder mental que puede bajar la defensa especial.'},
            {'name': 'Confusión', 'type': 'psychic', 'category': 'special', 'power': 50, 'accuracy': 100, 'pp': 25, 'description': 'Ataque mental que puede confundir al objetivo.'},
            
            # Movimientos de tipo Roca
            {'name': 'Lanzarrocas', 'type': 'rock', 'category': 'physical', 'power': 50, 'accuracy': 90, 'pp': 15, 'description': 'Lanza rocas pequeñas al objetivo.'},
            {'name': 'Avalancha', 'type': 'rock', 'category': 'physical', 'power': 75, 'accuracy': 90, 'pp': 10, 'description': 'Derrumbe de rocas que golpea al objetivo.'},
            
            # Movimientos de tipo Tierra
            {'name': 'Terremoto', 'type': 'ground', 'category': 'physical', 'power': 100, 'accuracy': 100, 'pp': 10, 'description': 'Potente terremoto que afecta a todos los objetivos.'},
            {'name': 'Terremoto', 'type': 'ground', 'category': 'physical', 'power': 100, 'accuracy': 100, 'pp': 10, 'description': 'Golpe con tierra o arena.'},
            
            # Movimientos de tipo Hielo
            {'name': 'Rayo Hielo', 'type': 'ice', 'category': 'special', 'power': 90, 'accuracy': 100, 'pp': 10, 'description': 'Rayo congelante que puede congelar al objetivo.'},
            {'name': 'Bola Hielo', 'type': 'ice', 'category': 'special', 'power': 65, 'accuracy': 100, 'pp': 10, 'description': 'Lanza una bola de hielo al objetivo.'},
            
            # Movimientos de tipo Dragón
            {'name': 'Dragón Alado', 'type': 'dragon', 'category': 'physical', 'power': 100, 'accuracy': 100, 'pp': 15, 'description': 'Potente ataque dragón con alta precisión.'},
            {'name': 'Furia Dragón', 'type': 'dragon', 'category': 'physical', 'power': 120, 'accuracy': 100, 'pp': 10, 'description': 'Ataque de furia que aumenta el ataque pero causa daño.'},
        ]
        
        moves = {}
        for move_data in moves_data:
            move, created = Move.objects.get_or_create(
                name=move_data['name'],
                defaults=move_data
            )
            moves[move.name] = move
            if created:
                self.stdout.write(f'  Creado movimiento: {move.name}')
            else:
                self.stdout.write(f'  Movimiento ya existente: {move.name}')
        
        # Crear criaturas
        creatures_data = [
            {
                'name': 'Flamisaur',
                'type1': 'fire',
                'type2': None,
                'hp': 45,
                'attack': 52,
                'defense': 43,
                'speed': 65,
                'sp_attack': 60,
                'sp_defense': 50,
                'description': 'Una criatura de fuego con una llama en la cola.',
                'image_url': '',
                'moves': [('Ascuas', 1), ('Lanzallamas', 15), ('Placaje', 5), ('Hiper Rayo', 30)]
            },
            {
                'name': 'Aquatix',
                'type1': 'water',
                'type2': None,
                'hp': 50,
                'attack': 48,
                'defense': 50,
                'speed': 55,
                'sp_attack': 65,
                'sp_defense': 55,
                'description': 'Criatura acuática con aletas poderosas.',
                'image_url': '',
                'moves': [('Burbuja', 1), ('Hidrobomba', 20), ('Placaje', 8), ('Terremoto', 35)]
            },
            {
                'name': 'Verdantix',
                'type1': 'grass',
                'type2': None,
                'hp': 55,
                'attack': 45,
                'defense': 55,
                'speed': 45,
                'sp_attack': 55,
                'sp_defense': 65,
                'description': 'Criatura de planta con hojas afiladas.',
                'image_url': '',
                'moves': [('Látigo Cepa', 1), ('Rayo Solar', 25), ('Burbuja', 10), ('Placaje', 5)]
            },
            {
                'name': 'Electroz',
                'type1': 'electric',
                'type2': None,
                'hp': 40,
                'attack': 50,
                'defense': 45,
                'speed': 90,
                'sp_attack': 75,
                'sp_defense': 50,
                'description': 'Criatura eléctrica extremadamente rápida.',
                'image_url': '',
                'moves': [('Impactrueno', 1), ('Trueno', 18), ('Placaje', 7), ('Rayo Hielo', 22)]
            },
            {
                'name': 'Psikix',
                'type1': 'psychic',
                'type2': None,
                'hp': 45,
                'attack': 40,
                'defense': 45,
                'speed': 85,
                'sp_attack': 85,
                'sp_defense': 70,
                'description': 'Criatura psíquica con grandes poderes mentales.',
                'image_url': '',
                'moves': [('Confusión', 1), ('Psíquico', 15), ('Placaje', 5), ('Rayo Solar', 28)]
            },
            {
                'name': 'Rocadon',
                'type1': 'rock',
                'type2': 'ground',
                'hp': 80,
                'attack': 85,
                'defense': 100,
                'speed': 30,
                'sp_attack': 40,
                'sp_defense': 70,
                'description': 'Criatura rocosa con gran defensa física.',
                'image_url': '',
                'moves': [('Lanzarrocas', 1), ('Avalancha', 12), ('Terremoto', 18), ('Placaje', 5)]
            },
            {
                'name': 'Glacix',
                'type1': 'ice',
                'type2': None,
                'hp': 55,
                'attack': 55,
                'defense': 50,
                'speed': 70,
                'sp_attack': 70,
                'sp_defense': 65,
                'description': 'Criatura de hielo con cuerpo cristalino.',
                'image_url': '',
                'moves': [('Bola Hielo', 1), ('Rayo Hielo', 16), ('Burbuja', 10), ('Placaje', 6)]
            },
            {
                'name': 'Dragox',
                'type1': 'dragon',
                'type2': None,
                'hp': 70,
                'attack': 80,
                'defense': 65,
                'speed': 75,
                'sp_attack': 70,
                'sp_defense': 65,
                'description': 'Criatura dragón con escamas poderosas.',
                'image_url': '',
                'moves': [('Placaje', 1), ('Dragón Alado', 20), ('Furia Dragón', 30), ('Lanzallamas', 15)]
            },
            {
                'name': 'Normix',
                'type1': 'normal',
                'type2': None,
                'hp': 60,
                'attack': 70,
                'defense': 60,
                'speed': 65,
                'sp_attack': 50,
                'sp_defense': 55,
                'description': 'Criatura equilibrada sin tipo elemental especial.',
                'image_url': '',
                'moves': [('Placaje', 1), ('Hiper Rayo', 25), ('Lanzarrocas', 12), ('Látigo Cepa', 8)]
            },
            {
                'name': 'Voladrix',
                'type1': 'flying',
                'type2': None,
                'hp': 50,
                'attack': 65,
                'defense': 50,
                'speed': 95,
                'sp_attack': 55,
                'sp_defense': 50,
                'description': 'Criatura voladora con alas poderosas.',
                'image_url': '',
                'moves': [('Placaje', 1), ('Dragón Alado', 18), ('Impactrueno', 14), ('Lanzallamas', 22)]
            },
            {
                'name': 'Venomix',
                'type1': 'poison',
                'type2': None,
                'hp': 55,
                'attack': 60,
                'defense': 55,
                'speed': 70,
                'sp_attack': 65,
                'sp_defense': 70,
                'description': 'Criatura venenosa con garras tóxicas.',
                'image_url': '',
                'moves': [('Látigo Cepa', 1), ('Burbuja', 8), ('Placaje', 5), ('Rayo Solar', 24)]
            },
            {
                'name': 'Fantasmix',
                'type1': 'ghost',
                'type2': None,
                'hp': 45,
                'attack': 55,
                'defense': 50,
                'speed': 80,
                'sp_attack': 75,
                'sp_defense': 65,
                'description': 'Criatura fantasmal que puede atravesar paredes.',
                'image_url': '',
                'moves': [('Confusión', 1), ('Psíquico', 14), ('Placaje', 6), ('Trueno', 26)]
            },
        ]
        
        for creature_data in creatures_data:
            moves_list = creature_data.pop('moves')
            creature, created = Creature.objects.get_or_create(
                name=creature_data['name'],
                defaults=creature_data
            )
            
            if created:
                self.stdout.write(f'  Creada criatura: {creature.name}')
                
                # Asignar movimientos
                for move_name, level in moves_list:
                    if move_name in moves:
                        CreatureMove.objects.get_or_create(
                            creature=creature,
                            move=moves[move_name],
                            defaults={'level_learned': level}
                        )
                        self.stdout.write(f'    - {move_name} al nivel {level}')
            else:
                self.stdout.write(f'  Criatura ya existente: {creature.name}')
        
        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados exitosamente!'))
        self.stdout.write(f'Total criaturas: {Creature.objects.count()}')
        self.stdout.write(f'Total movimientos: {Move.objects.count()}')
        self.stdout.write(f'Total relaciones criatura-movimiento: {CreatureMove.objects.count()}')
