# Publica na @joga.mundi o Reel do horário (fila pública em jogos/fila.json deste repositório).
# Uso: python3 postar.py HH:MM [--ensaio]. Não imprime segredo. O token da Meta é injetado pelo ambiente.
import datetime, json, os, sys, time, urllib.parse, urllib.request
BRT = datetime.timezone(datetime.timedelta(hours=-3))
agora = datetime.datetime.now(BRT); dia = agora.strftime("%Y-%m-%d")
hora = next((a for a in sys.argv[1:] if ":" in a), None); ensaio = "--ensaio" in sys.argv
if ensaio and "--dia" in sys.argv: dia = sys.argv[sys.argv.index("--dia") + 1]   # só no ensaio
IG = "17841416017895564"; G = "https://graph.facebook.com/v26.0"
RAW = "https://raw.githubusercontent.com/guidoMath/midia/main/jogos/"
def http(url, dados=None, timeout=90):
    req = urllib.request.Request(url, data=dados, method="POST" if dados else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)
    except urllib.error.HTTPError as e: return {"erro_http": e.code, "corpo": e.read()[:300].decode(errors="ignore")}
    except Exception as e: return {"erro": str(e)[:200]}
def telegram(msg):
    tg, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if ensaio or not tg or not chat: return
    http(f"https://api.telegram.org/bot{tg}/sendMessage", urllib.parse.urlencode({"chat_id": chat, "text": msg}).encode())
def sai(msg, avisa=False):
    if avisa: telegram(f"🔴 Joga Mundi {dia} {hora}: {msg}")
    print(msg); sys.exit(0)
if not hora: sai("faltou a hora")
fila = http(RAW + f"fila.json?t={int(time.time())}")
if "posts" not in fila: sai("não consegui ler a fila: " + json.dumps(fila)[:150], True)
p = next((x for x in fila["posts"] if x["data"] == dia and x["hora"] == hora), None)
if not p: sai(f"{dia} {hora}: nada na fila pra este horário")
leg = p["legenda"].strip(); l1 = leg.splitlines()[0]
if "(publi)" not in l1: sai("legenda sem (publi) na 1ª linha; não publiquei", True)
if any(t in leg.lower() for t in (" ia.", " ia ", "inteligência artificial")): sai("legenda fala de IA; não publiquei", True)
ja = http(G + f"/{IG}/media?fields=caption,permalink&limit=15")
if "data" not in ja: sai("não consegui ler a conta: " + json.dumps(ja)[:150], True)
norm = lambda t: " ".join((t or "").split())   # compara a legenda INTEIRA: dois vídeos do mesmo jogo têm a mesma 1ª linha
igual = next((m for m in ja["data"] if norm(m.get("caption")) == norm(leg)), None)
if igual: sai(f"{p['pasta']} já está publicado ({igual.get('permalink')}); nada a fazer")
video = RAW + p["pasta"] + "/video.mp4"
try:
    cod = urllib.request.urlopen(urllib.request.Request(video, method="HEAD"), timeout=60).status
except Exception as e: cod = str(e)[:80]
if cod != 200: sai(f"vídeo não responde ({cod}): {video}", True)
capa = RAW + p["pasta"] + "/capa.jpg"   # capa é opcional: sem ela, ou se a Meta recusar, publica sem
try:
    if urllib.request.urlopen(urllib.request.Request(capa, method="HEAD"), timeout=60).status != 200: capa = None
except Exception: capa = None
if ensaio: print(f"[ENSAIO] publicaria {p['pasta']} em {dia} {hora}\n[ENSAIO] {video}\n[ENSAIO] capa: {capa}\n[ENSAIO] legenda:\n{leg}"); sys.exit(0)
c = None
for tentativa in ([capa, None] if capa else [None]):
    campos = {"media_type": "REELS", "video_url": video, "caption": leg, "share_to_feed": "true"}
    if tentativa: campos["cover_url"] = tentativa
    c = http(G + f"/{IG}/media", urllib.parse.urlencode(campos).encode())
    if "id" not in c:
        if tentativa: print("com capa falhou ao criar; tentando sem capa: " + json.dumps(c)[:150]); continue
        sai("falhou ao criar o post: " + json.dumps(c)[:200], True)
    s = {}
    for _ in range(60):
        time.sleep(8); s = http(G + f"/{c['id']}?fields=status_code,status")
        if s.get("status_code") in ("FINISHED", "ERROR"): break
    if s.get("status_code") == "FINISHED": capa = tentativa; break
    if s.get("status_code") == "ERROR" and tentativa: print("a Meta recusou com capa; tentando sem capa: " + json.dumps(s)[:150]); continue
    if s.get("status_code") == "ERROR": sai("a Meta recusou o vídeo: " + json.dumps(s)[:200], True)
    sai("o vídeo não ficou pronto em 8 minutos; não publiquei", True)
pub = http(G + f"/{IG}/media_publish", urllib.parse.urlencode({"creation_id": c["id"]}).encode())
if "id" not in pub: sai("falhou ao publicar: " + json.dumps(pub)[:200], True)
link = http(G + f"/{pub['id']}?fields=permalink").get("permalink", "")
telegram(f"✅ Joga Mundi publicou {p.get('jogo', p['pasta'])} ({hora}): {link}")
print(f"publicado {dia} {hora} {p['pasta']} {pub['id']} {link}")
