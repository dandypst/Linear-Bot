"""
Client untuk berkomunikasi dengan Linera node service via GraphQL.

Bot kamu nggak login ke web Linera Markets sama sekali. Sebagai gantinya,
`linera service` di-jalanin lokal (port 8080) sebagai jembatan ke chain.
Tx di-sign otomatis oleh node service pakai wallet kamu.
"""

import json
import logging
import requests

log = logging.getLogger(__name__)


class LineraClient:
    def __init__(self, node_url: str, chain_id: str, application_id: str):
        self.node_url = node_url.rstrip("/")
        self.chain_id = chain_id
        self.application_id = application_id
        self.app_endpoint = (
            f"{self.node_url}/chains/{chain_id}/applications/{application_id}"
        )

    def _post(self, endpoint: str, query: str, variables: dict | None = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        try:
            r = requests.post(endpoint, json=payload, timeout=10)
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                log.error("GraphQL errors: %s", data["errors"])
            return data
        except requests.RequestException as e:
            log.error("HTTP error to %s: %s", endpoint, e)
            return {"errors": [str(e)]}

    # ---------- Query umum ke chain ----------

    def get_balance(self) -> dict:
        """Cek balance microchain kamu."""
        query = """
        query Balance($chainId: ChainId!) {
          chain(chainId: $chainId) {
            executionState {
              system {
                balance
              }
            }
          }
        }
        """
        return self._post(
            self.node_url, query, {"chainId": self.chain_id}
        )

    def list_applications(self) -> dict:
        """List semua aplikasi yang sudah deployed di chain kamu."""
        query = """
        query Apps($chainId: ChainId!) {
          applications(chainId: $chainId) {
            id
            description
            link
          }
        }
        """
        return self._post(self.node_url, query, {"chainId": self.chain_id})

    # ---------- Interaksi ke Linera Markets ----------
    # PENTING: nama mutation di bawah cuma PLACEHOLDER. Schema asli Linera
    # Markets harus kamu cek sendiri lewat GraphiQL di:
    #   http://localhost:8080/chains/{CHAIN_ID}/applications/{APP_ID}
    # Lihat tab "Docs" di pojok kanan atas GraphiQL — itu schema lengkap
    # dari aplikasi.

    def get_current_round(self, market_symbol: str, duration_sec: int) -> dict:
        """Ambil info round market yang sedang aktif (placeholder query)."""
        query = """
        query CurrentRound($symbol: String!, $duration: Int!) {
          currentRound(symbol: $symbol, duration: $duration) {
            id
            openPrice
            opensAt
            locksAt
            resolvesAt
            poolUp
            poolDown
          }
        }
        """
        return self._post(
            self.app_endpoint,
            query,
            {"symbol": market_symbol, "duration": duration_sec},
        )

    def place_bet(
        self, round_id: str, direction: str, amount: int
    ) -> dict:
        """
        Submit prediksi UP atau DOWN untuk round tertentu.

        direction: "UP" atau "DOWN"
        amount: jumlah token GMIC

        NOTE: Ganti nama mutation `placeBet` ini dengan nama yang sebenernya
        ada di schema Linera Markets. Cek di GraphiQL.
        """
        mutation = """
        mutation PlaceBet($roundId: ID!, $direction: Direction!, $amount: Int!) {
          placeBet(roundId: $roundId, direction: $direction, amount: $amount)
        }
        """
        return self._post(
            self.app_endpoint,
            mutation,
            {"roundId": round_id, "direction": direction, "amount": amount},
        )

    def get_my_history(self, limit: int = 20) -> dict:
        """Ambil riwayat bet kamu (placeholder)."""
        query = """
        query MyHistory($limit: Int!) {
          myBets(limit: $limit) {
            roundId
            direction
            amount
            outcome
            payout
          }
        }
        """
        return self._post(self.app_endpoint, query, {"limit": limit})
