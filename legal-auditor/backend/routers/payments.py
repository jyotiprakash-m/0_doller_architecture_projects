"""
Payments Router for Legal Auditor SaaS.
Handles Stripe Checkout sessions and Webhooks for credit replenishment.
"""
import logging
import stripe
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel

from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET
from services import db
from services.auth_utils import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["Payments"])

stripe.api_key = STRIPE_API_KEY

class CheckoutRequest(BaseModel):
    plan_id: str  # e.g., "starter", "pro"

# Pricing configuration
PLANS = {
    "starter": {"name": "Starter Pack", "credits": 5, "price": 500}, # $5.00
    "pro": {"name": "Professional Pack", "credits": 20, "price": 1500}, # $15.00
    "enterprise": {"name": "Enterprise Pack", "credits": 100, "price": 5000}, # $50.00
}

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest, 
    user_id: str = Depends(get_current_user_id)
):
    """Create a Stripe Checkout session for buying credits."""
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    plan = PLANS[request.plan_id]
    user = db.get_user_by_id(user_id)
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": plan["name"],
                            "description": f"Replenish {plan['credits']} audit credits.",
                        },
                        "unit_amount": plan["price"],
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:3000/#dashboard?payment=success",
            cancel_url="http://localhost:3000/#dashboard?payment=cancel",
            client_reference_id=user_id,
            customer_email=user["email"],
            metadata={
                "plan_id": request.plan_id,
                "credits": plan["credits"]
            }
        )
        return {"url": checkout_session.url}
    except Exception as e:
        logger.error(f"Stripe session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="Stripe-Signature")):
    """Handle Stripe webhooks to replenish credits."""
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        user_id = session.get("client_reference_id")
        credits_to_add = float(session.get("metadata", {}).get("credits", 0))
        
        if user_id and credits_to_add > 0:
            db.update_user_credits(user_id, credits_to_add)
            logger.info(f"Added {credits_to_add} credits to user {user_id}")
            
    return {"status": "success"}
