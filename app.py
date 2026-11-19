import os


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
            at INTEGER DEFAULT 0,
            PRIMARY KEY (uid, en)
        );
        CREATE TABLE IF NOT EXISTS settings(
            uid TEXT PRIMARY KEY,
            data TEXT DEFAULT '{}'
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


def _ensure_progress_modes_col(conn):
    try:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(progress)").fetchall()]
        if "modes" not in cols:
            conn.execute("ALTER TABLE progress ADD COLUMN modes TEXT DEFAULT '{}'")
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
    conn.close()
    return {"uid": uid, "name": name, "token": _make_token(uid)}


@app.get("/api/me")
def api_me(x_token: Optional[str] = Header(None)):
    uid = _uid_from_token(x_token)
    conn = _db()
    _ensure_user_phone_col(conn)
    row = conn.execute("SELECT name, phone FROM users WHERE uid=?", (uid,)).fetchone()
    conn.close()
    return {"uid": uid, "name": row["name"] if row else "", "phone": (row["phone"] or "") if row else ""}


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
    wrong = [
        {"en": r["en"], "zh": r["zh"], "chapterId": r["chapter_id"], "at": r["at"]}
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
    conn.execute(
        "INSERT OR REPLACE INTO wrongbook(uid,en,zh,chapter_id,at) VALUES(?,?,?,?,?)",
        (uid, en, body.get("zh") or "", body.get("chapterId") or "", int(_now_ts() * 1000)),
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
        raise HTTPException(
            status_code=503, detail="百度识别失败：%s" % data.get("err_msg", "unknown")
        )
    return "".join(data.get("result") or []).strip()


def _norm_asr(v) -> str:
    raw = str(v or "").lower()
    keep = "".join(ch for ch in raw if ch.isalnum() or ch in " '")
    return " ".join(keep.split())


def _baidu_ready() -> bool:
    return bool(BAIDU_ASR_KEY and BAIDU_ASR_SECRET)


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
    if not raw:
        raise HTTPException(status_code=400, detail="缺少录音数据")
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="录音太长")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(raw)
    tmp.close()
    engine = "whisper"
    try:
        if _baidu_ready():
            engine = "baidu"
            # 百度要求 16k / 16bit / 单声道 wav，先转码
            wav_path = tmp.name + ".wav"
            conv = subprocess.run(
                [ASR_PYTHON, os.path.join(os.path.dirname(ASR_SCRIPT), "to_wav.py"), tmp.name, wav_path],
                capture_output=True,
                timeout=30,
            )
            if conv.returncode != 0:
                raise HTTPException(status_code=503, detail="录音转码失败")
            try:
                text = _baidu_asr(wav_path)
            finally:
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass
        else:
            text = _asr_transcribe(tmp.name, expect)
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

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
    return {"ok": True, "text": text, "match": match, "score": round(score, 2), "engine": engine}


@app.get("/api/asr/status")
def api_asr_status():
    ready = _baidu_ready() or (os.path.exists(ASR_PYTHON) and os.path.exists(ASR_SCRIPT))
    return {"ok": True, "enabled": ready, "engine": "baidu" if _baidu_ready() else "whisper"}


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
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    rows = conn.execute("SELECT * FROM progress").fetchall()
    by_uid = {}
    for r in rows:
        by_uid.setdefault(r["uid"], []).append(r)
    out = []
    for u in users:
        items = by_uid.get(u["uid"], [])
        out.append(
            {
                "uid": u["uid"],
                "name": u["name"],
                "createdAt": u["created_at"],
                "chapterCount": len([i for i in items if (i["max_score"] or 0) > 0]),
                "lastStudyAt": max([i["last_study_at"] or 0 for i in items], default=0),
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
