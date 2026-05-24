import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime
import database
import mock_apis
import mssql_integration
from state_machine import VoiceAIStateMachine

PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Dynamic Session storage (Session ID -> State Machine Instance)
_sessions = {}

class BackofficeHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Robust REST and Static file server with ZERO external dependencies.
    """
    def log_message(self, format, *args):
        # Suppress standard terminal clutter, log clean server transactions
        sys_log = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HTTP {args[1]} - {args[0]}"
        print(f"📡 {sys_log}")

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        # CORS preflight fallback
        if path == "/":
            path = "/index.html"

        # --- API Routes ---
        if path.startswith("/api/"):
            self.handle_api_get(path, url_parsed.query)
            return

        # --- Static File Serving ---
        self.serve_static_file(path)

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        # Read JSON POST Body
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        
        try:
            body = json.loads(post_data) if post_data else {}
        except Exception:
            body = {}

        # --- API Routes ---
        if path.startswith("/api/"):
            self.handle_api_post(path, body)
            return

        self.send_json_response(404, {"error": "Endpoint not found"})

    def handle_api_get(self, path, query):
        if path == "/api/clients":
            # Fetches client ledgers and normalizes segment activation lists
            clients = [
                database.get_client("CLIENT_123"),
                database.get_client("CLIENT_456"),
                database.get_client("CLIENT_789")
            ]
            normalized_clients = []
            for client in clients:
                if client:
                    client["activated_segments"] = database.parse_activated_segments(client.get("activated_segments"))
                    normalized_clients.append(client)
            self.send_json_response(200, {"status": "success", "data": normalized_clients})

        elif path == "/api/database-status":
            status = mssql_integration.get_connection_status()
            self.send_json_response(200, {"status": "success", "data": status})

        elif path == "/api/behavioral-analytics":
            # Extracts MS SQL behavioral analytical insights
            analytics = mssql_integration.get_behavioral_patterns()
            self.send_json_response(200, {"status": "success", "data": analytics})

        elif path == "/api/order-logs":
            logs = database.get_order_logs()
            self.send_json_response(200, {"status": "success", "data": logs})

        else:
            self.send_json_response(404, {"error": f"API GET endpoint {path} not found"})

    def handle_api_post(self, path, body):
        global _sessions

        if path == "/api/sql-query":
            # Run custom SQL queries through MS SQL Connector
            sql_query = body.get("query", "")
            if not sql_query:
                self.send_json_response(400, {"status": "error", "message": "SQL query parameter is required"})
                return

            result = mssql_integration.run_query(sql_query)
            self.send_json_response(200, result)

        elif path == "/api/sql-config":
            # Updates real MS SQL Server connection variables
            server = body.get("server", "")
            dbname = body.get("database", "BrokerLedgerDB")
            username = body.get("username", "")
            password = body.get("password", "")
            port = int(body.get("port", 1433))
            encrypt = body.get("encrypt", True)

            config_res = mssql_integration.configure_mssql_connection(
                server=server,
                database=dbname,
                username=username,
                password=password,
                port=port,
                encrypt=encrypt
            )
            self.send_json_response(200, config_res)

        elif path == "/api/voice-ai/start":
            # Starts outbound call simulation
            client_id = body.get("client_id", "CLIENT_123")
            symbol = body.get("symbol", "RELIANCE")
            target = float(body.get("target", 3000.0))
            sl = float(body.get("sl", 2700.0))
            recommended_qty = int(body.get("recommended_qty", 50))

            try:
                sm = VoiceAIStateMachine(
                    client_id=client_id,
                    symbol=symbol,
                    target=target,
                    sl=sl,
                    recommended_qty=recommended_qty
                )
                session_id = sm.call_id
                _sessions[session_id] = sm
                
                # Fetch initial response (greeting + pitch opt-in)
                ai_speech = sm.handle_input("")
                
                self.send_json_response(200, {
                    "status": "success",
                    "session_id": session_id,
                    "state": sm.state,
                    "response": ai_speech,
                    "lang": sm.lang,
                    "client": sm.client,
                    "stock": sm.stock
                })
            except Exception as e:
                self.send_json_response(500, {"status": "error", "message": str(e)})

        elif path == "/api/voice-ai/turn":
            # Handles audio voice transcripts fed into conversational engine
            session_id = body.get("session_id", "")
            speech = body.get("speech", "")

            if not session_id or session_id not in _sessions:
                self.send_json_response(400, {"status": "error", "message": "Invalid or expired session ID"})
                return

            sm = _sessions[session_id]
            
            try:
                ai_speech = sm.handle_input(speech)
                
                # Expose generated OTP to simplify sandbox testing
                current_otp = mock_apis._active_otps.get(sm.client_id) if sm.state == "OTP_WAIT" else None

                # Generate proactive callback if status has changed to COMPLETED
                callback_speech = None
                if sm.state == "COMPLETED":
                    callback_speech = sm.execute_callback_call()

                self.send_json_response(200, {
                    "status": "success",
                    "state": sm.state,
                    "response": ai_speech,
                    "active_otp": current_otp,
                    "callback_speech": callback_speech,
                    "order_qty": sm.order_qty,
                    "logs": database.get_order_logs(sm.client_id)
                })
            except Exception as e:
                self.send_json_response(500, {"status": "error", "message": str(e)})

        else:
            self.send_json_response(404, {"error": f"API POST endpoint {path} not found"})

    def serve_static_file(self, path):
        # Prevent Directory Traversal
        sanitized_path = os.path.normpath(path.lstrip("/"))
        file_path = os.path.join(STATIC_DIR, sanitized_path)

        if not file_path.startswith(STATIC_DIR) or not os.path.exists(file_path) or os.path.isdir(file_path):
            # SPA Fallback
            file_path = os.path.join(STATIC_DIR, "index.html")
            if not os.path.exists(file_path):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 - Not Found")
                return

        # Determine MIME Type
        mime_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".ico": "image/x-icon",
            ".svg": "image/svg+xml"
        }
        _, ext = os.path.splitext(file_path)
        content_type = mime_types.get(ext.lower(), "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"500 - Internal Server Error: {e}".encode("utf-8"))

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def start_server():
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("", PORT)
    httpd = ThreadingHTTPServer(server_address, BackofficeHTTPRequestHandler)
    print("="*80)
    print(f"🎨 WEB DASHBOARD SERVER RUNNING AT: http://localhost:{PORT}")
    print(f"📊 MS SQL Connection: {mssql_integration.get_connection_status()['status']}")
    print(f"🎙️ Local Audio Pipeline ready to simulate interactive calls...")
    print("="*80)
    print("👉 Press [Ctrl+C] to stop the server.")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Web Dashboard server stopped gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    start_server()
