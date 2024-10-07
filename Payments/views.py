import stripe
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from Payments.models import Payment
from Server.models import Book, BookRental
from Server.views import rental_request
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


class CheckoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        cart_items = request.data.get('cart_items', [])
        if not cart_items:
            return Response({"detail": "No items in the cart"}, status=status.HTTP_400_BAD_REQUEST)

        book_ids = [item['book_id'] for item in cart_items if item['type'] == 'rental']
        total_amount = 0
        rental_details = {}

        # If there are rentals in the cart, calculate rental prices
        if book_ids:
            rental_details = rental_request(user, book_ids)
            if "error" in rental_details:
                return Response({"detail": rental_details["error"]}, status=status.HTTP_400_BAD_REQUEST)
            total_amount += rental_details["total_rental_amount"]

        return Response({
            "total_amount": total_amount,
            "rental_details": rental_details,
            "stripe_payment_intent": None  # Placeholder for Stripe payment intent
        }, status=status.HTTP_200_OK)


class CheckoutFinalizationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        payment_successful = request.data.get('payment_successful', False)
        stripe_payment_id = request.data.get('stripe_payment_id', None)
        cart_items = request.data.get('cart_items', [])

        if not payment_successful or not stripe_payment_id:
            return Response({"detail": "Payment failed or incomplete"}, status=status.HTTP_400_BAD_REQUEST)

        book_ids = [item['book_id'] for item in cart_items if item['type'] == 'rental']
        rentals = []

        # Finalize rentals if present
        if book_ids:
            rental_details = rental_request(user, book_ids)
            if "error" in rental_details:
                return Response({"detail": rental_details["error"]}, status=status.HTTP_400_BAD_REQUEST)

            for book_id in book_ids:
                book = Book.objects.get(id=book_id)
                free_rental = rental_details['free_books_used'] > 0
                rental = BookRental.objects.create(book=book, user=user, free=free_rental)
                rentals.append(rental)
                book.available -= 1
                book.save()

            # Update membership free books if used
            active_membership = user.memberships.filter(active=True).first()
            if active_membership:
                active_membership.free_books_used += rental_details['free_books_used']
                active_membership.save()

        # Record the payment (instead of transaction)
        payment = Payment.objects.create(
            user=user,
            stripe_payment_intent_id=stripe_payment_id,
            amount=sum([item['price'] for item in cart_items]),
            currency='usd',  # Adjust as necessary
            status="completed",  # Assuming payment is successful
            item="Book Rentals"
        )

        # Attach the payment to the rentals
        for rental in rentals:
            rental.payment = payment
            rental.save()

        return Response({
            "detail": "Checkout finalized successfully",
            "rental_ids": [rental.id for rental in rentals],
            "payment_id": payment.id
        }, status=status.HTTP_200_OK)
