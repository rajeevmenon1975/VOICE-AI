import time
import random
import uuid
from datetime import datetime
import database

# In-memory storage for active OTP sessions (Client ID -> OTP code)
_active_otps = {}

class RMSException(Exception):
    pass

def get_ledger_balance(client_id: str) -> dict:
    """Simulates: GET /v1/client/ledger?client_id=..."""
    client = database.get_client(client_id)
    if not client:
        return {"status": "error", "message": "Client not found"}
    
    return {
        "status": "success",
        "data": {
            "client_id": client["client_id"],
            "name": client["name"],
            "phone": client["phone"],
            "ledger_balance": client["ledger_balance"],
            "available_margin": client["ledger_balance"],
            "activated_segments": client["activated_segments"]
        }
    }

def validate_rms_rules(client_id: str, symbol: str, transaction_type: str, quantity: int, price_type: str, price: float, product_type: str) -> dict:
    """
    Simulates: POST /v1/rms/validate
    Executes core risk management validations against the mock ledger and stock database:
    1. Client validity
    2. Segment activation checks (e.g., F&O segmentation)
    3. Stock ban lists (SEBI F&O bans or custom broker blocks)
    4. Penny stock restriction safeguards
    5. Leverage margin checks (CNC vs MIS)
    6. Ledger balance sufficiency
    """
    client = database.get_client(client_id)
    if not client:
        return {
            "status": "REJECTED",
            "reason": "Client profile does not exist.",
            "margin_required": 0.0,
            "shortfall": 0.0
        }

    stock = database.get_stock(symbol)
    if not stock:
        return {
            "status": "REJECTED",
            "reason": f"Stock symbol {symbol} is not listed or suspended.",
            "margin_required": 0.0,
            "shortfall": 0.0
        }

    # Guardrail 1: Segment Verification
    activated_segs = [s.strip().upper() for s in client["activated_segments"].split(",")]
    if "EQUITY" not in activated_segs:
         return {
            "status": "REJECTED",
            "reason": "Equity trading segment is not activated for this client account.",
            "margin_required": 0.0,
            "shortfall": 0.0
        }

    # Guardrail 2: SEBI / Exchange Stock Ban List
    if stock["is_banned"]:
        return {
            "status": "REJECTED",
            "reason": f"Order rejected. {symbol} is currently under SEBI trading ban.",
            "margin_required": 0.0,
            "shortfall": 0.0
        }

    # Guardrail 3: Penny Stock / High-Risk Guardrail
    if stock["is_penny"] and quantity > 500:
        return {
            "status": "REJECTED",
            "reason": f"Risk Control: Maximum quantity limit of 500 exceeded for high-risk penny stock {symbol}.",
            "margin_required": 0.0,
            "shortfall": 0.0
        }

    # Use stock price if MARKET order
    trade_price = price if price_type.upper() == "LIMIT" else stock["current_price"]
    gross_value = quantity * trade_price

    # Guardrail 4: Margin Requirement Calculation
    # CNC (Cash-n-Carry / Delivery) requires 100% upfront margin
    # MIS (Margin Intraday Square-off) requires 20% margin (5x leverage)
    if product_type.upper() == "CNC":
        margin_required = gross_value
    elif product_type.upper() == "MIS":
        margin_required = gross_value * 0.20
    else:
        return {
            "status": "REJECTED",
            "reason": f"Unsupported product type: {product_type}. Must be CNC or MIS.",
            "margin_required": 0.0,
            "shortfall": 0.0
        }

    # Ledger funds sufficiency check
    available_funds = client["ledger_balance"]
    if transaction_type.upper() == "BUY":
        if margin_required > available_funds:
            shortfall = margin_required - available_funds
            return {
                "status": "REJECTED",
                "reason": f"Insufficient margin. Required: ₹{margin_required:,.2f}, Available: ₹{available_funds:,.2f}.",
                "margin_required": margin_required,
                "shortfall": shortfall
            }
        else:
            return {
                "status": "APPROVED",
                "reason": "Sufficient balance. Risk validation passed.",
                "margin_required": margin_required,
                "margin_available": available_funds,
                "shortfall": 0.0
            }
    else:
        # SELL trade: Check if client holds the shares in DP (Delivery) or allows intraday short
        if product_type.upper() == "CNC":
            # For simplicity, we assume client has holdings for sells, but we still approve RMS
            return {
                "status": "APPROVED",
                "reason": "Sell order holdings pre-approved.",
                "margin_required": 0.0,
                "margin_available": available_funds,
                "shortfall": 0.0
            }
        else:
            # Intraday MIS short-selling margin check
            if margin_required > available_funds:
                shortfall = margin_required - available_funds
                return {
                    "status": "REJECTED",
                    "reason": f"Insufficient margin for Intraday Short. Required: ₹{margin_required:,.2f}.",
                    "margin_required": margin_required,
                    "shortfall": shortfall
                }
            return {
                "status": "APPROVED",
                "reason": "Sufficient balance for short-selling.",
                "margin_required": margin_required,
                "margin_available": available_funds,
                "shortfall": 0.0
            }

