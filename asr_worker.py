"""
语音识别 sidecar：被 app.py 用 asr-venv 的 Python 调起来（子进程方式）

用法：python asr_worker.py <audio_path> [language]
输出：一行 JSON，例如 {"text": "see you soon"}

模型只在第一次调用时加载，之后常驻（由 app.py 的常驻连接复用）
"""
import json
import os
import sys

MODEL_SIZE = os.environ.get("ASR_MODEL", "base.en")

_model = None


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"),
        )
    return _model


def transcribe(path, language="en", prompt=None):
    """prompt 用来“提示”当前要听的目标词，能显著提升儿童短句的准确率"""
    model = get_model()
    kw = dict(
        language=language,
        beam_size=3,
        condition_on_previous_text=False,
        initial_prompt=prompt or None,
    )
    try:
        segments, _info = model.transcribe(path, vad_filter=True, **kw)
    except Exception:
        # 没装 onnxruntime 时 silero VAD 不可用：前端已经做过静音截止，直接关掉 VAD
        segments, _info = model.transcribe(path, vad_filter=False, **kw)
    text = "".join(seg.text for seg in segments).strip()
    return text


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        # 常驻模式：每行一个音频路径，输出一行 JSON（模型只加载一次）
        for line in sys.stdin:
            raw = line.strip()
            if not raw:
                continue
            audio = raw
            prompt = None
            if raw.startswith("{"):
                try:
                    req = json.loads(raw)
                    audio = req.get("path") or ""
                    prompt = req.get("prompt") or None
                except Exception:
                    continue
            try:
                result = transcribe(audio, "en", prompt)
                print(json.dumps({"text": result, "ok": True}, ensure_ascii=False), flush=True)
            except Exception as e:  # noqa
                print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), flush=True)
        sys.exit(0)

    audio = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    try:
        result = transcribe(audio, lang)
        print(json.dumps({"text": result, "ok": True}, ensure_ascii=False))
    except Exception as e:  # noqa
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
