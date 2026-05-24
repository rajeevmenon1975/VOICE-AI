import sys
import time
import database
import backoffice_app
from state_machine import VoiceAIStateMachine

def print_slow(text, delay=0.01):
    """Simulates voice synthesis text flowing in real-time."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def run_terminal_simulation():
    """Runs the traditional interactive terminal loop (original prototype code)."""
    print("\n" + "="*80)
    print("      📞 RUNNING TRADITIONAL TERMINAL VOICE SIMULATION")
    print("="*80 + "\n")

    # 1. Initialize SQLite
    database.init_db()

    # 2. Select Client
    print("👥 AVAILABLE MOCK CLIENTS IN THE BACK-OFFICE SYSTEM:")
    clients = [
        database.get_client("CLIENT_123"),
        database.get_client("CLIENT_456"),
        database.get_client("CLIENT_789")
    ]
    
    for idx, c in enumerate(clients, 1):
        print(f"  {idx}. ID: {c['client_id']} | Name: {c['name']} | Lang: {c['preferred_lang']} | Ledger: ₹{c['ledger_balance']:,.2f} | Segments: {c['activated_segments']}")

    while True:
        try:
            choice = int(input("\n👉 Select a client to call (1-3): "))
            if 1 <= choice <= 3:
                client = clients[choice - 1]
                break
        except ValueError:
            pass
        print("❌ Invalid selection. Choose a number between 1 and 3.")

    # 3. Select Stock Pitch
    print("\n📈 SELECT AN EQUITY RESEARCH CALL RECOMMENDATION TO PITCH:")
    stocks = [
        ("RELIANCE", "Reliance Industries", 3000.0, 2700.0, 50), # Qty 50 * 2800 = 140,000 margin
        ("TCS", "TCS Limited", 4000.0, 3700.0, 10),      # Qty 10 * 3850 = 38,500 margin
        ("ITC", "ITC Limited", 460.0, 410.0, 100),       # Qty 100 * 430 = 43,000 margin
        ("IDEA", "Vodafone Idea (PENNY STOCK)", 15.0, 10.0, 600), # Qty 600 (Triggers Penny Stock limit)
        ("GTLINFRA", "GTL Infra (SEBI BANNED)", 2.5, 1.2, 500)   # Banned stock
    ]

    for idx, s in enumerate(stocks, 1):
        print(f"  {idx}. Symbol: {s[0]} | Target: ₹{s[2]} | SL: ₹{s[3]} | Recommended Qty: {s[4]}")

    while True:
        try:
            choice = int(input("\n👉 Select a research recommendation to pitch (1-5): "))
            if 1 <= choice <= 5:
                pitch_stock = stocks[choice - 1]
                break
        except ValueError:
            pass
        print("❌ Invalid selection. Choose a number between 1 and 5.")

    symbol, name, target, sl, recommended_qty = pitch_stock

    # 4. Initiate State Machine
    print("\n" + "~"*80)
    print(f"📞 OUTBOUND CALL INITIATED TO: {client['name']} ({client['phone']})")
    print(f"🗣️  DETECTOR ACTIVE: Language Auto-Set to: {client['preferred_lang']}")
    print("~"*80 + "\n")

    sm = VoiceAIStateMachine(
        client_id=client["client_id"],
        symbol=symbol,
        target=target,
        sl=sl,
        recommended_qty=recommended_qty
    )

    # Initial Turn: Greet the user
    ai_response = sm.handle_input("") # Triggers greeting
    print("🤖 Voice AI:")
    print_slow(ai_response)

    # Conversation loop
    while sm.state not in ["COMPLETED", "TERMINATED"]:
        try:
            user_input = input("\n🗣️  You (Client): ")
            if not user_input.strip():
                continue
            
            ai_response = sm.handle_input(user_input)
            print("\n🤖 Voice AI:")
            print_slow(ai_response)
        except Exception as e:
            print(f"\n❌ System Exception: {e}")
            break

    # 5. Outbound callback (if trade completed successfully)
    if sm.state == "COMPLETED":
        print("\n" + "~"*80)
        print("⏳ SIMULATING OMS ORDER EXECUTION...")
        print("   Order filled completely in market. Triggering proactive Trade Callback Service.")
        print("~"*80)
        time.sleep(1.5)

        print("\n" + "~"*80)
        print(f"📞 OUTBOUND TRADING CALLBACK DIALING: {client['name']} ({client['phone']})")
        print("~"*80 + "\n")

        print("👤 Client: [Answers the phone]")
        print("🤖 Voice AI (Callback):")
        callback_script = sm.execute_callback_call()
        print_slow(callback_script)
        print("\n[Call completed and disconnected successfully.]\n")

    # 6. Database Audit Log Check
    print("="*80)
    print("📑 CORE COMPLIANCE REGULATORY AUDIT REPORT (SQLite):")
    print("="*80)
    
    order_logs = database.get_order_logs(client["client_id"])
    if order_logs:
        print("\n📝 COMPLETED ORDER LOGS FOR CLIENT:")
        for log in order_logs:
            print(f"  • Order ID: {log['order_id']}")
            print(f"    Symbol: {log['symbol']} | Action: {log['action']} | Qty: {log['quantity']} | Price: ₹{log['price']:.2f}")
            print(f"    Product: {log['product_type']} | Type: {log['order_type']} | Status: {log['status']}")
            if log["rejection_reason"]:
                print(f"    🚨 Rejection Reason: {log['rejection_reason']}")
            print(f"    🎙️ Recording URL: {log['recording_url']}")
            print(f"    📅 Created At: {log['created_at']}")
            print("-" * 50)
    else:
        print("\nℹ️ No trades were completed in this session.")

    print("\n🔒 SYSTEM STATUS: SECURE AND AUDITABLE. PROTOTYPE TERMINATED.")
    print("="*80)

def main():
    print("="*80)
    print("      🚀 INDIAN STOCKBROKING VOICE AI AGENT SIMULATION PLATFORM 🚀")
    print("         Compliance-Guardrailed, Multilingual & Fully Integrated")
    print("="*80)

    print("\n💡 CHOOSE RUN MODE:")
    print("  1. Run traditional CLI Interactive Voice Simulation")
    print("  2. Launch Premium Glassmorphic Web Dashboard (Analytics, MS SQL Console & Vocal Sandbox)")
    
    while True:
        try:
            choice = int(input("\n👉 Select a mode (1-2): "))
            if choice == 1:
                run_terminal_simulation()
                break
            elif choice == 2:
                backoffice_app.start_server()
                break
        except ValueError:
            pass
        print("❌ Invalid choice. Enter 1 or 2.")

if __name__ == "__main__":
    main()
