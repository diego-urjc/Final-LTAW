from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crea un usuario regular y un superusuario para PocketArena'

    def handle(self, *args, **options):
        self.stdout.write('Creando usuarios...')
        
        # Crear usuario regular
        regular_user, created = User.objects.get_or_create(
            username='user',
            defaults={
                'email': 'user@example.com',
                'is_active': True,
            }
        )
        if created:
            regular_user.set_password('password123')
            regular_user.save()
            self.stdout.write(self.style.SUCCESS('  Usuario regular creado: user / password123'))
        else:
            regular_user.set_password('password123')
            regular_user.save()
            self.stdout.write(self.style.WARNING('  Usuario regular ya existente: contraseña restablecida a password123'))
        
        # Crear superusuario
        superuser, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            superuser.set_password('admin123')
            superuser.save()
            self.stdout.write(self.style.SUCCESS('  Superusuario creado: admin / admin123'))
        else:
            superuser.set_password('admin123')
            superuser.save()
            self.stdout.write(self.style.WARNING('  Superusuario ya existente: contraseña restablecida a admin123'))
        
        self.stdout.write(self.style.SUCCESS('Usuarios configurados exitosamente!'))
