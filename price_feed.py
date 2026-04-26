"""
Sumber data harga real-time dari Binance public WebSocket.
Gratis, nggak perlu API key, latency rendah (cocok buat market 1-menit).
"""

import asyncio
import json
import logging
from collections import deque
import websockets

log = logging.getLogger(__name__)


class BinancePriceFeed:
    def __init__(self, symbol: str, history_size: int = 300):
        self.symbol = symbol.lower()
        self.url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"
        # Simpan harga terakhir N detik (rolling window)
        self.history: deque = deque(maxlen=history_size)
        self.latest_price: float | None = None

    async def run(self):
        """Connect & stream harga selamanya. Auto-reconnect kalau putus."""
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    log.info("Connected to Binance %s feed", self.symbol)
                    async for raw in ws:
                        msg = json.loads(raw)
                        price = float(msg["p"])
                        ts = int(msg["T"])
                        self.latest_price = price
                        self.history.append((ts, price))
            except Exception as e:
                log.warning("Binance WS disconnected: %s. Reconnecting in 3s", e)
                await asyncio.sleep(3)

    def momentum(self, window: int) -> float | None:
        """
        Return persentase perubahan harga di window N data terakhir.
        Positif = naik, negatif = turun.
        """
        if len(self.history) < window:
            return None
        old_price = self.history[-window][1]
        new_price = self.history[-1][1]
        return (new_price - old_price) / old_price
