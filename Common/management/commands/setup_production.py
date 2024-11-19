from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
from decouple import config

class Command(BaseCommand):
    help = "Prepare the database, apply migrations, and create a superuser for production."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Applying database migrations..."))
        try:
            call_command('makemigrations', interactive=False)
            call_command('migrate', interactive=False)
            self.stdout.write(self.style.SUCCESS("Database migrations applied successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error applying migrations: {e}"))
            return

        username = config("SUPERUSER_USERNAME").strip('"').strip("'")
        email = config("SUPERUSER_EMAIL").strip('"').strip("'")
        password = config("SUPERUSER_PASSWORD").strip('"').strip("'")

        self.stdout.write(f"Superuser details:\nUsername: {username}\nEmail: {email}")

        if not username or not email or not password:
            self.stdout.write(self.style.ERROR("SUPERUSER_USERNAME, SUPERUSER_EMAIL, or SUPERUSER_PASSWORD is missing in the environment variables."))
            return

        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING("Creating superuser..."))
            try:
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating superuser: {e}"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
