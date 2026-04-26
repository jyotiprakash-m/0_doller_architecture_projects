import stripe
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET
from services import db
from routers.auth import get_current_user_id

router = APIRouter(prefix="/api/billing", tags=["Billing"])
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = STRIPE_API_KEY

# Plan configuration (Hardcoded for MVP, ideally in config or DB)
SUBSCRIPTION_PRICE_ID = "price_mock_123" # User will need to replace this
CREDITS_PER_MONTH = 1000.0

@router.post("/create-checkout-session")
async def create_checkout_session(user_id: str = Depends(get_current_user_id)):
    """Create a Stripe checkout session for a subscription."""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # If user already has a stripe customer ID, use it, else Stripe will create one
        customer_kwargs = {}
        if user.get("stripe_customer_id"):
            customer_kwargs["customer"] = user["stripe_customer_id"]
        else:
            customer_kwargs["customer_email"] = user["email"]

        # For Next.js frontend running locally
        frontend_url = "http://localhost:3000"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'SupportSim AI Pro Tier',
                        'description': f'{int(CREDITS_PER_MONTH)} credits/month for agent training.',
                    },
                    'unit_amount': 1500, # $15.00
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{frontend_url}/billing?success=true",
            cancel_url=f"{frontend_url}/billing?canceled=true",
            client_reference_id=user_id,
            metadata={"user_id": user_id},
            **customer_kwargs
        )

        return {"checkout_url": checkout_session.url}
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
async def create_portal_session(user_id: str = Depends(get_current_user_id)):
    """Create a Stripe Customer Portal session."""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    user = db.get_user_by_id(user_id)
    if not user or not user.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="User is not a Stripe customer yet.")

    try:
        frontend_url = "http://localhost:3000/billing"
        portal_session = stripe.billing_portal.Session.create(
            customer=user["stripe_customer_id"],
            return_url=frontend_url,
        )
        return {"portal_url": portal_session.url}
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe Webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook secret not configured. Skipping webhook verification.")
        # Only allowed in dev if skipping verification intentionally
        try:
            event = stripe.Event.construct_from(import_json=payload, sig=sig_header, secret=None)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payload")
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase
        user_id = session.get("client_reference_id")
        customer_id = session.get("customer")
        
        if user_id and customer_id:
            # In a real app, you'd fetch the subscription to get the real end date
            # Here we just mock adding 30 days
            from datetime import timedelta
            period_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            
            # Award credits
            db.update_stripe_subscription(
                user_id=user_id,
                customer_id=customer_id,
                status="active",
                period_end=period_end,
                credits_to_add=CREDITS_PER_MONTH
            )
            logger.info(f"Subscription fulfilled for user {user_id}. Awarded {CREDITS_PER_MONTH} credits.")

    elif event['type'] == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription = event['data']['object']
        customer_id = subscription.get("customer")
        
        # Find user by customer ID (needs a quick DB query, we'll implement a simple one)
        conn = db.get_connection()
        user_row = conn.execute("SELECT id FROM users WHERE stripe_customer_id = ?", (customer_id,)).fetchone()
        
        if user_row:
            user_id = user_row["id"]
            db.update_stripe_subscription(
                user_id=user_id,
                customer_id=customer_id,
                status="canceled",
                period_end="",
                credits_to_add=0
            )
            logger.info(f"Subscription canceled for user {user_id}.")
        conn.close()

    return {"status": "success"}
