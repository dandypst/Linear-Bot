"""
Main loop bot trading Linera Markets.

Cara jalanin:
    python bot.py --dry-run     # tes dulu, nggak submit tx beneran
    python bot.py               # mode live (submit ke chain)

Pastiin SEBELUM jalanin:
1. `linera service --port 8080` udah jalan di terminal lain
2. .env udah diisi (CHAIN_ID, APPLICATION_ID, dll)
3. Tim Linera udah konfirmasi bot diizinkan di testnet kompetisi
"""

import argparse
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

from linera_client import LineraClient
from price_feed import BinancePriceFeed
from strategy import MomentumStrategy
from risk_manager import RiskManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bot")


async def trading_loop(
    client: LineraClient,
    feed: BinancePriceFeed,
    strategy: MomentumStrategy,
    risk: RiskManager,
    symbol: str,
    duration: int,
    bet_amount: int,
    dry_run: bool,
):
    """Loop utama: tiap ronde baru, generate sinyal, place bet kalau valid."""
    last_round_id = None

    while True:
        try:
            # 1. Cek ronde aktif sekarang di Linera Markets
            round_data = client.get_current_round(symbol.upper(), duration)
            current_round = round_data.get("data", {}).get("currentRound")

            if not current_round:
                log.debug("Belum ada ronde aktif, tunggu 2 detik")
                await asyncio.sleep(2)
                continue

            round_id = current_round["id"]

            # 2. Skip kalau ronde ini udah pernah di-bet
            if round_id == last_round_id:
                await asyncio.sleep(1)
                continue

            # 3. Cek waktu kunci ronde — kita bet T-3 detik sebelum lock
            locks_at = current_round.get("locksAt")
            # NOTE: format waktu (epoch ms vs detik) tergantung schema asli.
            # Sesuaikan kalau perlu.

            # 4. Cek risk
            ok, reason = risk.can_bet()
            if not ok:
                log.warning("Skip bet: %s", reason)
                await asyncio.sleep(5)
                continue

            # 5. Generate sinyal dari momentum
            signal = strategy.decide(feed)
            if signal is None:
                log.info("Sinyal lemah, skip ronde %s", round_id)
                last_round_id = round_id
                await asyncio.sleep(2)
                continue

            # 6. Submit bet
            log.info("📈 Sinyal %s untuk ronde %s, amount %d",
                     signal, round_id, bet_amount)
            if dry_run:
                log.info("[DRY-RUN] Skip submit ke chain")
            else:
                result = client.place_bet(round_id, signal, bet_amount)
                if "errors" in result:
                    log.error("Bet gagal: %s", result["errors"])
                else:
                    log.info("✅ Bet di-submit: %s", result)
                    risk.record_bet()

            last_round_id = round_id
            await asyncio.sleep(2)

        except Exception as e:
            log.exception("Error di trading loop: %s", e)
            await asyncio.sleep(5)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Jangan submit tx beneran, cuma log sinyal")
    args = parser.parse_args()

    load_dotenv()
    node_url = os.getenv("LINERA_NODE_URL", "http://localhost:8080")
    chain_id = os.getenv("CHAIN_ID")
    app_id = os.getenv("APPLICATION_ID")
    symbol = os.getenv("SYMBOL", "btcusdt")
    duration = int(os.getenv("ROUND_DURATION", "60"))
    bet_amount = int(os.getenv("BET_AMOUNT", "10"))
    momentum_window = int(os.getenv("MOMENTUM_WINDOW", "20"))
    momentum_threshold = float(os.getenv("MOMENTUM_THRESHOLD", "0.0005"))
    max_losses = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "5"))
    max_per_hour = int(os.getenv("MAX_BETS_PER_HOUR", "20"))

    if not chain_id or not app_id:
        log.error("CHAIN_ID dan APPLICATION_ID wajib diisi di .env")
        sys.exit(1)

    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")
    log.info("Symbol: %s | Round: %ds | Bet: %d GMIC",
             symbol, duration, bet_amount)

    client = LineraClient(node_url, chain_id, app_id)
    feed = BinancePriceFeed(symbol)
    strategy = MomentumStrategy(momentum_window, momentum_threshold)
    risk = RiskManager(max_losses, max_per_hour)

    # Cek konektivitas dulu
    bal = client.get_balance()
    log.info("Balance check: %s", bal)

    # Jalanin price feed & trading loop secara concurrent
    await asyncio.gather(
        feed.run(),
        trading_loop(client, feed, strategy, risk,
                     symbol, duration, bet_amount, args.dry_run),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot di-stop oleh user")
