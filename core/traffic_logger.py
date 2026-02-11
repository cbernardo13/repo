import sqlite3
import os
import logging
from datetime import datetime
from threading import Lock

logger = logging.getLogger("traffic_logger")

class TrafficLogger:
    def __init__(self, db_path="traffic.db"):
        self.db_path = db_path
        self.lock = Lock()
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create the table if it doesn't exist."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS traffic (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        prompt TEXT,
                        response TEXT,
                        provider TEXT,
                        model TEXT,
                        latency REAL,
                        status TEXT,
                        tokens_in INTEGER DEFAULT 0,
                        tokens_out INTEGER DEFAULT 0,
                        cost REAL DEFAULT 0.0,
                        channel TEXT DEFAULT 'unknown'
                    )
                ''')
                
                # Simple migration check: see if 'channel' column exists
                try:
                    cursor.execute('SELECT channel FROM traffic LIMIT 1')
                except sqlite3.OperationalError:
                    # Column likely missing, add it
                    logger.info("Migrating traffic table: adding 'channel' column")
                    cursor.execute('ALTER TABLE traffic ADD COLUMN channel TEXT DEFAULT "unknown"')
                    
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize traffic database: {e}")

    def log_traffic(self, prompt, response, provider, model, latency, status="success", tokens_in=0, tokens_out=0, cost=0.0, channel="unknown"):
        """Logs a traffic event to the database."""
        try:
            timestamp = datetime.now().isoformat()
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO traffic (timestamp, prompt, response, provider, model, latency, status, tokens_in, tokens_out, cost, channel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, prompt, response, provider, model, latency, status, tokens_in, tokens_out, cost, channel))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Failed to log traffic: {e}")

    def get_recent_traffic(self, limit=50, offset=0):
        """Retrieves recent traffic logs."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM traffic ORDER BY id DESC LIMIT ? OFFSET ?
                ''', (limit, offset))
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to retrieve traffic logs: {e}")
            return []

    def get_stats(self, days=7):
        """Retrieves aggregated statistics for the last N days."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Total Requests
                cursor.execute('SELECT COUNT(*) as count FROM traffic')
                total_requests = cursor.fetchone()['count']
                
                # Provider Distribution
                cursor.execute('''
                    SELECT provider, COUNT(*) as count 
                    FROM traffic 
                    GROUP BY provider
                ''')
                provider_stats = [dict(row) for row in cursor.fetchall()]
                
                # Cost per Provider
                cursor.execute('''
                    SELECT provider, SUM(cost) as total_cost 
                    FROM traffic 
                    GROUP BY provider
                ''')
                cost_stats = [dict(row) for row in cursor.fetchall()]

                # Requests per day (last N days)
                # Note: SQLite 'date' function might vary, assuming ISO8601 strings
                cursor.execute(f'''
                    SELECT date(timestamp) as day, COUNT(*) as count
                    FROM traffic
                    WHERE timestamp >= date('now', '-{days} days')
                    GROUP BY day
                    ORDER BY day ASC
                ''')
                daily_stats = [dict(row) for row in cursor.fetchall()]

                conn.close()
                
                return {
                    "total_requests": total_requests,
                    "provider_distribution": provider_stats,
                    "cost_distribution": cost_stats,
                    "daily_requests": daily_stats
                }
        except Exception as e:
            logger.error(f"Failed to retrieve traffic stats: {e}")
            return {}
