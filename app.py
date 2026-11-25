import os
import time


def load_dotenv_lite(path=None):
    """极简 .env 读取（没有 python-dotenv 依赖）：KEY=VALUE 一行一个"""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass


load_dotenv_lite()

"""
英语闯关 TTS 代理（免费，无需任何 API Key）

技术方案：edge-tts（微软 Edge 的在线语音合成通道，免费）
为什么要后端：小程序/浏览器直接请求微软接口会被跨域和鉴权拦住，
所以由这台服务器代取音频，再以 mp3 流返回给前端。

启动：
    pip install -r requirements.txt
    python app.py
默认端口 8000，接口：
    GET /tts?text=hello&rate=0.9
    GET /health
"""
import io
import hashlib
import os
from typing import Optional

import json
from datetime import datetime, timedelta
import threading

import edge_tts
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

app = FastAPI(title="English Study TTS Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")
CACHE_DIR = os.getenv("TTS_CACHE_DIR", "./cache")
CACHE_MAX_BYTES = int(os.getenv("TTS_CACHE_MAX", str(300 * 1024 * 1024)))

os.makedirs(CACHE_DIR, exist_ok=True)


def build_rate(rate: float) -> str:
    """把 0.6~1.4 的倍速转成 edge-tts 需要的百分比字符串，如 +0% / -10%"""
    rate = max(0.5, min(1.5, float(rate)))
    pct = int(round((rate - 1) * 100))
    return f"{pct:+d}%"


def cache_path(text: str, rate: str, voice: str) -> str:
    key = hashlib.md5(f"{text}|{rate}|{voice}".encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.mp3")


async def synth(text: str, rate_str: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def trim_cache():
    try:
        files = [
            (os.path.join(CACHE_DIR, f), os.path.getsize(os.path.join(CACHE_DIR, f)))
            for f in os.listdir(CACHE_DIR)
            if f.endswith(".mp3")
        ]
        total = sum(s for _, s in files)
        if total <= CACHE_MAX_BYTES:
            return
        files.sort(key=lambda x: os.path.getmtime(x[0]))
        for path, size in files:
            os.remove(path)
            total -= size
            if total <= CACHE_MAX_BYTES:
                break
    except Exception as e:
        print("trim cache error", e)


@app.get("/health")
def health():
    return {"ok": True, "voice": DEFAULT_VOICE}


@app.get("/tts")
async def tts(
    request: Request,
    text: str = Query(..., min_length=1, max_length=500),
    rate: Optional[float] = 0.9,
    voice: Optional[str] = None,
):
    text = text.strip()
    voice = voice or DEFAULT_VOICE
    rate_str = build_rate(rate if rate is not None else 0.9)
    path = cache_path(text, rate_str, voice)

    if os.path.exists(path):
        with open(path, "rb") as f:
            audio = f.read()
    else:
        audio = await synth(text, rate_str, voice)
        if audio:
            with open(path, "wb") as f:
                f.write(audio)
            trim_cache()

    if not audio:
        return Response(status_code=502, content=b"tts failed")

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Length": str(len(audio)),
            "Accept-Ranges": "bytes",
        },
    )


# =========================================================
# 题库数据（章节/单词/例句）+ 后台管理接口
# =========================================================
DATA_DIR = os.getenv("DATA_DIR", "./data")
DATA_FILE = os.path.join(DATA_DIR, "chapters.json")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "xiaoyu")
DATA_LOCK = threading.Lock()

os.makedirs(DATA_DIR, exist_ok=True)


def _read_units():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("read chapters error", e)
        return []


def _write_units(units):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(units, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", ADMIN_TOKEN)


@app.post("/api/admin/login")
async def api_admin_login(request: Request):
    """管理后台登录：只保留一个管理员账号（可用环境变量改）"""
    body = await request.json()
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    if username != ADMIN_USER or password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="账号或口令不对")
    return {"ok": True, "token": ADMIN_TOKEN, "username": ADMIN_USER}


def _check_token(token):
    if not token or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="token 不对")


@app.get("/api/chapters")
def api_chapters(full: Optional[int] = 1, token: Optional[str] = None):
    """题库：full=1 返回完整内容（前端用），full=0 只返回目录信息"""
    units = _read_units()
    if full:
        return JSONResponse(units)
    return JSONResponse(
        [
            {
                "id": u.get("id"),
                "title": u.get("title"),
                "subtitle": u.get("subtitle"),
                "wordCount": len(u.get("words") or []),
                "sentenceCount": len(u.get("sentences") or []),
            }
            for u in units
        ]
    )


@app.get("/api/chapters/{chapter_id}")
def api_chapter_one(chapter_id: str):
    for u in _read_units():
        if u.get("id") == chapter_id:
            return JSONResponse(u)
    raise HTTPException(status_code=404, detail="没有这个单元")


@app.post("/api/chapters")
async def api_chapter_save(request: Request, x_admin_token: Optional[str] = Header(None)):
    """新增或覆盖一个单元（按 id 匹配，存在就覆盖）"""
    _check_token(x_admin_token)
    body = await request.json()
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="缺少 id")
    with DATA_LOCK:
        units = _read_units()
        idx = next((i for i, u in enumerate(units) if u.get("id") == body["id"]), -1)
        if idx >= 0:
            units[idx] = body
        else:
            units.append(body)
        _write_units(units)
    return {"ok": True, "count": len(units)}