def send_voice_otp(client_id: str) -> str:
    """
    Generates a secure 4-digit Voice-OTP for Two-Factor Authentication.
    Simulates sending it via SMS and WhatsApp.
    """
    client = database.get_client(client_id)
    if not client:
        return ""

    otp = f"{random.randint(1000, 9999)}"
    _active_otps[client_id] = otp

    # Print simulating an SMS/WhatsApp dispatch
    print("\n" + "="*60)
    print(f"📡 [MOCK GATEWAY] DISPATCHING SECURE 2FA OTP TO REGISTERED MOBILE {client['phone']}")
    print(f"💬 SMS: \"Use verification code {otp} to authorize your order on [Broker Name] Voice AI. Code expires in 3 mins.\"")
    print(f"💬 WhatsApp: \"🔐 [Broker Name] OTP: {otp}. Never share this code.\"")
    print("="*60 + "\n")

    return otp

def verify_voice_otp(client_id: str, spoken_otp: str) -> bool:
    """Verifies the OTP transcribed from the user's spoken confirmation."""
    clean_spoken = "".join(filter(str.isdigit, str(spoken_otp)))
    cached_otp = _active_otps.get(client_id)
    
    if cached_otp and clean_spoken == cached_otp:
        # OTP consumed upon successful verification
        del _active_otps[client_id]
        return True
    return False

def place_order(client_id: str, symbol: str, transaction_type: str, quantity: int, price_type: str, price: float, product_type: str, recording_url: str) -> dict:
    """
    Simulates: POST /v1/orders/place
    Executes the trade through the Order Management System (OMS).
    Applies final real-time checks, updates the client's ledger, and creates SEBI compliance audits.
    """
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"
    
    # 1. Run final RMS check
    rms_status = validate_rms_rules(
        client_id=client_id,
        symbol=symbol,
        transaction_type=transaction_type,
        quantity=quantity,
        price_type=price_type,
        price=price,
        product_type=product_type
    )

    if rms_status["status"] == "REJECTED":
        # Log rejected order for complaints auditability
        database.log_order(
            order_id=order_id,
            client_id=client_id,
            symbol=symbol,
            action=transaction_type,
            quantity=quantity,
            price=price,
            order_type=price_type,
            product_type=product_type,
            status="REJECTED",
            rejection_reason=rms_status["reason"],
            recording_url=recording_url
        )
        return {
            "status": "error",
            "message": f"Order rejected by RMS: {rms_status['reason']}",
            "order_id": order_id
        }

    # 2. Execution logic - update balances & write logs
    client = database.get_client(client_id)
    stock = database.get_stock(symbol)
    trade_price = price if price_type.upper() == "LIMIT" else stock["current_price"]

    # Calculate actual ledger settlement
    margin = rms_status["margin_required"]
    new_balance = client["ledger_balance"]
    
    if transaction_type.upper() == "BUY":
        # Block the margin amount from the ledger
        new_balance -= margin
    else:
        # Sell orders immediately add premium cash back (mocking standard settlement)
        new_balance += (quantity * trade_price)

    database.update_client_balance(client_id, new_balance)
    
    # Log completed order
    database.log_order(
        order_id=order_id,
        client_id=client_id,
        symbol=symbol,
        action=transaction_type,
        quantity=quantity,
        price=trade_price,
        order_type=price_type,
        product_type=product_type,
        status="COMPLETED",
        recording_url=recording_url
    )

    return {
        "status": "success",
        "data": {
            "order_id": order_id,
            "status": "COMPLETED",
            "average_price": trade_price,
            "quantity_filled": quantity,
            "updated_ledger": new_balance
        }
    }
