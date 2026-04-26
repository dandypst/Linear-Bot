"""
Risk management. Wajib dipake. Bot tanpa pengaman = bot bunuh diri.
"""

import logging
import time
from collections import deque

log = logging.getLogger(__name__)


class RiskManager:
    def __init__(
        self,
        max_consecutive_losses: int,
        max_bets_per_hour: int,
    ):
        self.max_consecutive_losses = max_consecutive_losses
        self.max_bets_per_hour = max_bets_per_hour
        self.consecutive_losses = 0
        self.bet_timestamps: deque = deque()
        self.halted = False

    def can_bet(self) -> tuple[bool, str]:
        if self.halted:
            return False, "Bot di-halt karena consecutive loss limit"

        # Bersihin timestamp lebih dari 1 jam
        cutoff = time.time() - 3600
        while self.bet_timestamps and self.bet_timestamps[0] < cutoff:
            self.bet_timestamps.popleft()

        if len(self.bet_timestamps) >= self.max_bets_per_hour:
            return False, f"Hit batas {self.max_bets_per_hour} bet/jam"

        return True, "ok"

    def record_bet(self):
        self.bet_timestamps.append(time.time())

    def record_outcome(self, won: bool):
        if won:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            log.warning("Consecutive loss: %d", self.consecutive_losses)
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.halted = True
                log.error("BOT DI-HALT: hit %d consecutive losses",
                          self.consecutive_losses)
