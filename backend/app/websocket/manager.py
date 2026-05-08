import json
from typing import Dict, List, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbols: List[str]):
        await websocket.accept()
        for symbol in symbols:
            sym = symbol.upper()
            if sym not in self.active_connections:
                self.active_connections[sym] = []
            self.active_connections[sym].append(websocket)

    def disconnect(self, websocket: WebSocket, symbols: List[str]):
        for symbol in symbols:
            sym = symbol.upper()
            if sym in self.active_connections:
                self.active_connections[sym] = [ws for ws in self.active_connections[sym] if ws != websocket]
                if not self.active_connections[sym]:
                    del self.active_connections[sym]

    async def broadcast(self, symbol: str, data: dict):
        sym = symbol.upper()
        if sym not in self.active_connections:
            return
        message = json.dumps(data)
        stale = []
        for ws in self.active_connections[sym]:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.active_connections[sym] = [w for w in self.active_connections[sym] if w != ws]
            if not self.active_connections[sym]:
                del self.active_connections[sym]

    @property
    def tracked_symbols(self) -> Set[str]:
        return set(self.active_connections.keys())


manager = ConnectionManager()
