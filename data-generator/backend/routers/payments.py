"""
Payments Router for Synthetic Data Generator SaaS.
Handles Stripe Checkout sessions and Webhooks for credit top-ups.

Plans:
  - starter:    50 generation credits   → $5
  - pro:        250 generation credits  → $19
  - enterprise: 1000 generation credits → $49
"""
import logging
import stripe
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel

from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PUBLISHABLE_KEY
from services import db
from services.auth_utils import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["Payments"])

stripe.api_key = STRIPE_API_KEY

class CheckoutRequest(BaseModel):
    plan_id: str  # "starter" | "pro" | "enterprise"

# ── Pricing Plans ─────────────────────────────────────────────────────────────
# credits = number of generation jobs the user can trigger
PLANS = {
    "starter": {
        "name": "Starter Pack",
        "credits": 50,
        "price": 500,           # $5.00 in cents
        "description": "50 data generation jobs — perfect for small projects.",
        "badge": "Most Popular",
    },
    "pro": {
        "name": "Pro Pack",
        "credits": 250,
        "price": 1900,          # $19.00 in cents
        "description": "250 generation jobs — for active development teams.",
        "badge": "Best Value",
    },
    "enterprise": {
        "name": "Enterprise Pack",
        "credits": 1000,
        "price": 4900,          # $49.00 in cents
        "description": "1,000 generation jobs — unlimited scale for your org.",
        "badge": None,
    },
}


@router.get("/plans")
async def get_plans():
    """Return available pricing plans (no auth needed — shown on landing page)."""
    return {
        "plans": [
            {
                "id": plan_id,
                "name": config["name"],
                "credits": config["credits"],
                "price_usd": config["price"] / 100,
                "description": config["description"],
                "badge": config["badge"],
            }
            for plan_id, config in PLANS.items()
        ],
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
    }


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create a Stripe Checkout session to purchase generation credits."""
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan ID: {request.plan_id}")

    plan = PLANS[request.plan_id]
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not STRIPE_API_KEY or STRIPE_API_KEY.startswith("sk_test_YOUR"):
        raise HTTPException(
            status_code=503,
            detail="Stripe is not configured. Add your STRIPE_API_KEY to .env"
        )

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": plan["name"],
                            "description": plan["description"],
                        },
                        "unit_amount": plan["price"],
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:3000/?payment=success",
            cancel_url="http://localhost:3000/?payment=cancel",
            client_reference_id=user_id,
            customer_email=user["email"],
            metadata={
                "plan_id": request.plan_id,
                "credits": str(plan["credits"]),
                "user_id": user_id,
            }
        )
        logger.info(f"Checkout session created for user {user_id}, plan: {request.plan_id}")
        return {"url": checkout_session.url, "session_id": checkout_session.id}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=str(e.user_message))
    except Exception as e:
        logger.error(f"Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Handle Stripe webhooks to replenish user credits on successful payment.
    Must be called by Stripe, not the frontend (signature verification enforced).
    """
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.warning("Stripe webhook: invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook: invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = session.get("client_reference_id")
        metadata = session.get("metadata", {})
        credits_to_add = int(metadata.get("credits", 0))
        plan_id = metadata.get("plan_id", "unknown")

        if user_id and credits_to_add > 0:
            db.update_user_credits(user_id, credits_to_add)
            logger.info(
                f"✅ Payment complete — added {credits_to_add} credits to user {user_id} (plan: {plan_id})"
            )
        else:
            logger.warning(f"Webhook: missing user_id or credits in metadata: {metadata}")

    return {"status": "success"}


@router.get("/credits")
async def get_credits(user_id: str = Depends(get_current_user_id)):
    """Get current user's credit balance."""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "credits": user["credits"],
        "user_id": user_id,
    }
