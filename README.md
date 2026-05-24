# 📞 Voice AI Stockbroker Integration Prototype (India)

A Python implementation of an enterprise-grade, compliance-guardrailed Voice AI system designed for Indian stock brokerages. It demonstrates localized multilingual advisory, real-time back-office ledger queries, Risk Management System (RMS) checkouts, SMS 2FA authorizations, error-free order entry, and automated trade callback notifications.

---

## 🏗️ Project Architecture & Components

The prototype is fully written in Python using SQLite as an embedded transactional database:

1.  **`database.py`**: Initializes the SQLite database (`trader.db`) and seeds three mock clients with varying balances/segment access, along with active, banned, and penny stocks. It acts as the broker's compliance ledger and call-telemetry store.
2.  **`mock_apis.py`**: Simulates the broker's transactional microservices:
    *   `GET /client/ledger`: Margin cash check.
    *   `POST /rms/validate`: Real-time pre-trade risk validations (banned list, penny-stock quantity restrictions, intraday vs delivery margins, and fund checks).
    *   `POST /orders/place`: Executes the order, updates client ledgers, and logs the execution.
    *   `2FA Voice-OTP Service`: Caches and simulates dynamic SMS/WhatsApp codes.
3.  **`state_machine.py`**: Manages the conversational states. It has complete translation scripts and localized templates in **English**, **Hindi (Hinglish)**, and **Gujarati (Gujlish)** to deliver smooth regional audio flows.
4.  **`run_demo.py`**: The interactive driver script. Runs the entire pipeline right in your terminal.
5.  **`implementation_plan.md`**: Architectural blueprint and step-by-step enterprise guides.

---

## ⚡ How to Run the Interactive Simulation

To launch the interactive simulator, run the following command in your terminal:

```bash
python run_demo.py
```

### What You Can Test
*   **Segment Activation Safeguards**: Call Amit Patel or Priya Sharma and check how the system responds.
*   **Banned Stock Blocking**: Pitch `GTLINFRA` (Banned) and see the Voice AI instantly block the trade and warn the client before placing it.
*   **Penny Stock Quantity Guardrails**: Pitch `IDEA` (Penny stock) with 600 shares, and watch the risk engine reject it due to security boundaries.
*   **Insufficient Margin Adjustments**: Call Priya Sharma (Ledger: ₹12,000) and pitch `RELIANCE` (requires ₹1,40,000 margin). The Voice AI will detect the shortfall and dynamically offer an adjusted lower quantity (4 shares instead of 50) or a UPI payment link!
*   **Multilingual Audio Flows**:
    *   **Rajeev Menon** speaks English.
    *   **Priya Sharma** speaks Hindi.
    *   **Amit Patel** speaks Gujarati.
*   **Authentic 2FA OTP verification**: Speak/enter the generated mock SMS code when requested. Enter a wrong code to test security blocking!
*   **Proactive Callback Loop**: Witness the proactive outbound trade-fill call once the order executes.
*   **SEBI-Compliant SQLite Log**: Review the complete SQLite audit log report showing the final ledger balance, order status, and recording references.

---

## 📁 Directory Structure
```
voice_ai_trader/
├── trader.db               # SQLite database (auto-generated)
├── database.py             # Schema & Seed data
├── mock_apis.py            # Ledger, RMS & Order APIs
├── state_machine.py        # Conversational dialog tree (EN, HI, GU)
├── run_demo.py             # Interactive terminal demo
├── requirements.txt        # Empty (Zero external packages needed)
└── implementation_plan.md  # Architectural reference
```
