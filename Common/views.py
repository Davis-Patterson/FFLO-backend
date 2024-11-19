from django.http import JsonResponse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from decouple import config
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(csrf_exempt, name='dispatch')
class SetupDatabaseView(View):
    def post(self, request, *args, **kwargs):
        response = {"status": "success", "message": ""}

        # Step 1: Apply migrations
        try:
            call_command('makemigrations', interactive=False)
            call_command('migrate', interactive=False)
            response["message"] += "Migrations applied successfully. "
        except Exception as e:
            response["status"] = "error"
            response["message"] += f"Error applying migrations: {str(e)}"
            return JsonResponse(response, status=500)

        # Step 2: Create superuser
        try:
            username = config("SUPERUSER_USERNAME").strip('"').strip("'")
            email = config("SUPERUSER_EMAIL").strip('"').strip("'")
            password = config("SUPERUSER_PASSWORD").strip('"').strip("'")

            User = get_user_model()
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                response["message"] += f"Superuser '{username}' created successfully."
            else:
                response["message"] += f"Superuser '{username}' already exists."
        except Exception as e:
            response["status"] = "error"
            response["message"] += f"Error creating superuser: {str(e)}"
            return JsonResponse(response, status=500)

        return JsonResponse(response, status=200)
