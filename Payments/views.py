import stripe
from django.conf import settings
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from Payments.models import Payment
from rest_framework.views import APIView

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get('amount')  # Ensure amount is calculated server-side
        currency = "usd"

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe expects the amount in cents
                currency=currency,
                metadata={"user_id": user.id}
            )

            # Store the payment intent in the database
            Payment.objects.create(
                user=user,
                stripe_payment_intent_id=intent['id'],
                amount=amount,
                currency=currency,
                status=intent['status']
            )

            return Response({
                'client_secret': intent['client_secret']
            })

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=400)


def handle_payment_succeeded(payment_intent):
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
        payment.status = 'succeeded'
        payment.save()
    except Payment.DoesNotExist:
        print("Payment not found for this intent ID")


def handle_payment_failed(payment_intent):
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
        payment.status = 'failed'
        payment.save()
    except Payment.DoesNotExist:
        print("Payment not found for this intent ID")


class StripeWebhookView(APIView):
    def post(self, request):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            handle_payment_succeeded(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            handle_payment_failed(event['data']['object'])

        return HttpResponse(status=200)
