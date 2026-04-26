# Linera Markets Auto-Trading Bot (Starter)

Bot otomatis untuk Linera Markets testnet, ngumpulin Portal Points lewat trading prediction market jangka pendek (1/3/5 menit).

> **Disclaimer**: Ini buat eksperimen di testnet (token GMIC, bukan uang asli). Strategi sederhana di sini bukan strategi yang dijamin profit. Sebelum berharap menang leaderboard, kamu HARUS:
> 1. Konfirmasi ke tim Linera (Discord/Telegram) bahwa **bot/automation diizinkan** di testnet kompetisi. Kalau dilarang, Portal Points kamu bisa dianulir.
> 2. Pelajari strategi yang sebenarnya, bukan asal pakai contoh ini.

---

## Arsitektur

```
Binance WebSocket (data harga real-time)
        ↓
Strategi Python (sinyal UP/DOWN)
        ↓
Linera Node Service (lokal, GraphQL endpoint di localhost:8080)
        ↓
Linera Markets Application (di on-chain microchain kamu)
```

Bot **tidak login lewat web/email**. Otentikasi pakai wallet lokal Linera, tx di-sign otomatis oleh node service.

---

## Tahap 1 — Install software dasar

### Linux (Ubuntu/Debian)

```bash
# Tools dasar
sudo apt update
sudo apt install -y build-essential pkg-config libssl-dev curl git python3 python3-pip

# Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Linera CLI dari crates.io
cargo install --locked linera-storage-service
cargo install --locked linera-service

# Verifikasi
linera --version
```

### macOS

```bash
# Pakai Homebrew
brew install rust python git
cargo install --locked linera-storage-service
cargo install --locked linera-service
```

### Windows

Pakai WSL2 (Ubuntu) — Linera CLI nggak native di Windows.

---

## Tahap 2 — Setup wallet testnet

Cek dulu **nama testnet phase yang aktif sekarang** di https://linera.dev atau Discord Linera. Ganti `XXX` di bawah dengan nama yang aktif (contoh sebelumnya: `conway`, `babbage`, `archimedes`).

```bash
# Set lokasi wallet
export LINERA_TMP_DIR=$HOME/.linera-bot
mkdir -p $LINERA_TMP_DIR
export LINERA_WALLET="$LINERA_TMP_DIR/wallet.json"
export LINERA_KEYSTORE="$LINERA_TMP_DIR/keystore.json"
export LINERA_STORAGE="rocksdb:$LINERA_TMP_DIR/client.db"

# Faucet URL testnet aktif (CEK DULU NAMA YANG TERBARU!)
export FAUCET_URL=https://faucet.testnet-XXX.linera.net

# Init wallet & klaim microchain dengan token testnet
linera wallet init --faucet $FAUCET_URL
linera wallet request-chain --faucet $FAUCET_URL

# Lihat wallet & chain ID kamu
linera wallet show

# Cek balance
linera query-balance
```

Catat **Chain ID** kamu — bot perlu ini.

> Tambahin `export LINERA_*` di `~/.bashrc` atau `~/.zshrc` biar persistent.

---

## Tahap 3 — Jalankan node service (GraphQL endpoint)

Bot perlu Linera node yang jalan terus di background sebagai jembatan ke chain:

```bash
linera service --port 8080
```

Ini bakal expose GraphQL endpoint di `http://localhost:8080`. Biarin terminal ini terbuka, atau pakai `tmux`/`screen`/`systemd` buat 24/7.

Tes dengan buka browser ke `http://localhost:8080` — kamu harusnya liat GraphiQL UI.

---

## Tahap 4 — Cari Application ID Linera Markets

Ini bagian yang harus dicari sendiri, karena Linera Markets app ID nggak ditarok di doc publik:

1. Tanya di Discord/Telegram Linera: "What's the Application ID for Linera Markets on the current testnet?"
2. Atau, kalau kamu udah dikasih akses testnet & bisa lihat aplikasinya di chain kamu, query lewat GraphiQL:
   ```graphql
   query {
     applications(chainId: "CHAIN_ID_KAMU") {
       id
       description
       link
     }
   }
   ```
3. Cek juga schema mutation yang tersedia (bid, predict, dll) di GraphiQL — schema-nya self-documenting.

Simpan Application ID di `.env`.

---

## Tahap 5 — Setup Python bot

```bash
cd linera-bot
pip install -r requirements.txt
cp .env.example .env
# Edit .env, isi CHAIN_ID dan APPLICATION_ID kamu
```

Jalankan bot:

```bash
python bot.py
```

Karena ini testnet (token GMIC, bukan uang asli), nggak perlu dry-run. Tapi tetap bijak: mulai dengan `BET_AMOUNT` kecil di `.env` dulu, monitor beberapa ronde, baru naikkan kalau strategi kelihatan masuk akal.

---

## Yang harus kamu sesuaikan sendiri

1. **Mutation GraphQL di `linera_client.py`** — placeholder `placeBet` di kode aku itu bukan mutation asli Linera Markets. Kamu wajib cari nama mutation yang benar dari schema GraphiQL (kemungkinan: `predict`, `bet`, `submitPrediction`, dll).
2. **Strategi di `strategy.py`** — yang aku kasih cuma momentum sederhana. Ganti dengan strategi yang kamu yakin punya edge.
3. **Risk management** — kasih limit max loss per jam, max consecutive loss, dll. JANGAN bot lepas tanpa pengaman.

---

## Resource

- Dokumentasi resmi: https://linera.dev
- Discord Linera: https://discord.gg/linera
- Telegram Linera: https://t.me/linera_official
- GitHub Linera Protocol: https://github.com/linera-io/linera-protocol
- Contoh aplikasi Rust SDK: https://github.com/linera-io/linera-protocol/tree/main/examples
