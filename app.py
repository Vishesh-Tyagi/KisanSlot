from flask import Flask, request, redirect, session, render_template, flash
from jinja2 import DictLoader
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, random, datetime

app = Flask(__name__)
app.secret_key = "sih2026-demo"
DB = "kisan.db"
SLOTS = ["09:00-11:00", "11:00-13:00", "14:00-16:00", "16:00-18:00"]
SLOT_LIMIT = 5
MIN_PER_FARMER = 15
RATES = {"Wheat": 2425, "Paddy": 2369, "Mustard": 6200, "Gram": 5875}  # demo Rs/quintal

HI = {
 "KisanSlot": "किसान स्लॉट", "Home": "होम", "Dashboard": "डैशबोर्ड", "My Bookings": "मेरी बुकिंग", "Book Slot": "स्लॉट बुक करें",
 "Login": "लॉगिन", "Register": "पंजीकरण", "Logout": "लॉगआउट", "Live Queue": "लाइव कतार", "Hi,": "नमस्ते,",
 "Book your procurement slot. Skip the queue.": "अपना खरीद स्लॉट बुक करें। कतार से बचें।",
 "Slot booking · Live queue · SMS alerts · Payment tracking": "स्लॉट बुकिंग · लाइव कतार · SMS अलर्ट · भुगतान ट्रैकिंग",
 "Farmers": "किसान", "Slots booked": "बुक किए गए स्लॉट", "Payments done": "भुगतान पूर्ण", "Centres": "केंद्र", "Centre": "केंद्र",
 "Check the live queue at any centre. No login needed.": "किसी भी केंद्र की लाइव कतार देखें। लॉगिन की ज़रूरत नहीं।",
 "How it works": "यह कैसे काम करता है", "1. Register": "1. पंजीकरण", "Phone and crop": "फ़ोन और फसल",
 "2. Book": "2. बुकिंग", "Pick centre, date and a low-crowd slot": "केंद्र, तारीख और कम भीड़ वाला स्लॉट चुनें",
 "3. Track": "3. ट्रैक करें", "Queue position, SMS alerts, QR token": "कतार में स्थान, SMS अलर्ट, QR टोकन",
 "4. Get paid": "4. भुगतान पाएं", "Procurement and payment status": "खरीद और भुगतान की स्थिति",
 "Create your account": "अपना खाता बनाएं", "Welcome back": "वापसी पर स्वागत है", "Name": "नाम",
 "Mobile number": "मोबाइल नंबर", "Main crop": "मुख्य फसल", "Password": "पासवर्ड",
 "Already have an account?": "पहले से खाता है?", "New farmer?": "नए किसान हैं?", "Demo admin login": "डेमो एडमिन लॉगिन",
 "Wheat": "गेहूं", "Paddy": "धान", "Mustard": "सरसों", "Gram": "चना",
 "Date": "तारीख", "Quantity (quintals)": "मात्रा (क्विंटल)", "Crowd": "भीड़", "seats left": "सीटें बाकी",
 "Confirm Booking": "बुकिंग पक्की करें", "Low": "कम", "Medium": "मध्यम", "High": "अधिक", "Full": "भरा हुआ",
 "Token": "टोकन", "Status": "स्थिति", "Payment": "भुगतान", "Booked": "बुक किया", "Arrived": "पहुंचे",
 "Procured": "खरीदा गया", "Paid": "भुगतान हुआ", "Pending": "लंबित", "Processing": "प्रक्रिया में", "Cancelled": "रद्द",
 "Cancel": "रद्द करें", "Queue position": "कतार में स्थान", "Estimated wait": "अनुमानित प्रतीक्षा", "min": "मिनट",
 "qtl": "क्विंटल", "No bookings yet.": "अभी कोई बुकिंग नहीं।", "Notifications": "सूचनाएं", "None yet.": "अभी कोई नहीं।",
 "Now serving": "अभी सेवा में", "Waiting": "प्रतीक्षा में", "No one at the counter right now.": "अभी काउंटर पर कोई नहीं।",
 "auto-refreshes every 10 seconds": "हर 10 सेकंड में अपने आप अपडेट", "Slot": "स्लॉट", "Est. wait": "अनु. प्रतीक्षा",
 "Officer Dashboard": "अधिकारी डैशबोर्ड", "Bookings": "बुकिंग", "In queue": "कतार में", "Quintals procured": "खरीदे गए क्विंटल",
 "Payments pending": "लंबित भुगतान", "All centres": "सभी केंद्र", "Filter": "फ़िल्टर", "Token / name / phone": "टोकन / नाम / फ़ोन",
 "Slot load": "स्लॉट लोड", "Centre Queue Management": "केंद्र कतार प्रबंधन", "Farmer": "किसान", "Date / Slot": "तारीख / स्लॉट",
 "Qty": "मात्रा", "Action": "कार्रवाई", "Mark Arrived": "पहुंचा चिह्नित करें", "Mark Procured": "खरीदा चिह्नित करें",
 "Mark Paid": "भुगतान चिह्नित करें", "Rs": "₹",
 "Registered! Please login.": "पंजीकरण सफल! कृपया लॉगिन करें।",
 "This phone number is already registered.": "यह फ़ोन नंबर पहले से पंजीकृत है।",
 "Wrong phone or password.": "फ़ोन या पासवर्ड गलत है।",
 "Sorry, that slot just got full. Pick another.": "क्षमा करें, यह स्लॉट भर गया। दूसरा चुनें।",
 "Booking confirmed! Your token is": "बुकिंग पक्की! आपका टोकन है",
 "Logged in successfully.": "सफलतापूर्वक लॉगिन हुआ।", "You have been logged out.": "आप लॉगआउट हो गए हैं।",
 "Karnal Mandi Centre": "करनाल मंडी केंद्र", "Khanna Grain Market": "खन्ना अनाज मंडी", "Indore Krishi Upaj Mandi": "इंदौर कृषि उपज मंडी",
 "Karnal": "करनाल", "Ludhiana": "लुधियाना", "Indore": "इंदौर", "Centre Officer": "केंद्र अधिकारी",
 "KisanSlot · Smart India Hackathon 2026 · PS 26032 · Dept. of Consumer Affairs":
 "किसान स्लॉट · स्मार्ट इंडिया हैकाथॉन 2026 · PS 26032 · उपभोक्ता मामले विभाग",
}
NOTES = {  # notifications are stored as keys and shown in the reader's language
 "slot": ("SMS: Slot confirmed. Token {0}, {1} {2}. Carry Aadhaar & land record.", "SMS: स्लॉट पक्का। टोकन {0}, {1} {2}। आधार और ज़मीन के कागज़ साथ लाएं।"),
 "arr": ("SMS: Token {0} - please proceed to the weighing counter now.", "SMS: टोकन {0} - कृपया अभी तौल काउंटर पर पहुंचें।"),
 "proc": ("SMS: {0} qtl procured. Rs {1} payment is processing.", "SMS: {0} क्विंटल खरीदा गया। ₹{1} का भुगतान प्रक्रिया में है।"),
 "paid": ("SMS: Rs {0} credited to your bank account. Token {1}.", "SMS: ₹{0} आपके बैंक खाते में जमा हुए। टोकन {1}।"),
}


