"""Generatore payload e gestione stato programmi Huidu."""
import logging
import copy
import json
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def time_str_to_sec(t_str: str) -> int:
    """Converte 'HH:MM:SS' in secondi."""
    parts = t_str.split(':')
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    s = int(parts[2]) if len(parts) > 2 else 0
    return h * 3600 + m * 60 + s

def sec_to_time_str(sec: int) -> str:
    """Converte secondi in 'HH:MM:SS'."""
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def merge_intervals(intervals: List[tuple]) -> List[tuple]:
    """Unisce intervalli temporali sovrapposti."""
    if not intervals: return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def get_free_intervals(occupied: List[tuple]) -> List[tuple]:
    """Calcola gli intervalli liberi nella giornata (0-86399)."""
    free = []
    current_start = 0
    for occ in occupied:
        if occ[0] > current_start:
            free.append((current_start, occ[0] - 1))
        current_start = max(current_start, occ[1] + 1)
    if current_start <= 86399:
        free.append((current_start, 86399))
    return free

def generate_payload(
    cache_programs: Dict[str, Dict[str, Any]],
    action: str,
    target_uuid: str = None
) -> List[Dict[str, Any]]:
    """Genera il payload data per la chiamata API method=replace."""
    payload_programs = []
    
    if action == "manda_live":
        if target_uuid and target_uuid in cache_programs:
            cache_programs[target_uuid]["status"] = "live"
            
        # Per mantenere l'esclusività tra modalità, disabilitiamo i programmati
        for uid, p in cache_programs.items():
            if p.get("status") == "programmed":
                p["status"] = "disabled"
                p["playControl"] = None
                
        # Ritorna tutte le live (che si alterneranno sul controller)
        payload_programs = [p for p in cache_programs.values() if p.get("status") == "live"]
        
    elif action == "disabilita":
        if target_uuid and target_uuid in cache_programs:
            cache_programs[target_uuid]["status"] = "disabled"
            
        # Ritorna le restanti live o programmate
        # Se eravamo in live, restituisce le live. Se in palinsesto, restituisce le programmed.
        payload_programs = [p for p in cache_programs.values() if p.get("status") in ("live", "programmed")]

    elif action == "svuota_schermo":
        # Disabilita tutto
        for p in cache_programs.values():
            p["status"] = "disabled"
            p["playControl"] = None
        # Ritorna vuoto
        payload_programs = []
        
    elif action == "push_palinsesto":
        # Tutto ciò che non ha un playControl valido (es. le live) viene disabilitato
        for uid, p in cache_programs.items():
            if p.get("playControl") is None:
                p["status"] = "disabled"
            else:
                p["status"] = "programmed"
                
        payload_programs = [p for p in cache_programs.values() if p.get("status") == "programmed"]
        
    elif action == "sincronizza":
        # Invia lo stato corrente: se c'è almeno una live manda quelle, altrimenti le programmed
        has_live = any(p.get("status") == "live" for p in cache_programs.values())
        if has_live:
            payload_programs = [p for p in cache_programs.values() if p.get("status") == "live"]
        else:
            payload_programs = [p for p in cache_programs.values() if p.get("status") == "programmed"]
        
    else:
        raise ValueError(f"Azione non supportata: {action}")
        
    return payload_programs
