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


@app.get("/admin")
def admin_page():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin", "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return Response(status_code=404, content=b"admin page missing")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