@app.delete("/api/chapters/{chapter_id}")
def api_chapter_delete(chapter_id: str, x_admin_token: Optional[str] = Header(None)):
    _check_token(x_admin_token)
    with DATA_LOCK:
        units = [u for u in _read_units() if u.get("id") != chapter_id]
        _write_units(units)
    return {"ok": True, "count": len(units)}


@app.post("/api/chapters/reorder")
async def api_chapter_reorder(request: Request, x_admin_token: Optional[str] = Header(None)):
    """按传入的 id 数组重排顺序"""
    _check_token(x_admin_token)
    body = await request.json()
    order = body.get("ids") or []
    with DATA_LOCK:
        units = _read_units()
        by_id = {u.get("id"): u for u in units}
        new_units = [by_id[i] for i in order if i in by_id]
        for u in units:
            if u.get("id") not in order:
                new_units.append(u)
        _write_units(new_units)
    return {"ok": True}


# ================= 用户账号 + 学习进度（SQLite，无额外依赖） =================
import sqlite3
import uuid
from time import time as _now_ts

DB_FILE = os.getenv("DB_FILE", os.path.join(DATA_DIR, "app.db"))
USER_SECRET = os.getenv("USER_TOKEN_SECRET", "en-study-user-secret")


def _db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            uid TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            code_hash TEXT NOT NULL,
            phone TEXT DEFAULT '',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS progress(
            uid TEXT NOT NULL,
            chapter_id TEXT NOT NULL,
            max_score REAL DEFAULT 0,
            done_days TEXT DEFAULT '[]',
            modes TEXT DEFAULT '{}',
            last_study_at INTEGER DEFAULT 0,
            PRIMARY KEY (uid, chapter_id)
        );
        CREATE TABLE IF NOT EXISTS practice_state(
            uid TEXT NOT NULL,
            chapter_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            data TEXT DEFAULT '{}',
            updated_at INTEGER DEFAULT 0,
            PRIMARY KEY (uid, chapter_id, mode)
        );
        CREATE TABLE IF NOT EXISTS wrongbook(
            uid TEXT NOT NULL,
            en TEXT NOT NULL,
            zh TEXT DEFAULT '',
            chapter_id TEXT DEFAULT '',
            qtype TEXT DEFAULT '',
            prompt TEXT DEFAULT '',
            mine TEXT DEFAULT '',
            answer TEXT DEFAULT '',
            options TEXT DEFAULT '',
            done INTEGER DEFAULT 0,
            reviewed_at INTEGER DEFAULT 0,
            at INTEGER DEFAULT 0,
            PRIMARY KEY (uid, en)
        );
        CREATE TABLE IF NOT EXISTS settings(
            uid TEXT PRIMARY KEY,
            data TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS checkins(
            uid TEXT NOT NULL,
            day TEXT NOT NULL,
            at INTEGER DEFAULT 0,
            PRIMARY KEY (uid, day)
        );
        CREATE TABLE IF NOT EXISTS activity(
            uid TEXT NOT NULL,
            kind TEXT NOT NULL,
            at INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS user_cards(
            uid TEXT NOT NULL,
            card_id TEXT NOT NULL,
            chapter_id TEXT DEFAULT '',
            at INTEGER DEFAULT 0,
            PRIMARY KEY (uid, card_id)
        );
        CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT DEFAULT '',
            name TEXT DEFAULT '',
            text TEXT NOT NULL,
            at INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT 0
        );
        """
    )
    conn.commit()
    conn.close()


_init_db()


def _hash_code(code: str) -> str:
    return hashlib.sha256(("code:" + code).encode("utf-8")).hexdigest()


def _make_token(uid: str) -> str:
    sig = hashlib.sha256((uid + USER_SECRET).encode("utf-8")).hexdigest()[:20]
    return f"{uid}.{sig}"


def _uid_from_token(token: Optional[str]) -> str:
    if not token or "." not in token:
        raise HTTPException(status_code=401, detail="请先登录")
    uid, sig = token.rsplit(".", 1)
    if _make_token(uid).split(".")[1] != sig:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return uid


def _ensure_user_phone_col(conn):
    """老库补 phone 列（已有用户不受影响）"""
    try:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "phone" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''")
            conn.commit()
    except Exception:
        pass


def _ensure_user_gender_col(conn):
    """老库补 gender 列：空字符串=还没选过"""
    try:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "gender" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN gender TEXT DEFAULT ''")
            conn.commit()
    except Exception:
        pass


def _ensure_progress_modes_col(conn):
    try:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(progress)").fetchall()]
        if "modes" not in cols:
            conn.execute("ALTER TABLE progress ADD COLUMN modes TEXT DEFAULT '{}'")
            conn.commit()
    except Exception:
        pass


def _ensure_wrongbook_cols(conn):
    try:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(wrongbook)").fetchall()]
        want = {
            "qtype": "TEXT DEFAULT ''",
            "prompt": "TEXT DEFAULT ''",
            "mine": "TEXT DEFAULT ''",
            "answer": "TEXT DEFAULT ''",
            "options": "TEXT DEFAULT ''",
            "done": "INTEGER DEFAULT 0",
            "reviewed_at": "INTEGER DEFAULT 0",
        }
        for name, ddl in want.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE wrongbook ADD COLUMN {name} {ddl}")
        conn.commit()
    except Exception:
        pass


def _progress_map(uid: str) -> dict:
    conn = _db()
    _ensure_progress_modes_col(conn)
    rows = conn.execute("SELECT * FROM progress WHERE uid=?", (uid,)).fetchall()
    conn.close()
    out = {}
    for r in rows:
        try:
            days = json.loads(r["done_days"] or "[]")
        except Exception:
            days = []
        try:
            modes = json.loads(r["modes"] or "{}")
        except Exception:
            modes = {}
        out[r["chapter_id"]] = {
            "maxScore": r["max_score"] or 0,
            "doneDays": days,
            "modes": modes if isinstance(modes, dict) else {},
            "lastStudyAt": r["last_study_at"] or 0,
        }
    return out


@app.post("/api/feedback")
async def api_feedback(request: Request, x_token: Optional[str] = Header(None)):
    """用户意见反馈：存库，后台管理页可查"""
    uid = _uid_from_token(x_token) or ""
    body = await request.json()
    text = (body.get("text") or "").strip()[:500]
    if not text:
        raise HTTPException(status_code=400, detail="反馈内容不能为空")
    name = ""
    conn = _db()
    try:
        row = conn.execute("SELECT name FROM users WHERE uid=?", (uid,)).fetchone()
        if row:
            name = row["name"] or ""
        conn.execute(
            "INSERT INTO feedback(uid, name, text, at, created_at) VALUES (?,?,?,?,?)",
            (uid, name, text, int(body.get("at") or 0), int(_now_ts() * 1000)),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@app.post("/api/login")
async def api_login(request: Request):
    """昵称 + 口令登录；昵称不存在则自动注册"""
    body = await request.json()
    name = (body.get("name") or "").strip()
    code = (body.get("code") or "").strip()
    phone = (body.get("phone") or "").strip()
    if phone and (not phone.isdigit() or len(phone) != 11):
        raise HTTPException(status_code=400, detail="手机号要 11 位数字")
    if not name:
        raise HTTPException(status_code=400, detail="请填写昵称")
    if len(name) > 20:
        raise HTTPException(status_code=400, detail="昵称最多 20 个字")
    if len(code) < 4:
        raise HTTPException(status_code=400, detail="口令至少 4 位")

    conn = _db()
    _ensure_user_phone_col(conn)
    _ensure_user_gender_col(conn)
    row = conn.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
    if row:
        if row["code_hash"] != _hash_code(code):
            conn.close()
            raise HTTPException(status_code=401, detail="口令不对")
        uid = row["uid"]
        if phone and (row["phone"] or "") != phone:
            conn.execute("UPDATE users SET phone=? WHERE uid=?", (phone, uid))
            conn.commit()
    else:
        uid = uuid.uuid4().hex[:16]
        conn.execute(
            "INSERT INTO users(uid,name,code_hash,phone,created_at) VALUES(?,?,?,?,?)",
            (uid, name, _hash_code(code), phone, _now_ts()),
        )
        conn.commit()
    gender = (row["gender"] or "") if row else ""
    try:
        conn.execute(
            "INSERT INTO activity(uid, kind, at) VALUES (?,?,?)",
            (uid, "login", int(_now_ts() * 1000)),
        )
        conn.commit()
    except Exception:
        pass
    conn.close()
    return {"uid": uid, "name": name, "token": _make_token(uid), "gender": gender}


@app.get("/api/me")
def api_me(x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    conn = _db()
    _ensure_user_phone_col(conn)
    _ensure_user_gender_col(conn)
    row = conn.execute("SELECT name, phone, gender FROM users WHERE uid=?", (uid,)).fetchone()
    conn.close()
    return {
        "uid": uid,
        "name": row["name"] if row else "",
        "phone": (row["phone"] or "") if row else "",
        "gender": (row["gender"] or "") if row else "",
    }


@app.get("/api/words")
def api_words(offset: int = 0, limit: int = 10, x_token: Optional[str] = Header(None)):
    """学过的单词列表，分页给前端（每次默认 10 条）"""
    uid = _uid_from_token(x_token)
    offset = max(0, int(offset or 0))
    limit = min(50, max(1, int(limit or 10)))
    prog = _progress_map(uid)
    # 倒序：最近学的单元排前面（同单元内保持原来的单词顺序）
    studied = []
    for u in _read_units():
        p = prog.get(u.get("id")) or {}
        modes = p.get("modes") or {}
        if not isinstance(modes, dict) or not modes.get("study"):
            continue
        studied.append((p.get("lastStudyAt") or 0, str(u.get("id") or ""), u))
    studied.sort(key=lambda t: (t[0], t[1]), reverse=True)
    items = []
    for _ts, _cid, u in studied:
        title = u.get("title") or ""
        for w in (u.get("words") or []):
            if not isinstance(w, dict) or not w.get("en"):
                continue
            items.append(
                {
                    "en": w.get("en"),
                    "cn": w.get("cn") or "",
                    "sentence": w.get("sentence") or "",
                    "chapterId": u.get("id"),
                    "chapterTitle": title,
                }
            )
    total = len(items)
    page = items[offset : offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": page,
        "hasMore": offset + len(page) < total,
    }


@app.get("/api/progress")
def api_progress_get(x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    conn = _db()
    try:
        settings = json.loads(
            (conn.execute("SELECT data FROM settings WHERE uid=?", (uid,)).fetchone() or {"data": "{}"})["data"] or "{}"
        )
    except Exception:
        settings = {}
    _ensure_wrongbook_cols(conn)
    wrong = [
        {
            "en": r["en"],
            "zh": r["zh"],
            "chapterId": r["chapter_id"],
            "type": r["qtype"] or "",
            "prompt": r["prompt"] or "",
            "mine": r["mine"] or "",
            "answer": r["answer"] or "",
            "options": (json.loads(r["options"]) if r["options"] else []),
            "done": bool(r["done"]) if "done" in r.keys() else False,
            "at": r["at"],
        }
        for r in conn.execute("SELECT * FROM wrongbook WHERE uid=? ORDER BY at DESC LIMIT 100", (uid,)).fetchall()
    ]
    conn.close()
    return {"progress": _progress_map(uid), "wrong": wrong, "settings": settings}


@app.get("/api/state")
async def api_state_get(chapter_id: str = Query(None, alias="chapterId"), x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    conn = _db()
    rows = conn.execute(
        "SELECT mode,data,updated_at FROM practice_state WHERE uid=? AND chapter_id=?",
        (uid, chapter_id or ""),
    ).fetchall()
    conn.close()
    states = {}
    for r in rows:
        try:
            states[r["mode"]] = json.loads(r["data"] or "{}")
        except Exception:
            states[r["mode"]] = {}
    return {"ok": True, "states": states}


@app.post("/api/state")
async def api_state_save(request: Request, x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    body = await request.json()
    chapter_id = body.get("chapterId") or ""
    mode = body.get("mode") or ""
    if not mode:
        raise HTTPException(status_code=400, detail="缺少 mode")
    data = body.get("data") or {}
    conn = _db()
    conn.execute(
        "INSERT OR REPLACE INTO practice_state(uid,chapter_id,mode,data,updated_at) VALUES(?,?,?,?,?)",
        (uid, chapter_id, mode, json.dumps(data, ensure_ascii=False), int(_now_ts() * 1000)),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/progress")
async def api_progress_save(request: Request, x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    body = await request.json()
    chapter_id = body.get("chapterId")
    if not chapter_id:
        raise HTTPException(status_code=400, detail="缺少 chapterId")
    patch = body.get("patch") or {}
    conn = _db()
    _ensure_progress_modes_col(conn)
    row = conn.execute(
        "SELECT * FROM progress WHERE uid=? AND chapter_id=?", (uid, chapter_id)
    ).fetchone()
    max_score = row["max_score"] if row else 0
    done_days = json.loads(row["done_days"]) if row else []
    last_at = row["last_study_at"] if row else 0
    if patch.get("maxScore") is not None:
        max_score = max(max_score, patch["maxScore"])
    if patch.get("doneDays"):
        for d in patch["doneDays"]:
            if d not in done_days:
                done_days.append(d)
    try:
        old_modes = json.loads(row["modes"] or "{}") if row else {}
    except Exception:
        old_modes = {}
    if not isinstance(old_modes, dict):
        old_modes = {}
    if isinstance(patch.get("modes"), dict):
        old_modes.update(patch["modes"])

    last_at = int(_now_ts() * 1000)
    conn.execute(
        "INSERT OR REPLACE INTO progress(uid,chapter_id,max_score,done_days,modes,last_study_at) VALUES(?,?,?,?,?,?)",
        (
            uid,
            chapter_id,
            max_score,
            json.dumps(done_days, ensure_ascii=False),
            json.dumps(old_modes, ensure_ascii=False),
            last_at,
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "progress": _progress_map(uid).get(chapter_id)}


@app.post("/api/wrong")
async def api_wrong_add(request: Request, x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    body = await request.json()
    en = (body.get("en") or "").strip()
    if not en:
        raise HTTPException(status_code=400, detail="缺少 en")
    conn = _db()
    _ensure_wrongbook_cols(conn)
    conn.execute(
        "INSERT OR REPLACE INTO wrongbook(uid,en,zh,chapter_id,qtype,prompt,mine,answer,options,done,reviewed_at,at)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            uid,
            en,
            body.get("zh") or "",
            body.get("chapterId") or "",
            body.get("type") or "",
            body.get("prompt") or "",
            body.get("mine") or "",
            body.get("answer") or "",
            json.dumps(body.get("options") or [], ensure_ascii=False) if body.get("options") else "",
            int(body.get("done") or 0),
            0,
            int(_now_ts() * 1000),
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/wrong/done")
async def api_wrong_done(request: Request, x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    body = await request.json()
    keys = body.get("keys") or body.get("en") or []
    if isinstance(keys, str):
        keys = [keys]
    conn = _db()
    _ensure_wrongbook_cols(conn)
    now = int(_now_ts() * 1000)
    for k in keys:
        if not k:
            continue
        conn.execute(
            "UPDATE wrongbook SET done=1, reviewed_at=? WHERE uid=? AND en=?",
            (now, uid, k),
        )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/wrong")
def api_wrong_clear(x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    conn = _db()
    conn.execute("DELETE FROM wrongbook WHERE uid=?", (uid,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/settings")
async def api_settings_save(request: Request, x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    body = await request.json()
    conn = _db()
    conn.execute(
        "INSERT OR REPLACE INTO settings(uid,data) VALUES(?,?)",
        (uid, json.dumps(body, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _checkin_days(conn, uid: str) -> list:
    rows = conn.execute(
        "SELECT day FROM checkins WHERE uid=? ORDER BY day ASC", (uid,)
    ).fetchall()
    return [r["day"] for r in rows]


def _streak(days: list) -> int:
    """连续天数：从今天（或昨天）往前数"""
    if not days:
        return 0
    ds = set(days)
    d = datetime.now().date()
    if d.isoformat() not in ds:
        d = d - timedelta(days=1)
    n = 0
    while d.isoformat() in ds:
        n += 1
        d = d - timedelta(days=1)
    return n


def _ts_day(ts, default: int = 0):
    """把秒/毫秒时间戳转成本地日期字符串"""
    try:
        v = float(ts or 0)
    except Exception:
        return None
    if v <= 0:
        return None
    if v > 1e12:  # 毫秒
        v = v / 1000.0
    if v < 1e9:
        return None
    try:
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d")
    except Exception:
        return None


def _heal_checkins(conn, uid: str) -> list:
    """从学习活跃记录/进度里补回历史打卡（老版本只存在本地，服务端没有）"""
    days = set(_checkin_days(conn, uid))
    try:
        rows = conn.execute(
            "SELECT at FROM activity WHERE uid=? AND kind='study'", (uid,)
        ).fetchall()
        for r in rows:
            d = _ts_day(r["at"])
            if d:
                days.add(d)
    except Exception:
        pass
    try:
        rows = conn.execute(
            "SELECT last_study_at FROM progress WHERE uid=?", (uid,)
        ).fetchall()
        for r in rows:
            d = _ts_day(r["last_study_at"])
            if d:
                days.add(d)
    except Exception:
        pass
    today = _today_str()
    days = {d for d in days if d <= today}
    for d in days:
        conn.execute(
            "INSERT OR IGNORE INTO checkins(uid, day, at) VALUES (?,?,?)",
            (uid, d, int(_now_ts() * 1000)),
        )
    conn.commit()
    return sorted(days)


@app.get("/api/checkin")
def api_checkin_get(x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    conn = _db()
    try:
        days = _heal_checkins(conn, uid)
    finally:
        conn.close()
    return {"days": days, "streak": _streak(days), "today": _today_str()}


@app.post("/api/checkin")
async def api_checkin_post(request: Request, x_token: Optional[str] = Header(None)):
    """学完一节（单词或练习）就记一次打卡；可带 body.days 补录本机历史打卡"""
    uid = _uid_from_token(x_token)
    day = _today_str()
    backfill = []
    try:
        body = await request.json()
        if isinstance(body, dict):
            backfill = [d for d in (body.get("days") or []) if isinstance(d, str)][:400]
    except Exception:
        backfill = []
    today_d = datetime.now().date()
    valid = []
    for d in backfill:
        try:
            dd = datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            continue
        if dd <= today_d:
            valid.append(d)
    conn = _db()
    try:
        exists = conn.execute(
            "SELECT 1 FROM checkins WHERE uid=? AND day=?", (uid, day)
        ).fetchone()
        for d in valid:
            conn.execute(
                "INSERT OR IGNORE INTO checkins(uid, day, at) VALUES (?,?,?)",
                (uid, d, int(_now_ts() * 1000)),
            )
        conn.execute(
            "INSERT OR IGNORE INTO checkins(uid, day, at) VALUES (?,?,?)",
            (uid, day, int(_now_ts() * 1000)),
        )
        conn.execute(
            "INSERT INTO activity(uid, kind, at) VALUES (?,?,?)",
            (uid, "study", int(_now_ts() * 1000)),
        )
        conn.commit()
        days = _heal_checkins(conn, uid)
        return {"ok": True, "isNew": not exists, "days": days, "streak": _streak(days), "today": day}
    finally:
        conn.close()


@app.post("/api/activity")
def api_activity(x_token: Optional[str] = Header(None)):
    """只记录学习活跃（用于后台活跃度），不打卡"""
    uid = _uid_from_token(x_token)
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO activity(uid, kind, at) VALUES (?,?,?)",
            (uid, "study", int(_now_ts() * 1000)),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@app.post("/api/gender")
async def api_gender_save(request: Request, x_token: Optional[str] = Header(None)):
    """首次登录时选性别：只写一次，之后登录不再问"""
    uid = _uid_from_token(x_token)
    body = await request.json()
    gender = (body.get("gender") or "").strip()
    if gender not in ("boy", "girl"):
        raise HTTPException(status_code=400, detail="gender 只能是 boy 或 girl")
    conn = _db()
    try:
        _ensure_user_gender_col(conn)
        conn.execute("UPDATE users SET gender=? WHERE uid=?", (gender, uid))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "gender": gender}


# ---------------- 语音识别（本地 whisper，儿童单词朗读） ----------------
import subprocess
import tempfile

ASR_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asr_worker.py")
ASR_PYTHON = os.getenv("ASR_PYTHON") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "asr-venv", "bin", "python"
)
_asr_proc = None
_asr_lock = threading.Lock()


def _asr_start():
    """常驻子进程：模型只加载一次，后续识别 0.3~0.8s"""
    global _asr_proc
    if _asr_proc is not None and _asr_proc.poll() is None:
        return _asr_proc
    if not os.path.exists(ASR_PYTHON) or not os.path.exists(ASR_SCRIPT):
        raise HTTPException(status_code=503, detail="语音识别未安装")
    _asr_proc = subprocess.Popen(
        [ASR_PYTHON, ASR_SCRIPT, "--serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    return _asr_proc


def _asr_transcribe(path: str, prompt: Optional[str] = None) -> str:
    with _asr_lock:
        proc = _asr_start()
        payload = json.dumps({"path": path, "prompt": prompt or None}, ensure_ascii=False)
        proc.stdin.write(payload + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            raise HTTPException(status_code=503, detail="语音识别进程异常")
        data = json.loads(line)
        if not data.get("ok"):
            raise HTTPException(status_code=503, detail="语音识别失败")
        return data.get("text", "")


# ---------------- 百度智能云短语音识别（英文，dev_pid=1737） ----------------
BAIDU_ASR_KEY = os.getenv("BAIDU_ASR_KEY", "")
BAIDU_ASR_SECRET = os.getenv("BAIDU_ASR_SECRET", "")
_baidu_cache = {"token": "", "exp": 0}


def _baidu_token() -> str:
    import time
    import urllib.parse
    import urllib.request

    if _baidu_cache["token"] and _baidu_cache["exp"] > time.time() + 60:
        return _baidu_cache["token"]
    params = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": BAIDU_ASR_KEY,
            "client_secret": BAIDU_ASR_SECRET,
        }
    )
    url = "https://aip.baidubce.com/oauth/2.0/token?" + params
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=503, detail="百度语音 token 获取失败")
    _baidu_cache["token"] = token
    _baidu_cache["exp"] = time.time() + int(data.get("expires_in", 2592000))
    return token


def _baidu_asr(wav_path: str) -> str:
    import base64
    import urllib.request

    with open(wav_path, "rb") as f:
        raw = f.read()
    payload = {
        "format": "wav",
        "rate": 16000,
        "channel": 1,
        "cuid": "en-study-web",
        "token": _baidu_token(),
        "dev_pid": 1737,  # 英语模型
        "speech": base64.b64encode(raw).decode("utf-8"),
        "len": len(raw),
    }
    req = urllib.request.Request(
        "https://vop.baidu.com/server_api",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("err_no") != 0:
        code = data.get("err_no")
        # 3301/3302/3303/3304/3305/3307 之类是「音频没声音、太长、质量差」
        # 小朋友按早了、说太小声很常见，按「没听清」处理，不让前端报服务错误
        if code in (3301, 3302, 3303, 3304, 3305, 3307, 3310, 3311):
            return ""
        raise HTTPException(
            status_code=503, detail="百度识别失败(%s)：%s" % (code, data.get("err_msg", "unknown"))
        )
    return "".join(data.get("result") or []).strip()


def _norm_asr(v) -> str:
    raw = str(v or "").lower()
    keep = "".join(ch for ch in raw if ch.isalnum() or ch in " '")
    return " ".join(keep.split())


def _baidu_ready() -> bool:
    return bool(BAIDU_ASR_KEY and BAIDU_ASR_SECRET)


_wav_proc = None
_wav_lock = threading.Lock()


def _wav_start():
    """常驻转码进程：只启动一次，之后每次转码几十毫秒"""
    global _wav_proc
    if _wav_proc and _wav_proc.poll() is None:
        return _wav_proc
    try:
        _wav_proc = subprocess.Popen(
            [ASR_PYTHON, os.path.join(os.path.dirname(ASR_SCRIPT), "to_wav.py"), "--serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except Exception as e:  # noqa: BLE001
        print("[asr] 转码进程起不来: %s" % e, flush=True)
        _wav_proc = None
    return _wav_proc


def _to_wav(src: str, dst: str) -> bool:
    proc = _wav_start()
    if not proc:
        return False
    with _wav_lock:
        try:
            proc.stdin.write("%s\t%s\n" % (src, dst))
            proc.stdin.flush()
            line = proc.stdout.readline().strip()
            return line == "ok"
        except Exception as e:  # noqa: BLE001
            print("[asr] 转码通信失败: %s" % e, flush=True)
            global _wav_proc
            _wav_proc = None
            return False


def _wav_is_silent(path: str) -> bool:
    """整段几乎是静音就直接判“没听清”，不花百度调用次数"""
    try:
        import array
        import wave

        with wave.open(path, "rb") as w:
            data = array.array("h")
            data.frombytes(w.readframes(w.getnframes()))
        if not data:
            return True
        peak = max(abs(v) for v in data)
        return peak < 1200
    except Exception:  # noqa: BLE001
        return False


def _write_tmp(raw: bytes, suffix: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(raw)
    tmp.close()
    return tmp.name


def _whisper_ready() -> bool:
    return os.path.exists(ASR_PYTHON) and os.path.exists(ASR_SCRIPT)


def _sim(text: str, expect) -> float:
    if not text or not expect:
        return 0.0
    import difflib

    a, b = _norm_asr(text), _norm_asr(expect)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _wav_duration(path: str) -> float:
    try:
        import wave

        with wave.open(path, "rb") as w:
            return w.getnframes() / float(w.getframerate() or 16000)
    except Exception:  # noqa: BLE001
        return 0.0


def _asr_candidates(wav_path: str, expect) -> list:
    """whisper 与百度并行跑，互不拖慢：返回 [(text, engine, score)]"""
    out = []

    def _whisper():
        try:
            t = _asr_transcribe(wav_path, expect)
            if t:
                out.append((t, "whisper", _sim(t, expect)))
        except Exception as e:  # noqa: BLE001
            print("[asr] whisper 失败: %s" % e, flush=True)

    def _baidu():
        try:
            if _baidu_ready():
                t = _baidu_asr(wav_path)
                if t:
                    out.append((t, "baidu", _sim(t, expect)))
        except Exception as e:  # noqa: BLE001
            print("[asr] 百度失败: %s" % getattr(e, "detail", e), flush=True)

    threads = []
    for fn in (_whisper, _baidu):
        th = threading.Thread(target=fn, daemon=True)
        th.start()
        threads.append(th)
    for th in threads:
        th.join(timeout=60)
    return out


def _asr_work(raw: bytes, suffix: str, expect) -> tuple:
    """同步识别（放到线程里跑，避免阻塞事件循环）：返回 (text, engine, dur)

    先把录音统一转成 16k 单声道 wav 并做轻量降噪/增益，然后 whisper 与百度
    并行识别（whisper 带目标词提示，单个英文单词最准），取与目标词更接近的候选。
    录音过短（<0.55s，基本是没张开嘴就停了）直接判没听清，不浪费识别时间。
    """
    path = _write_tmp(raw, suffix)
    try:
        wav = path + ".wav"
        if not _to_wav(path, wav) or not os.path.exists(wav) or os.path.getsize(wav) < 800:
            print("[asr] 转码失败，按没听清处理", flush=True)
            return "", "none", 0.0
        dur = _wav_duration(wav)
        if dur < 0.30:
            print("[asr] 录音太短(%.2fs)，按没听清处理" % dur, flush=True)
            return "", "none", dur
        if _wav_is_silent(wav):
            print("[asr] 整段静音，按没听清处理", flush=True)
            return "", "none", dur
        cand = _asr_candidates(wav, expect)
        if not cand:
            return "", "none", dur
        best = max(cand, key=lambda c: (c[2], c[1] == "whisper"))
        print("[asr] 候选 %s 选中 %s (%.2fs)" % ([("%s:%s:%.2f" % c) for c in cand], best[1], dur), flush=True)
        return best[0], best[1], dur
    finally:
        for f in (path, path + ".wav"):
            try:
                os.unlink(f)
            except Exception:
                pass


@app.post("/api/asr")
async def api_asr(request: Request, expect: Optional[str] = Query(None)):
    """上传一段录音（原始二进制），返回识别出的英文（小朋友不用打字）

    expect：本次要说的目标词，用于结果相似度判定（本地模型还会当提示词用）
    识别引擎：配置了百度密钥走百度智能云，否则回退本地 whisper
    """
    ctype = (request.headers.get("content-type") or "").lower()
    suffix_map = {
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
        "audio/m4a": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
    }
    suffix = next((v for k, v in suffix_map.items() if k in ctype), ".webm")
    raw = await request.body()
    # 排查用：留最近 5 条原始录音，方便回听“到底录到了什么”
    try:
        dbg = os.path.join(tempfile.gettempdir(), "asr-dbg")
        os.makedirs(dbg, exist_ok=True)
        fn = os.path.join(dbg, "%s-%s%s" % (time.strftime("%H%M%S"), (expect or "x")[:12], suffix))
        with open(fn, "wb") as f:
            f.write(raw)
        files = sorted(os.listdir(dbg))
        for old in files[:-5]:
            os.unlink(os.path.join(dbg, old))
        print("[asr] 存档 %s %d bytes" % (fn, len(raw)), flush=True)
    except Exception as e:  # noqa: BLE001
        print("[asr] 存档失败: %s" % e, flush=True)
    if not raw:
        return {"ok": True, "text": "", "match": None, "score": 0.0, "engine": "none", "reason": "empty"}
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="录音太长")
    import asyncio

    text, engine, dur = await asyncio.to_thread(_asr_work, raw, suffix, expect)

    # 相似度判定：孩子说得含糊一点也算对
    match = None
    score = 0.0
    if expect:
        import difflib

        a, b = _norm_asr(text), _norm_asr(expect)
        if a and b:
            score = difflib.SequenceMatcher(None, a, b).ratio()
            if b in a or score >= 0.75:
                match = expect
                score = max(score, 0.9)
    return {"ok": True, "text": text, "match": match, "score": round(score, 2), "engine": engine, "dur": round(dur, 2)}


_warm_once = {"done": False}


@app.on_event("startup")
def _warm_asr_on_start():
    """服务一启动就在后台把 whisper 模型读进来，第一次识别不用干等"""
    global _warm_once
    if _warm_once["done"]:
        return
    _warm_once["done"] = True

    def _run():
        try:
            _asr_start()
            print("[asr] whisper 预热进程已拉起", flush=True)
        except Exception as e:  # noqa: BLE001
            print("[asr] whisper 预热失败: %s" % e, flush=True)

    threading.Thread(target=_run, daemon=True).start()


@app.get("/api/asr/status")
def api_asr_status():
    whisper_ok = _whisper_ready()
    ready = whisper_ok or _baidu_ready()
    engine = "whisper+baidu" if (whisper_ok and _baidu_ready()) else ("whisper" if whisper_ok else ("baidu" if _baidu_ready() else "none"))
    return {"ok": True, "enabled": ready, "engine": engine, "whisper": whisper_ok, "baidu": _baidu_ready()}


DOLL_IDS = ["doll%02d" % i for i in range(1, 9)]


def _owned_dolls(conn, uid: str) -> list:
    rows = conn.execute(
        "SELECT card_id FROM user_cards WHERE uid=? ORDER BY at ASC", (uid,)
    ).fetchall()
    return [r["card_id"] for r in rows]


@app.get("/api/cards")
def api_cards(x_token: Optional[str] = Header(None)):
    """我的娃娃卡（服务端保存，换手机也在）"""
    uid = _uid_from_token(x_token)
    conn = _db()
    try:
        owned = _owned_dolls(conn, uid)
    finally:
        conn.close()
    return {"owned": owned}


@app.post("/api/cards/award")
async def api_cards_award(request: Request, x_token: Optional[str] = Header(None)):
    """完成章节随机奖励一张娃娃卡：本章已发过则返回既有的，不重复发"""
    uid = _uid_from_token(x_token)
    body = await request.json()
    chapter_id = (body.get("chapterId") or "").strip()
    if not chapter_id:
        raise HTTPException(status_code=400, detail="缺少 chapterId")
    conn = _db()
    try:
        # 同一章只发一次
        row = conn.execute(
            "SELECT card_id FROM user_cards WHERE uid=? AND chapter_id=?", (uid, chapter_id)
        ).fetchone()
        if row:
            return {"cardId": row["card_id"], "isNew": False, "owned": _owned_dolls(conn, uid)}
        owned = _owned_dolls(conn, uid)
        pool = [c for c in DOLL_IDS if c not in owned] or DOLL_IDS
        import random
        card_id = random.choice(pool)
        conn.execute(
            "INSERT INTO user_cards(uid, card_id, chapter_id, at) VALUES (?,?,?,?)",
            (uid, card_id, chapter_id, int(_now_ts() * 1000)),
        )
        conn.commit()
        return {"cardId": card_id, "isNew": True, "owned": _owned_dolls(conn, uid)}
    finally:
        conn.close()


@app.get("/api/feedback/list")
def api_feedback_list(x_admin_token: Optional[str] = Header(None)):
    """后台：用户意见反馈列表（新的在前）"""
    _check_token(x_admin_token)
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, uid, name, text, at, created_at FROM feedback ORDER BY id DESC LIMIT 500"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@app.delete("/api/feedback/{fid}")
def api_feedback_delete(fid: int, x_admin_token: Optional[str] = Header(None)):
    _check_token(x_admin_token)
    conn = _db()
    try:
        conn.execute("DELETE FROM feedback WHERE id=?", (fid,))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@app.get("/api/users")
def api_users(x_admin_token: Optional[str] = Header(None)):
    """管理端：查看所有学员及学习情况"""
    _check_token(x_admin_token)
    conn = _db()
    _ensure_user_phone_col(conn)
    _ensure_user_gender_col(conn)
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    rows = conn.execute("SELECT * FROM progress").fetchall()
    by_uid = {}
    for r in rows:
        by_uid.setdefault(r["uid"], []).append(r)
    acts = conn.execute("SELECT uid, kind, MAX(at) AS last FROM activity GROUP BY uid, kind").fetchall()
    last_login = {}
    last_study = {}
    for a in acts:
        if a["kind"] == "login":
            last_login[a["uid"]] = a["last"] or 0
        else:
            last_study[a["uid"]] = a["last"] or 0

    now_ms = int(_now_ts() * 1000)
    day_ms = 86400000

    def status_of(uid, progress_last):
        # 活跃：最近 7 天有学习（单词/练习）
        study_at = max(last_study.get(uid, 0), progress_last or 0)
        login_at = last_login.get(uid, 0)
        if study_at and now_ms - study_at <= 7 * day_ms:
            return "active", study_at
        # 半活跃：最近 7 天只是登录，没学习
        if login_at and now_ms - login_at <= 7 * day_ms:
            return "half", study_at
        # 不活跃：7 天内既没学习也没登录
        return "silent", study_at

    out = []
    for u in users:
        items = by_uid.get(u["uid"], [])
        progress_last = max([i["last_study_at"] or 0 for i in items], default=0)
        st, study_at = status_of(u["uid"], progress_last)
        out.append(
            {
                "uid": u["uid"],
                "name": u["name"],
                "phone": (u["phone"] or "") if "phone" in u.keys() else "",
                "gender": (u["gender"] or "") if "gender" in u.keys() else "",
                "createdAt": u["created_at"],
                "status": st,
                "lastStudyAt": int(study_at) if study_at else 0,
                "lastLoginAt": last_login.get(u["uid"], 0),
                "chapterCount": len([i for i in items if (i["max_score"] or 0) > 0]),
                "chapters": {i["chapter_id"]: i["max_score"] for i in items},
            }
        )
    conn.close()
    return JSONResponse(out)


@app.delete("/api/users/{uid}")
def api_user_delete(uid: str, x_admin_token: Optional[str] = Header(None)):
    _check_token(x_admin_token)
    conn = _db()
    conn.execute("DELETE FROM users WHERE uid=?", (uid,))
    conn.execute("DELETE FROM progress WHERE uid=?", (uid,))
    conn.execute("DELETE FROM wrongbook WHERE uid=?", (uid,))
    conn.execute("DELETE FROM settings WHERE uid=?", (uid,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ===== 管理后台（React + Ant Design，构建产物 admin-app/dist） =====
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

ADMIN_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin-app", "dist")


@app.get("/admin")
def admin_redirect():
    return RedirectResponse(url="/admin/")


if os.path.isdir(ADMIN_DIST):
    app.mount("/admin", StaticFiles(directory=ADMIN_DIST, html=True), name="admin")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
