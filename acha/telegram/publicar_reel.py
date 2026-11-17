# Publica o Reel do horário: confere o preço na API da Shopee, posta o vídeo com o
# link no canal @achamundi e publica no Instagram @acha.mundi. Uso: publicar_reel.py AAAA-MM-DD HH:MM
# Não imprime segredo. Se o preço mudou, posta só no Telegram (com o preço novo) e avisa.
import datetime, hashlib, json, os, subprocess, sys, time, urllib.parse, urllib.request
dia, hora = sys.argv[1], sys.argv[2]
IG = "17841458014404483"; G = "https://graph.facebook.com/v26.0/"
RAW = "https://raw.githubusercontent.com/guidoMath/midia/main/"
def http(url, dados=None, cab=None, metodo=None):
    req = urllib.request.Request(url, data=dados, headers=cab or {}, method=metodo or ("POST" if dados else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=90) as r: return json.load(r)
    except urllib.error.HTTPError as e: return {"erro_http": e.code, "corpo": e.read()[:300].decode(errors="ignore")}
    except Exception as e: return {"erro": str(e)[:200]}
tg = os.environ.get("TELEGRAM_BOT_TOKEN"); privado = os.environ.get("TELEGRAM_CHAT_ID")
def aviso(msg):
    http(f"https://api.telegram.org/bot{tg}/sendMessage", urllib.parse.urlencode({"chat_id": privado, "text": f"Acha Reel {dia} {hora}: {msg}"}).encode())
    print(msg)
lista = http(f"{RAW}acha/{dia}/reels.json?t={int(time.time())}")
m = next((x for x in lista if x["hora"] == hora), None) if isinstance(lista, list) else None
if not m: aviso("sem Reel nesse horário na lista"); sys.exit(0)
app, seg = os.environ.get("SHOPEE_APP_ID"), os.environ.get("SHOPEE_SECRET")
corpo = json.dumps({"query": "{productOfferV2(itemId:%d,limit:1){nodes{priceMin priceMax}}}" % int(m["id_produto"])}, separators=(",", ":"))
ts = str(int(time.time())); ass = hashlib.sha256((app + ts + corpo + seg).encode()).hexdigest()
r = http("https://open-api.affiliate.shopee.com.br/graphql", corpo.encode(), {"Content-Type": "application/json", "Authorization": f"SHA256 Credential={app}, Timestamp={ts}, Signature={ass}"})
nos = ((r.get("data") or {}).get("productOfferV2") or {}).get("nodes") or []
if not nos: aviso("produto sem oferta na API; nada publicado"); sys.exit(0)
pmin, pmax = float(nos[0]["priceMin"]), float(nos[0]["priceMax"])
igual = abs(pmin - m["preco_min"]) < 0.005 and abs(pmax - m["preco_max"]) < 0.005
reais = lambda v: "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
d = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m")
texto = f"{m['nome_tg']}\n\n💰 {'a partir de ' if pmax > pmin else ''}{reais(pmin)} em {d} (pode mudar, confere no link)\n\n👉 {m['link']}\n\n(publi)"
subprocess.run(["curl", "-sSf", "-o", "/tmp/v.mp4", RAW + m.get("video_tg", m["video"])])  # Telegram: versão sem a tela "Link no Telegram"
t = subprocess.run(["curl", "-sS", "-F", "chat_id=@achamundi", "--form-string", "caption=" + texto, "-F", "supports_streaming=true",
                    "-F", "video=@/tmp/v.mp4", f"https://api.telegram.org/bot{tg}/sendVideo"], capture_output=True, text=True).stdout
ok_tg = json.loads(t or "{}").get("ok")
if not igual:
    aviso(f"preço mudou ({reais(m['preco_min'])} no vídeo, {reais(pmin)} agora): Reel NÃO publicado. Telegram {'ok' if ok_tg else 'FALHOU'}"); sys.exit(0)
c = http(G + IG + "/media", urllib.parse.urlencode({"media_type": "REELS", "video_url": RAW + m["video"], "caption": m["legenda"], "share_to_feed": "true"}).encode())
if "id" not in c: aviso("container falhou: " + json.dumps(c)[:200] + f" | Telegram {'ok' if ok_tg else 'FALHOU'}"); sys.exit(0)
for _ in range(60):
    st = http(G + c["id"] + "?fields=status_code").get("status_code")
    if st in ("FINISHED", "ERROR", "EXPIRED"): break
    time.sleep(8)
if st != "FINISHED": aviso(f"container {c['id']} ficou {st}; Reel não publicado"); sys.exit(0)
p = http(G + IG + "/media_publish", urllib.parse.urlencode({"creation_id": c["id"]}).encode())
link = http(G + p["id"] + "?fields=permalink").get("permalink") if "id" in p else None
aviso(f"{m['experimento']} | Telegram {'ok' if ok_tg else 'FALHOU'} | Instagram " + (f"{link} (media {p['id']})" if link else "FALHOU " + json.dumps(p)[:150]))
