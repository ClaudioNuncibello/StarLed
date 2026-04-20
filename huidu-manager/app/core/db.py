import sqlite3
import os
from datetime import datetime
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestore del database SQLite locale di SLPlayer.
    
    Tabella principale:
    - uploaded_files: memorizza i file media caricati sui vari dispositivi per evitare duplication check md5.
    """
    
    def __init__(self, db_path: str = "slplayer.db"):
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Inizializza le tabelle se non esistono."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS uploaded_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        md5 TEXT NOT NULL,
                        size INTEGER NOT NULL,
                        type TEXT NOT NULL,
                        uploaded_at TEXT NOT NULL
                    )
                """)
                # Indice per ricerca rapida duplicati
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_uploaded_md5_device 
                    ON uploaded_files (md5, device_id)
                """)
                conn.commit()
            logger.info(f"Database {self.db_path} inizializzato correttamente.")
        except Exception as e:
            logger.error(f"Impossibile inizializzare db SQLite: {str(e)}")

    def file_already_on_device(self, md5: str, device_id: str) -> Optional[Dict[str, Any]]:
        """Ritorna il record DB (es. nome file, size) se il file è già stato caricato."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM uploaded_files WHERE md5=? AND device_id=?", 
                    (md5, device_id)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Errore lettura record {md5}: {e}")
            return None

    def insert_uploaded_file(self, device_id: str, name: str, md5: str, size: int, file_type: str) -> bool:
        """Inserisce o aggiorna un file caricato su un determinato device_id."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Controllo eventuale inserimento se non è pre-esistente lo stesso identico MD5 (altrimenti duplica lo storico)
                cursor.execute(
                    "SELECT id FROM uploaded_files WHERE md5=? AND device_id=?", 
                    (md5, device_id)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Rinnova il timestamp e possibilmente il nome se è sovrascritto
                    cursor.execute("""
                        UPDATE uploaded_files 
                        SET uploaded_at=?, name=?, size=?, type=? 
                        WHERE id=?
                    """, (datetime.now().isoformat(), name, size, file_type, existing['id']))
                else:
                    cursor.execute("""
                        INSERT INTO uploaded_files (device_id, name, md5, size, type, uploaded_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (device_id, name, md5, size, file_type, datetime.now().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Errore scrittura storico per {name}: {e}")
            return False
