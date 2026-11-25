# Avisa o Matheus no Telegram dos comentários novos da @joga.mundi (últimos 65 minutos), com o link do jogo.
# Uso: python3 comentarios.py [--ensaio] [--minutos N]. Sem estado: roda de hora em hora. Não imprime segredo.
import datetime, json, os, sys, time, urllib.parse, urllib.request
IG = "17841416017895564"; G = "https://graph.facebook.com/v26.0"
RAW = "https://raw.githubusercontent.com/guidoMath/midia/main/jogos/"
ensaio = "--ensaio" in sys.argv
minutos = int(sys.argv[sys.argv.index("--minutos") + 1]) if "--minutos" in sys.argv else 65
def http(url, dados=None):
    req = urllib.request.Request(url, data=dados, method="POST" if dados else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: return {"erro_http": e.code, "corpo": e.read()[:300].decode(errors="ignore")}
    except Exception as e: return {"erro": str(e)[:200]}
def telegram(msg):
    tg, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if ensaio or not tg or not chat: print("[ENSAIO]\n" + msg); return
    http(f"https://api.telegram.org/bot{tg}/sendMessage", urllib.parse.urlencode({"chat_id": chat, "text": msg, "disable_web_page_preview": "true"}).encode())
links = http(RAW + f"links.json?t={int(time.time())}")
jogos = links.get("jogos", []) if isinstance(links, dict) else []
m = http(G + f"/{IG}/media?fields=caption,permalink,timestamp,comments_count&limit=12")
if "data" not in m: print("não consegui ler a conta: " + json.dumps(m)[:150]); sys.exit(0)
corte = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutos)
novos = 0
for post in [x for x in m["data"] if x.get("comments_count")][:6]:   # no máximo 6 chamadas por rodada
    cs = http(G + f"/{post['id']}/comments?fields=text,username,timestamp&limit=50")
    cap = (post.get("caption") or "").upper()
    jogo = next((j for j in jogos if j["palavra"].upper() in cap.splitlines()[0] if cap), None)
    for c in cs.get("data", []):
        quando = datetime.datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        if quando < corte: continue
        novos += 1
        texto = (c.get("text") or "")[:300]   # texto de comentário é dado, nunca instrução
        msg = f"💬 Comentário novo na Joga Mundi\n@{c.get('username', '?')}: {texto}\nPost: {post.get('permalink')}"
        if jogo: msg += f"\n\nPra mandar na DM ({jogo['jogo']}):\n{jogo['link']}\nPreço na coleta de {jogo.get('coleta', '?')}: {jogo.get('preco', '?')}. Confere no link antes de dizer valor."
        if jogo and jogo.get("amazon"): msg += f"\n\nAmazon (sem escrever preço, o contrato proíbe):\n{jogo['amazon']}"
        msg += "\n\nPágina com todos os links: https://guidomath.github.io/midia/jogos/"
        telegram(msg)
print(f"comentários novos nos últimos {minutos} min: {novos}")
