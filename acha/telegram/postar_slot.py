# Posta no canal @achamundi o produto do horário (fila pública no repositório midia).
# Preço puxado da API da Shopee na hora. Não imprime segredo.
import datetime, hashlib, json, os, sys, time, urllib.parse, urllib.request
BRT = datetime.timezone(datetime.timedelta(hours=-3))
agora = datetime.datetime.now(BRT)
hora = agora.replace(minute=0 if agora.minute < 30 else 30).strftime("%H:%M")
dia = agora.strftime("%Y-%m-%d")
def http(url, dados=None, cab=None):
    req = urllib.request.Request(url, data=dados, headers=cab or {}, method="POST" if dados else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: return {"erro_http": e.code, "corpo": e.read()[:300].decode(errors="ignore")}
    except Exception as e: return {"erro": str(e)[:200]}
tg = os.environ.get("TELEGRAM_BOT_TOKEN"); privado = os.environ.get("TELEGRAM_CHAT_ID")
def telegram(metodo, campos):
    return http(f"https://api.telegram.org/bot{tg}/{metodo}", urllib.parse.urlencode(campos).encode())
def alerta(msg):
    telegram("sendMessage", {"chat_id": privado, "text": "Acha Telegram " + dia + " " + hora + ": " + msg}); print(msg); sys.exit(0)
fila = http(f"https://raw.githubusercontent.com/guidoMath/midia/main/acha/telegram/fila-{dia}.json?t={int(time.time())}")
if "itens" not in fila: print("sem fila hoje"); sys.exit(0)
item = next((x for x in fila["itens"] if x["hora"] == hora), None)
if not item: print("nada neste horário"); sys.exit(0)
if item.get("pular"): print("pulado:", item["pular"]); sys.exit(0)
app, seg = os.environ.get("SHOPEE_APP_ID"), os.environ.get("SHOPEE_SECRET")
corpo = json.dumps({"query": "{productOfferV2(itemId:%d,limit:1){nodes{priceMin priceMax productName}}}" % int(item["id_produto"])}, separators=(",", ":"))
ts = str(int(time.time()))
ass = hashlib.sha256((app + ts + corpo + seg).encode()).hexdigest()
r = http("https://open-api.affiliate.shopee.com.br/graphql", corpo.encode(),
         {"Content-Type": "application/json", "Authorization": f"SHA256 Credential={app}, Timestamp={ts}, Signature={ass}"})
nos = ((r.get("data") or {}).get("productOfferV2") or {}).get("nodes") or []
if not nos: alerta("produto " + str(item["id_produto"]) + " sem oferta na API; não postei. " + json.dumps(r)[:150])
pmin, pmax = float(nos[0]["priceMin"]), float(nos[0]["priceMax"])
reais = lambda v: "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
preco = ("a partir de " if pmax > pmin else "") + reais(pmin)
texto = f"{item['nome']}\n\n💰 {preco} em {agora.strftime('%d/%m')} (pode mudar, confere no link)\n\n👉 {item['link']}\n\n(publi)"
res = telegram("sendPhoto", {"chat_id": "@achamundi", "photo": item["foto"], "caption": texto, "disable_notification": "true"})
if not res.get("ok"): alerta("FALHOU ao postar " + item["nome"] + ": " + json.dumps(res)[:200])
print("postado", hora, item["nome"], preco)
