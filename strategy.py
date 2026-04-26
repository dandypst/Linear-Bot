"""
Strategi sederhana: momentum follower.

Asumsi: kalau harga BTC/ETH/SOL bergerak kuat di N detik terakhir,
kemungkinan akan lanjut bergerak ke arah yang sama dalam 1 menit.

INI BUKAN STRATEGI YANG DIJAMIN PROFIT. Cuma starter buat kamu modifikasi.
Strategi nyata yang berhasil di prediction market 1-menit biasanya pakai:
- Order book imbalance dari beberapa exchange
- Funding rate divergence
- Volume profile
- Market microstructure signals

Ganti `decide()` di bawah dengan logika yang kamu yakin punya edge.
"""

import logging

log = logging.getLogger(__name__)


class MomentumStrategy:
    def __init__(self, window: int, threshold: float):
        """
        window: jumlah data poin terakhir buat hitung momentum
        threshold: persentase minimum (mis. 0.0005 = 0.05%) buat anggap sinyal valid
        """
        self.window = window
        self.threshold = threshold

    def decide(self, price_feed) -> str | None:
        """
        Return "UP", "DOWN", atau None (skip ronde ini).
        """
        m = price_feed.momentum(self.window)
        if m is None:
            log.debug("Belum cukup data buat hitung momentum")
            return None
        log.info("Momentum %s detik: %.4f%%", self.window, m * 100)
        if m > self.threshold:
            return "UP"
        if m < -self.threshold:
            return "DOWN"
        return None  # momentum lemah, skip