def t(s):
    return HI.get(s, s) if session.get("lang") == "hi" else s


def note(m):
    if m.startswith("@"):
        k, *a = m[1:].split("|")
        return NOTES[k][1 if session.get("lang") == "hi" else 0].format(*a)
    return m


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, phone TEXT UNIQUE,
        password TEXT, crop TEXT, role TEXT DEFAULT 'farmer');
    CREATE TABLE IF NOT EXISTS centres(id INTEGER PRIMARY KEY, name TEXT, district TEXT);
    CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY, user_id INT, centre_id INT,
        date TEXT, slot TEXT, qty INT, token TEXT, status TEXT DEFAULT 'Booked',
        payment TEXT DEFAULT 'Pending', amount INT DEFAULT 0);
    CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY, user_id INT, msg TEXT, ts TEXT);
    """)
    if not c.execute("SELECT 1 FROM centres").fetchone():
        c.executemany("INSERT INTO centres(name,district) VALUES(?,?)", [
            ("Karnal Mandi Centre", "Karnal"), ("Khanna Grain Market", "Ludhiana"),
            ("Indore Krishi Upaj Mandi", "Indore")])
        c.execute("INSERT INTO users(name,phone,password,role) VALUES(?,?,?,?)",
                  ("Centre Officer", "admin", generate_password_hash("admin123"), "admin"))
    c.commit()
    c.close()


def notify(c, uid, msg):
    c.execute("INSERT INTO notifications(user_id,msg,ts) VALUES(?,?,?)",
              (uid, msg, datetime.datetime.now().strftime("%d %b %H:%M")))


def me():
    if "uid" not in session:
        return None
    c = db()
    u = c.execute("SELECT * FROM users WHERE id=?", (session["uid"],)).fetchone()
    c.close()
    if not u:
        session.pop("uid", None)
    return u


@app.context_processor
def inj():
    return dict(t=t, note=note, user=me(), lang=session.get("lang", "en"))


def crowd(used):
    r = used / SLOT_LIMIT
    return ("Full", "red") if r >= 1 else ("High", "orange") if r >= .7 else ("Medium", "amber") if r >= .4 else ("Low", "green")


@app.route("/lang/<l>")
def lang(l):
    session["lang"] = "hi" if l == "hi" else "en"
    return redirect(request.referrer or "/")


@app.route("/")
def home():
    c = db()
    s = dict(farmers=c.execute("SELECT COUNT(*) FROM users WHERE role='farmer'").fetchone()[0],
             bookings=c.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
             paid=c.execute("SELECT COUNT(*) FROM bookings WHERE payment='Paid'").fetchone()[0])
    centres = c.execute("SELECT * FROM centres").fetchall()
    c.close()
    return render_template("home.html", s=s, centres=centres)


@app.route("/register", methods=["GET", "POST"])
def register():
    if me():
        return redirect("/")
    if request.method == "POST":
        f = request.form
        c = db()
        try:
            c.execute("INSERT INTO users(name,phone,password,crop) VALUES(?,?,?,?)",
                      (f["name"], f["phone"], generate_password_hash(f["password"]), f["crop"]))
            c.commit()
            flash(t("Registered! Please login."))
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash(t("This phone number is already registered."))
        finally:
            c.close()
    return render_template("register.html", crops=RATES)


@app.route("/login", methods=["GET", "POST"])
def login():
    if me():
        return redirect("/")
    if request.method == "POST":
        c = db()
        u = c.execute("SELECT * FROM users WHERE phone=?", (request.form["phone"],)).fetchone()
        c.close()
        if u and check_password_hash(u["password"], request.form["password"]):
            session["uid"] = u["id"]
            flash(t("Logged in successfully."))
            return redirect("/admin" if u["role"] == "admin" else "/dashboard")
        flash(t("Wrong phone or password."))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("uid", None)
    flash(t("You have been logged out."))
    return redirect("/")


@app.route("/book", methods=["GET", "POST"])
def book():
    u = me()
    if not u or u["role"] != "farmer":
        return redirect("/login")
    c = db()
    centres = c.execute("SELECT * FROM centres").fetchall()
    date = request.values.get("date") or str(datetime.date.today() + datetime.timedelta(days=1))
    cid = int(request.values.get("centre") or centres[0]["id"])
    counts = {r["slot"]: r["n"] for r in c.execute(
        "SELECT slot, COUNT(*) n FROM bookings WHERE centre_id=? AND date=? AND status!='Cancelled' GROUP BY slot",
        (cid, date))}
    avail = [(s, SLOT_LIMIT - counts.get(s, 0), *crowd(counts.get(s, 0))) for s in SLOTS]
    if request.method == "POST" and "slot" in request.form:
        slot, qty = request.form["slot"], int(request.form["qty"])
        if counts.get(slot, 0) >= SLOT_LIMIT:
            flash(t("Sorry, that slot just got full. Pick another."))
        else:
            token = "T" + str(random.randint(1000, 9999))
            c.execute("INSERT INTO bookings(user_id,centre_id,date,slot,qty,token) VALUES(?,?,?,?,?,?)",
                      (u["id"], cid, date, slot, qty, token))
            notify(c, u["id"], f"@slot|{token}|{date}|{slot}")
            c.commit()
            c.close()
            flash(f"{t('Booking confirmed! Your token is')} {token}")
            return redirect("/dashboard")
    c.close()
    return render_template("book.html", centres=centres, date=date, cid=cid, avail=avail, today=str(datetime.date.today()))


@app.route("/dashboard")
def dashboard():
    u = me()
    if not u or u["role"] != "farmer":
        return redirect("/login")
    c = db()
    rows = c.execute("""SELECT b.*, c.name cname FROM bookings b JOIN centres c ON c.id=b.centre_id
                        WHERE user_id=? ORDER BY b.id DESC""", (u["id"],)).fetchall()
    bookings = []
    for b in rows:
        b = dict(b)
        b["step"] = 3 if b["payment"] == "Paid" else {"Booked": 0, "Arrived": 1, "Procured": 2}.get(b["status"], 0)
        if b["status"] in ("Booked", "Arrived"):
            ahead = c.execute("""SELECT COUNT(*) FROM bookings WHERE centre_id=? AND date=? AND slot=?
                AND status IN ('Booked','Arrived') AND id<?""", (b["centre_id"], b["date"], b["slot"], b["id"])).fetchone()[0]
            b["pos"], b["wait"] = ahead + 1, ahead * MIN_PER_FARMER
        bookings.append(b)
    notes = c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 8", (u["id"],)).fetchall()
    c.close()
    return render_template("dashboard.html", bookings=bookings, notes=notes)


@app.route("/cancel/<int:bid>")
def cancel(bid):
    u = me()
    if u:
        c = db()
        c.execute("UPDATE bookings SET status='Cancelled' WHERE id=? AND user_id=? AND status='Booked'", (bid, u["id"]))
        c.commit()
        c.close()
    return redirect("/dashboard")


@app.route("/queue/<int:cid>")
def board(cid):
    c = db()
    centre = c.execute("SELECT * FROM centres WHERE id=?", (cid,)).fetchone()
    act = "status IN ('Booked','Arrived')"
    first = c.execute(f"SELECT MIN(date) FROM bookings WHERE centre_id=? AND {act}", (cid,)).fetchone()[0]
    date = request.args.get("date") or first or str(datetime.date.today())
    rows = c.execute(f"""SELECT b.token,b.slot,b.status,u.name FROM bookings b JOIN users u ON u.id=b.user_id
        WHERE centre_id=? AND date=? AND {act} ORDER BY slot,b.id""", (cid, date)).fetchall()
    c.close()
    return render_template("board.html", centre=centre, date=date, serving=[r for r in rows if r["status"] == "Arrived"],
                           waiting=[r for r in rows if r["status"] == "Booked"])


@app.route("/admin")
def admin():
    u = me()
    if not u or u["role"] != "admin":
        return redirect("/login")
    cid, date, q = request.args.get("centre", ""), request.args.get("date", ""), request.args.get("q", "").strip()
    sql = """SELECT b.*, u.name fname, u.phone, c.name cname FROM bookings b
        JOIN users u ON u.id=b.user_id JOIN centres c ON c.id=b.centre_id WHERE 1=1"""
    args = []
    if cid:
        sql += " AND b.centre_id=?"; args.append(cid)
    if date:
        sql += " AND b.date=?"; args.append(date)
    if q:
        sql += " AND (b.token LIKE ? OR u.phone LIKE ? OR u.name LIKE ?)"; args += [f"%{q}%"] * 3
    c = db()
    rows = c.execute(sql + " ORDER BY b.date, b.slot, b.id", args).fetchall()
    centres = c.execute("SELECT * FROM centres").fetchall()
    c.close()
    live = [r for r in rows if r["status"] != "Cancelled"]
    stats = dict(total=len(live), waiting=sum(r["status"] in ("Booked", "Arrived") for r in live),
                 procured=sum(r["status"] == "Procured" for r in live),
                 pending=sum(r["status"] == "Procured" and r["payment"] != "Paid" for r in live),
                 qty=sum(r["qty"] for r in live if r["status"] == "Procured"))
    load = [(s, sum(r["slot"] == s for r in live)) for s in SLOTS]
    return render_template("admin.html", rows=rows, stats=stats, load=load, centres=centres, cid=cid, date=date, q=q,
                           mx=max([n for _, n in load] + [SLOT_LIMIT]))


@app.route("/admin/update/<int:bid>/<field>/<value>")
def update(bid, field, value):
    u = me()
    if not u or u["role"] != "admin" or field not in ("status", "payment"):
        return redirect("/login")
    c = db()
    b = c.execute("SELECT b.*, u.crop FROM bookings b JOIN users u ON u.id=b.user_id WHERE b.id=?", (bid,)).fetchone()
    c.execute(f"UPDATE bookings SET {field}=? WHERE id=?", (value, bid))
    if field == "status" and value == "Arrived":
        notify(c, b["user_id"], f"@arr|{b['token']}")
    elif field == "status" and value == "Procured":
        amt = b["qty"] * RATES.get(b["crop"], 2400)
        c.execute("UPDATE bookings SET amount=?, payment='Processing' WHERE id=?", (amt, bid))
        notify(c, b["user_id"], f"@proc|{b['qty']}|{amt}")
    elif field == "payment" and value == "Paid":
        notify(c, b["user_id"], f"@paid|{b['amount']}|{b['token']}")
    c.commit()
    c.close()
    return redirect(request.referrer or "/admin")


T = {
"base.html": """<!doctype html><html lang="{{lang}}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{{t('KisanSlot')}}</title><style>
:root{--g:#14532d;--g2:#2e7d32;--s:#ff9933;--bg:#f2f7f1;--tx:#1b2a1d;--mut:#6b7a6c}
*{box-sizing:border-box}body{font-family:'Segoe UI','Nirmala UI',system-ui,sans-serif;margin:0;background:var(--bg);color:var(--tx);line-height:1.5}
a{color:var(--g2)}nav{background:linear-gradient(90deg,var(--g),var(--g2));color:#fff;padding:10px 18px;display:flex;flex-wrap:wrap;gap:8px;
justify-content:space-between;align-items:center;position:sticky;top:0;z-index:5;box-shadow:0 2px 10px #0003}
nav:after{content:'';position:absolute;left:0;right:0;bottom:-4px;height:4px;background:linear-gradient(90deg,#ff9933 33%,#fff 33% 66%,#138808 66%)}
.logo{font-weight:700;font-size:20px;color:#fff;text-decoration:none}.links{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.links a{color:#fff;text-decoration:none;padding:7px 11px;border-radius:8px;font-size:14px}.links a:hover{background:#ffffff2e}
.chip{background:#ffffff26;padding:6px 12px;border-radius:20px;font-size:13px}.lang{background:var(--s);color:#000!important;font-weight:600}
.wrap{max-width:980px;margin:24px auto;padding:0 14px}
.hero{background:radial-gradient(circle at 80% 20%,#66bb6a55,transparent 50%),linear-gradient(135deg,var(--g),#388e3c);color:#fff;border-radius:20px;padding:44px 22px;text-align:center}
.hero h1{margin:8px 0;font-size:clamp(24px,5vw,40px)}.hero p{opacity:.92;margin:0 0 22px}.emo{font-size:40px;letter-spacing:8px}
.card{background:#fff;border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:0 2px 10px #0000000d;border:1px solid #e6eee5}
.card h2,.card h3{margin-top:0;color:var(--g)}
input,select{padding:12px;margin:4px 0 14px;width:100%;border:1.5px solid #cfdccf;border-radius:10px;font-size:16px;background:#fff}
input:focus,select:focus{outline:0;border-color:var(--g2);box-shadow:0 0 0 3px #2e7d3226}
.btn{background:var(--g2);color:#fff;border:0;padding:12px 20px;border-radius:10px;cursor:pointer;text-decoration:none;display:inline-block;font-size:15px;font-weight:600;margin:3px}
.btn:hover{filter:brightness(1.1)}.btn.o{background:var(--s);color:#000}.btn.w{background:#fff;color:var(--g)}.btn.red{background:#c62828}.btn.sm{padding:6px 12px;font-size:12px}.btn.full{width:100%}
.badge{padding:3px 11px;border-radius:12px;font-size:12px;background:#e5e5e5;white-space:nowrap;font-weight:600}
.Booked,.Pending,.amber{background:#fff0c2}.Arrived,.Processing{background:#cfe3ff}.Procured,.Paid,.green{background:#c8e6c9}.Cancelled,.red{background:#f8d7da}.orange{background:#ffe0b2}
.flash{background:#e8f5e9;border-left:4px solid var(--g2);padding:12px;margin-bottom:14px;border-radius:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:16px 0}
.stat{background:#fff;padding:16px;border-radius:14px;text-align:center;border:1px solid #e6eee5}.stat b{font-size:28px;display:block;color:var(--g2)}.stat span{color:var(--mut);font-size:13px}
.step{background:#fff;border:1px solid #e6eee5;border-radius:14px;padding:16px}.step b{color:var(--g)}
.steps{display:flex;margin:14px 0}.steps div{flex:1;text-align:center;font-size:12px;color:#999;position:relative}
.steps div:before{content:'✓';color:#fff;font-size:12px;line-height:24px;display:block;width:24px;height:24px;border-radius:50%;background:#ddd;margin:0 auto 4px}
.steps div.on{color:var(--g2);font-weight:700}.steps div.on:before{background:var(--g2)}
.bk{display:flex;gap:16px;flex-wrap:wrap;justify-content:space-between;border-top:1px solid #eee;padding:16px 0}
.tbl{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:680px}td,th{padding:10px 8px;border-bottom:1px solid #eee;text-align:left;font-size:14px}th{color:var(--mut);font-size:12px;text-transform:uppercase}
.bar{background:#e8f5e9;border-radius:6px;height:14px}.bar i{display:block;height:14px;background:var(--g2);border-radius:6px}
.slot{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;border:1.5px solid #dde6dd;border-radius:12px;padding:13px;margin-bottom:10px;cursor:pointer}
.slot:has(input:checked){border-color:var(--g2);background:#f1f8f1}
.big{font-size:30px;font-weight:700;color:var(--g2)}.auth{max-width:440px;margin:30px auto}
footer{text-align:center;color:var(--mut);font-size:12px;padding:24px}
@media(max-width:600px){.wrap{margin:14px auto}.hero{padding:30px 14px}.links a{padding:6px 8px;font-size:13px}}</style></head><body>
<nav><a class="logo" href="/">🌾 {{t('KisanSlot')}}</a><div class="links"><a href="/">{{t('Home')}}</a>
{% if user and user.role=='admin' %}<a href="/admin">{{t('Dashboard')}}</a>{% elif user %}<a href="/dashboard">{{t('My Bookings')}}</a><a href="/book">{{t('Book Slot')}}</a>
{% else %}<a href="/login">{{t('Login')}}</a><a href="/register">{{t('Register')}}</a>{% endif %}
{% if user %}<span class="chip">👤 {{user.name}}</span><a href="/logout">{{t('Logout')}}</a>{% endif %}
<a class="lang" href="/lang/{{'en' if lang=='hi' else 'hi'}}">{{'English' if lang=='hi' else 'हिंदी'}}</a></div></nav>
<div class="wrap">{% for m in get_flashed_messages() %}<div class="flash">{{m}}</div>{% endfor %}{% block body %}{% endblock %}</div>
<footer>{{t('KisanSlot · Smart India Hackathon 2026 · PS 26032 · Dept. of Consumer Affairs')}}</footer></body></html>""",

"home.html": """{% extends 'base.html' %}{% block body %}
<div class="hero"><div class="emo">🌾🚜📱</div><h1>{{t('Book your procurement slot. Skip the queue.')}}</h1>
<p>{{t('Slot booking · Live queue · SMS alerts · Payment tracking')}}</p>
{% if not user %}<a class="btn o" href="/register">{{t('Register')}}</a><a class="btn w" href="/login">{{t('Login')}}</a>
{% elif user.role=='admin' %}<a class="btn o" href="/admin">{{t('Dashboard')}}</a>
{% else %}<a class="btn o" href="/book">{{t('Book Slot')}}</a><a class="btn w" href="/dashboard">{{t('My Bookings')}}</a>{% endif %}</div>
<div class="grid"><div class="stat"><b>{{s.farmers}}</b><span>{{t('Farmers')}}</span></div><div class="stat"><b>{{s.bookings}}</b><span>{{t('Slots booked')}}</span></div>
<div class="stat"><b>{{s.paid}}</b><span>{{t('Payments done')}}</span></div><div class="stat"><b>{{centres|length}}</b><span>{{t('Centres')}}</span></div></div>
<div class="card"><h2>📺 {{t('Live Queue')}}</h2><p>{{t('Check the live queue at any centre. No login needed.')}}</p>
{% for c in centres %}<a class="btn sm" href="/queue/{{c.id}}">{{t(c.name)}}</a>{% endfor %}</div>
<div class="card"><h2>{{t('How it works')}}</h2><div class="grid">
<div class="step"><b>{{t('1. Register')}}</b><br>{{t('Phone and crop')}}</div><div class="step"><b>{{t('2. Book')}}</b><br>{{t('Pick centre, date and a low-crowd slot')}}</div>
<div class="step"><b>{{t('3. Track')}}</b><br>{{t('Queue position, SMS alerts, QR token')}}</div><div class="step"><b>{{t('4. Get paid')}}</b><br>{{t('Procurement and payment status')}}</div></div></div>{% endblock %}""",

"register.html": """{% extends 'base.html' %}{% block body %}<div class="card auth"><h2>{{t('Create your account')}}</h2><form method="post">
{{t('Name')}}<input name="name" required>{{t('Mobile number')}}<input name="phone" required pattern="[0-9]{10}" inputmode="numeric" maxlength="10">
{{t('Main crop')}}<select name="crop">{% for k in crops %}<option value="{{k}}">{{t(k)}}</option>{% endfor %}</select>
{{t('Password')}}<input name="password" type="password" required><button class="btn full">{{t('Register')}}</button></form>
<p>{{t('Already have an account?')}} <a href="/login">{{t('Login')}}</a></p></div>{% endblock %}""",

"login.html": """{% extends 'base.html' %}{% block body %}<div class="card auth"><h2>{{t('Welcome back')}}</h2><form method="post">
{{t('Mobile number')}}<input name="phone" required>{{t('Password')}}<input name="password" type="password" required>
<button class="btn full">{{t('Login')}}</button></form><p>{{t('New farmer?')}} <a href="/register">{{t('Register')}}</a></p>
<p><small>{{t('Demo admin login')}}: <b>admin</b> / <b>admin123</b></small></p></div>{% endblock %}""",

"book.html": """{% extends 'base.html' %}{% block body %}<div class="card"><h2>{{t('Book Slot')}}</h2>
<form method="get">{{t('Centre')}}<select name="centre" onchange="this.form.submit()">{% for c in centres %}
<option value="{{c.id}}" {{'selected' if c.id==cid}}>{{t(c.name)}} ({{t(c.district)}})</option>{% endfor %}</select>
{{t('Date')}}<input type="date" name="date" min="{{today}}" value="{{date}}" onchange="this.form.submit()"></form></div>
<div class="card"><form method="post"><input type="hidden" name="centre" value="{{cid}}"><input type="hidden" name="date" value="{{date}}">
{{t('Quantity (quintals)')}}<input type="number" name="qty" min="1" value="20" required>
{% for s,left,lvl,cls in avail %}<label class="slot"><span><input type="radio" name="slot" value="{{s}}" style="width:auto;margin:0 8px 0 0" {{'disabled' if left<=0}} required>
<b>{{s}}</b></span><span><span class="badge {{cls}}">{{t('Crowd')}}: {{t(lvl)}}</span> <small>{{left}} {{t('seats left')}}</small></span></label>{% endfor %}
<button class="btn full">{{t('Confirm Booking')}}</button></form></div>{% endblock %}""",

"dashboard.html": """{% extends 'base.html' %}{% block body %}
<div class="card"><h2>{{t('My Bookings')}}</h2>{% if not bookings %}<p>{{t('No bookings yet.')}} <a href="/book">{{t('Book Slot')}}</a></p>{% endif %}
{% for b in bookings %}<div class="bk"><div style="flex:1;min-width:240px"><b style="font-size:19px">{{t('Token')}} {{b.token}}</b> · {{t(b.cname)}}<br>
{{b.date}}, {{b.slot}} · {{b.qty}} {{t('qtl')}}<br>{{t('Status')}}: <span class="badge {{b.status}}">{{t(b.status)}}</span>
{{t('Payment')}}: <span class="badge {{b.payment}}">{{t(b.payment)}}</span>{% if b.amount %} <b>₹{{b.amount}}</b>{% endif %}
{% if b.status!='Cancelled' %}<div class="steps">{% for n in ['Booked','Arrived','Procured','Paid'] %}<div class="{{'on' if loop.index0<=b.step}}">{{t(n)}}</div>{% endfor %}</div>{% endif %}
{% if b.pos %}<p>📍 {{t('Queue position')}}: <b>{{b.pos}}</b> · {{t('Estimated wait')}}: <b>{{b.wait}} {{t('min')}}</b> · <a href="/queue/{{b.centre_id}}?date={{b.date}}">{{t('Live Queue')}}</a></p>{% endif %}
{% if b.status=='Booked' %}<a class="btn red sm" href="/cancel/{{b.id}}">{{t('Cancel')}}</a>{% endif %}</div>
{% if b.status!='Cancelled' %}<div id="qr{{b.id}}"></div>{% endif %}</div>{% endfor %}</div>
<div class="card"><h3>🔔 {{t('Notifications')}}</h3>{% for n in notes %}<p>{{note(n.msg)}} <small>({{n.ts}})</small></p>{% else %}<p>{{t('None yet.')}}</p>{% endfor %}</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script><script>
{% for b in bookings %}{% if b.status!='Cancelled' %}try{new QRCode(document.getElementById('qr{{b.id}}'),{text:'{{b.token}}',width:96,height:96})}catch(e){}{% endif %}{% endfor %}</script>{% endblock %}""",

"board.html": """{% extends 'base.html' %}{% block body %}<meta http-equiv="refresh" content="10">
<div class="card"><h2>📺 {{t('Live Queue')}} - {{t(centre.name)}}</h2><p>{{date}} · {{t('auto-refreshes every 10 seconds')}}</p>
<h3>{{t('Now serving')}}</h3>{% for r in serving %}<span class="big">{{r.token}}</span> <small>({{r.name.split()[0]}}, {{r.slot}})</small> &nbsp;{% else %}<p>{{t('No one at the counter right now.')}}</p>{% endfor %}
<h3>{{t('Waiting')}} ({{waiting|length}})</h3><div class="tbl"><table style="min-width:0"><tr><th>#</th><th>{{t('Token')}}</th><th>{{t('Slot')}}</th><th>{{t('Est. wait')}}</th></tr>
{% for r in waiting %}<tr><td>{{loop.index}}</td><td><b>{{r.token}}</b></td><td>{{r.slot}}</td><td>{{(loop.index0+serving|length)*15}} {{t('min')}}</td></tr>{% endfor %}</table></div></div>{% endblock %}""",

"admin.html": """{% extends 'base.html' %}{% block body %}<h2>{{t('Officer Dashboard')}}</h2>
<div class="grid"><div class="stat"><b>{{stats.total}}</b><span>{{t('Bookings')}}</span></div><div class="stat"><b>{{stats.waiting}}</b><span>{{t('In queue')}}</span></div>
<div class="stat"><b>{{stats.procured}}</b><span>{{t('Procured')}}</span></div><div class="stat"><b>{{stats.qty}}</b><span>{{t('Quintals procured')}}</span></div><div class="stat"><b>{{stats.pending}}</b><span>{{t('Payments pending')}}</span></div></div>
<div class="card"><form method="get" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;align-items:end">
<select name="centre"><option value="">{{t('All centres')}}</option>{% for c in centres %}<option value="{{c.id}}" {{'selected' if c.id|string==cid}}>{{t(c.name)}}</option>{% endfor %}</select>
<input type="date" name="date" value="{{date}}"><input name="q" placeholder="{{t('Token / name / phone')}}" value="{{q}}"><button class="btn" style="margin:0 0 14px">{{t('Filter')}}</button></form></div>
<div class="card"><h3>{{t('Slot load')}}</h3>{% for s,n in load %}<p style="margin:8px 0">{{s}} - {{n}}<span class="bar" style="display:block"><i style="width:{{n*100/mx}}%"></i></span></p>{% endfor %}</div>
<div class="card tbl"><h3>{{t('Centre Queue Management')}}</h3><table><tr><th>{{t('Token')}}</th><th>{{t('Farmer')}}</th><th>{{t('Centre')}}</th><th>{{t('Date / Slot')}}</th><th>{{t('Qty')}}</th><th>{{t('Status')}}</th><th>{{t('Payment')}}</th><th>{{t('Action')}}</th></tr>
{% for r in rows %}<tr><td><b>{{r.token}}</b></td><td>{{r.fname}}<br><small>{{r.phone}}</small></td><td>{{t(r.cname)}}</td><td>{{r.date}}<br>{{r.slot}}</td><td>{{r.qty}}</td>
<td><span class="badge {{r.status}}">{{t(r.status)}}</span></td><td><span class="badge {{r.payment}}">{{t(r.payment)}}</span>{% if r.amount %}<br>₹{{r.amount}}{% endif %}</td><td>
{% if r.status=='Booked' %}<a class="btn sm" href="/admin/update/{{r.id}}/status/Arrived">{{t('Mark Arrived')}}</a>{% endif %}
{% if r.status=='Arrived' %}<a class="btn sm" href="/admin/update/{{r.id}}/status/Procured">{{t('Mark Procured')}}</a>{% endif %}
{% if r.status=='Procured' and r.payment!='Paid' %}<a class="btn o sm" href="/admin/update/{{r.id}}/payment/Paid">{{t('Mark Paid')}}</a>{% endif %}
</td></tr>{% endfor %}</table></div>{% endblock %}""",
}
app.jinja_loader = DictLoader(T)

if __name__ == "__main__":
    init()
    import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
