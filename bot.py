import requests
import time
from datetime import datetime

API = "https://api.dexscreener.com/token-profiles/latest/v1"

def buscar_tokens():
    try:
        resposta = requests.get(API, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        print("Erro:", e)
        return []

def analisar(token):
    chain = token.get("chainId", "")
    address = token.get("tokenAddress", "")
    url = token.get("url", "")

    if chain != "solana":
        return

    print("\n" + "=" * 45)
    print("NOVO TOKEN SOLANA")
    print("Hora:", datetime.now().strftime("%H:%M:%S"))
    print("Contrato:", address)
    print("DEX:", url)
    print("STATUS: PARA INVESTIGAÇÃO")
    print("MODO: SIMULAÇÃO")
    print("=" * 45)

print("🚀 SOLANA MEME RADAR INICIADO")
print("Modo SIMULAÇÃO — nenhuma compra será realizada.")

while True:
    tokens = buscar_tokens()

    for token in tokens:
        analisar(token)

    print("\nPróxima verificação em 30 segundos...")
    time.sleep(30)
