import requests
import time
from datetime import datetime

DEX_API = "https://api.dexscreener.com/token-profiles/latest/v1"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

# ===== CONFIGURAÇÃO =====
MIN_LIQUIDITY = 5000
MIN_VOLUME_24H = 10000
MIN_TXNS_24H = 50
CHECK_EVERY = 30

seen = set()


def get_new_tokens():
    try:
        r = requests.get(DEX_API, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Erro ao buscar tokens:", e)
        return []


def rpc(method, params):
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        r = requests.post(
            SOLANA_RPC,
            json=payload,
            timeout=10
        )

        return r.json().get("result")

    except Exception:
        return None


def get_top_holders(mint):
    result = rpc(
        "getTokenLargestAccounts",
        [mint, {"commitment": "finalized"}]
    )

    if not result:
        return []

    return result.get("value", [])


def holder_score(mint):
    holders = get_top_holders(mint)

    if not holders:
        return 0

    amounts = []

    for holder in holders:
        try:
            amounts.append(float(holder["uiAmount"]))
        except:
            pass

    if not amounts:
        return 0

    total = sum(amounts)

    if total <= 0:
        return 0

    top5 = sum(amounts[:5])
    concentration = (top5 / total) * 100

    # Quanto menor a concentração, melhor
    if concentration < 25:
        return 20

    if concentration < 40:
        return 15

    if concentration < 55:
        return 10

    if concentration < 70:
        return 5

    return 0


def calculate_score(liquidity, volume, txns, holder_points):

    score = 0

    # Liquidez
    if liquidity >= 50000:
        score += 25
    elif liquidity >= 20000:
        score += 20
    elif liquidity >= 10000:
        score += 15
    elif liquidity >= MIN_LIQUIDITY:
        score += 10

    # Volume
    if volume >= 100000:
        score += 25
    elif volume >= 50000:
        score += 20
    elif volume >= 20000:
        score += 15
    elif volume >= MIN_VOLUME_24H:
        score += 10

    # Transações
    if txns >= 1000:
        score += 20
    elif txns >= 500:
        score += 15
    elif txns >= 100:
        score += 10
    elif txns >= MIN_TXNS_24H:
        score += 5

    # Distribuição
    score += holder_points

    return min(score, 100)


def analyze_token(token):

    if token.get("chainId") != "solana":
        return

    mint = token.get("tokenAddress")

    if not mint or mint in seen:
        return

    seen.add(mint)

    url = token.get("url", "")

    print("\n" + "=" * 60)
    print("🔎 NOVO TOKEN SOLANA")
    print("Hora:", datetime.now().strftime("%H:%M:%S"))
    print("Mint:", mint)
    print("DEX:", url)

    # Procuramos o par no DEX Screener
    try:
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
            timeout=10
        )

        data = response.json()
        pairs = data.get("pairs") or []

    except Exception:
        pairs = []

    if not pairs:
        print("Sem mercado encontrado ainda.")
        print("=" * 60)
        return

    # Escolhe o par Solana com maior liquidez
    sol_pairs = [
        p for p in pairs
        if p.get("chainId") == "solana"
    ]

    if not sol_pairs:
        return

    pair = max(
        sol_pairs,
        key=lambda x: float(
            (x.get("liquidity") or {}).get("usd") or 0
        )
    )

    liquidity = float(
        (pair.get("liquidity") or {}).get("usd") or 0
    )

    volume = float(
        (pair.get("volume") or {}).get("h24") or 0
    )

    txns_data = pair.get("txns") or {}
    h24 = txns_data.get("h24") or {}

    buys = int(h24.get("buys") or 0)
    sells = int(h24.get("sells") or 0)

    txns = buys + sells

    price = pair.get("priceUsd") or "0"
    market_cap = pair.get("marketCap") or pair.get("fdv") or 0

    holder_points = holder_score(mint)

    score = calculate_score(
        liquidity,
        volume,
        txns,
        holder_points
    )

    print(f"💧 Liquidez: ${liquidity:,.0f}")
    print(f"📊 Volume 24h: ${volume:,.0f}")
    print(f"🟢 Compras 24h: {buys}")
    print(f"🔴 Vendas 24h: {sells}")
    print(f"🔄 Transações: {txns}")
    print(f"💰 Market Cap: ${float(market_cap):,.0f}")
    print(f"💵 Preço: ${price}")
    print(f"👥 Distribuição: +{holder_points} pontos")
    print("-" * 60)

    if score >= 80:
        status = "🔥 FORTE SINAL — INVESTIGAR"
    elif score >= 60:
        status = "🟡 ATENÇÃO"
    elif score >= 40:
        status = "⚪ FRACO"
    else:
        status = "🔴 DESCARTAR"

    print(f"⭐ SCORE: {score}/100")
    print("STATUS:", status)
    print("MODO: SIMULAÇÃO")
    print("=" * 60)


print()
print("🚀 SOLANA MEME RADAR V2")
print("🧪 MODO SIMULAÇÃO")
print("💰 NENHUMA COMPRA SERÁ REALIZADA")
print()

while True:

    tokens = get_new_tokens()

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"Tokens analisados: {len(tokens)}"
    )

    for token in tokens:
        analyze_token(token)

    print(
        f"⏳ Próxima análise em {CHECK_EVERY} segundos..."
    )

    time.sleep(CHECK_EVERY)
