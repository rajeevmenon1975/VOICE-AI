import os
import sqlite3
import time
from datetime import datetime

# Try importing pyodbc for real MS SQL Server connectivity
try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trader.db")

class MSSQLEmulator:
    """
    High-fidelity MS SQL database emulator powered by the local SQLite database.
    It maps SQLite results and returns MS SQL styled metadata (e.g. connection speeds,
    server information, and dialect formatting) for the Backoffice console.
    """
    def __init__(self):
        self.server = "127.0.0.1\\SQLEXPRESS"
        self.database = "BrokerLedgerDB"
        self.status = "CONNECTED (Simulated Sandbox)"
        self.connection_time_ms = 14.5

    def get_connection(self):
        # Maps local SQLite for simulation
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def run_query(self, query: str):
        """Executes a SQL query in the local SQLite engine simulating MS SQL behavior."""
        start_time = time.time()
        conn = self.get_connection()
        cursor = conn.cursor()

        # Clean/adapt MS SQL query syntax slightly to SQLite standard (e.g. dbo. prefix)
        clean_query = query.replace("dbo.", "").replace("[", "").replace("]", "")

        try:
            cursor.execute(clean_query)
            if clean_query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                results = [dict(r) for r in rows]
            else:
                conn.commit()
                results = {"rows_affected": cursor.rowcount}
                columns = ["rows_affected"]

            error = None
        except Exception as e:
            results = None
            columns = None
            error = str(e)
        finally:
            conn.close()

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "success": error is None,
            "results": results,
            "columns": columns,
            "error": error,
            "elapsed_ms": round(elapsed_ms, 2),
            "server": self.server,
            "database": self.database,
            "driver": "ODBC Driver 18 for SQL Server (Simulated)"
        }

class RealMSSQLConnector:
    """
    Production-grade MS SQL connector class using pyodbc.
    It connects to a real MS SQL instance if connection details are provided.
    """
    def __init__(self, server, database, username, password, port=1433, encrypt=True):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.port = port
        self.encrypt = "yes" if encrypt else "no"
        self.status = "DISCONNECTED"

    def run_query(self, query: str):
        if not HAS_PYODBC:
            return {
                "success": False,
                "error": "pyodbc module is not installed in the local environment.",
                "elapsed_ms": 0,
                "server": self.server
            }

        start_time = time.time()
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt={self.encrypt};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )

        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
            else:
                conn.commit()
                results = {"rows_affected": cursor.rowcount}
                columns = ["rows_affected"]

            error = None
            conn.close()
        except Exception as e:
            results = None
            columns = None
            error = str(e)

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "success": error is None,
            "results": results,
            "columns": columns,
            "error": error,
            "elapsed_ms": round(elapsed_ms, 2),
            "server": self.server,
            "database": self.database,
            "driver": "ODBC Driver 18 for SQL Server"
        }

# Global database manager (defaults to Emulator sandbox)
_db_manager = MSSQLEmulator()

def configure_mssql_connection(server, database, username, password, port=1433, encrypt=True):
    """Sets the active connector to a real MS SQL Server."""
    global _db_manager
    if HAS_PYODBC and server:
        _db_manager = RealMSSQLConnector(server, database, username, password, port, encrypt)
        return {"status": "success", "message": f"Configured real MS SQL Server connection to {server}."}
    else:
        _db_manager = MSSQLEmulator()
        return {
            "status": "warning",
            "message": "pyodbc missing or server details empty. Using high-fidelity local SQLite sandbox instead."
        }

def get_connection_status():
    """Returns the current connection status details."""
    if isinstance(_db_manager, MSSQLEmulator):
        return {
            "mode": "Sandbox Simulator",
            "server": _db_manager.server,
            "database": _db_manager.database,
            "status": "Connected (Sandbox Enabled)",
            "has_pyodbc": HAS_PYODBC
        }
    else:
        return {
            "mode": "Production MS SQL Server",
            "server": _db_manager.server,
            "database": _db_manager.database,
            "status": "Configured",
            "has_pyodbc": HAS_PYODBC
        }

def run_query(query: str):
    """Entrypoint to run SQL query on the active engine."""
    return _db_manager.run_query(query)

def get_behavioral_patterns():
    """
    Computes analytical metrics representing backoffice behavioral patterns of the client ledger:
    - Margin utilization indexes.
    - Transaction frequency metrics.
    - Regional language interaction metrics.
    - Segment concentrations.
    """
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate statistics from standard SQLite schemas to model behaviors
    try:
        # 1. Total ledger balance by client
        cursor.execute("SELECT client_id, name, ledger_balance, preferred_lang, activated_segments FROM clients")
        clients = [dict(r) for r in cursor.fetchall()]

        # 2. Segment distributions
        segment_counts = {"EQUITY": 0, "F&O": 0}
        lang_counts = {}
        for c in clients:
            # Language
            lang = c["preferred_lang"]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            # Segments
            segs = [s.strip().upper() for s in c["activated_segments"].split(",")]
            for s in segs:
                if s in segment_counts:
                    segment_counts[s] += 1

        # 3. Aggregated order stats for trade behaviors
        cursor.execute("""
            SELECT client_id, symbol, action, quantity, price, status, rejection_reason 
            FROM order_logs
        """)
        orders = [dict(r) for r in cursor.fetchall()]

        # Calculate penny stock vs standard stock transaction frequency
        penny_trades = 0
        standard_trades = 0
        rejected_trades = 0
        completed_trades = 0

        for o in orders:
            # Rejections
            if o["status"] == "REJECTED":
                rejected_trades += 1
            else:
                completed_trades += 1

            # Penny stock detection (e.g. IDEA, GTLINFRA, or price < 20)
            if o["symbol"] in ["IDEA", "GTLINFRA"] or o["price"] < 20:
                penny_trades += 1
            else:
                standard_trades += 1

        # Calculate average margin usage based on client balances
        # Priya Sharma: low balance (high utilization risk)
        # Rajeev Menon: high balance (low utilization risk)
        behavioral_data = {
            "clients": clients,
            "metrics": {
                "total_ledger_value": sum(c["ledger_balance"] for c in clients),
                "avg_ledger_balance": sum(c["ledger_balance"] for c in clients) / max(len(clients), 1),
                "penny_stock_trades_count": penny_trades,
                "standard_stock_trades_count": standard_trades,
                "rejection_rate_percentage": round((rejected_trades / max(len(orders), 1)) * 100, 2),
                "completion_rate_percentage": round((completed_trades / max(len(orders), 1)) * 100, 2),
            },
            "distributions": {
                "languages": lang_counts,
                "segments": segment_counts
            }
        }
    except Exception as e:
        behavioral_data = {"error": str(e)}
    finally:
        conn.close()

    return behavioral_data
