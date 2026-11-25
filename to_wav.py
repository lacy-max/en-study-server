"""
把任意录音（webm / m4a / mp3 / wav）转成百度短语音识别要求的 16k / 16bit / 单声道 WAV。

用法：python to_wav.py <input> <output.wav>
依赖：av（PyAV，faster-whisper 自带，无需额外安装）
"""
import sys

import av
from av.audio.resampler import AudioResampler


def convert(src: str, dst: str, rate: int = 16000) -> None:
    inp = av.open(src)
    stream = inp.streams.audio[0]
    resampler = AudioResampler(format="s16", layout="mono", rate=rate)

    out = av.open(dst, "w")
    out_stream = out.add_stream("pcm_s16le", rate=rate)
    out_stream.layout = "mono"

    for frame in inp.decode(stream):
        for rf in resampler.resample(frame):
            for packet in out_stream.encode(rf):
                out.mux(packet)

    for packet in out_stream.encode(None):
        out.mux(packet)

    out.close()
    inp.close()


def polish(dst: str, rate: int = 16000) -> None:
    """去掉首尾静音、把音量拉到合适，孩子小声读也能识别"""
    import array
    import wave

    with wave.open(dst, "rb") as w:
        n = w.getnframes()
        data = array.array("h")
        data.frombytes(w.readframes(n))
    if not data:
        return
    peak = max(abs(v) for v in data) or 1
    thr = max(300, int(peak * 0.12))
    i = 0
    while i < len(data) and abs(data[i]) < thr:
        i += 1
    j = len(data) - 1
    while j > i and abs(data[j]) < thr:
        j -= 1
    if j - i < rate * 0.2:  # 几乎全是静音，原样返回
        return
    pad = int(rate * 0.25)
    start = max(0, i - pad)
    end = min(len(data), j + pad)
    seg = data[start:end]
    seg_peak = max(abs(v) for v in seg) or 1
    if seg_peak < 4500:  # 偏小声才放大，且最多 2 倍，避免削波失真反而识别不准
        gain = min(2.0, 5000 / seg_peak)
        for k in range(len(seg)):
            v = int(seg[k] * gain)
            seg[k] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
    with wave.open(dst, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(seg.tobytes())


def denoise(dst: str, rate: int = 16000) -> None:
    """去底噪 + 去低频嗡声：给识别引擎一段干净的语音

    做法很轻量：一阶高通滤掉 80Hz 以下的空调/电机噪声，再按 20ms 分帧做
    软噪声门——比整体 RMS 明显小的帧按比例压低，句间杂音基本消失，
    但保留气音和尾音，不会把轻声的辅音一起吃掉。
    """
    try:
        import array
        import wave

        import numpy as np
    except Exception:  # noqa: BLE001
        return
    try:
        with wave.open(dst, "rb") as w:
            data = array.array("h")
            data.frombytes(w.readframes(w.getnframes()))
        if not data:
            return
        x = np.asarray(data, dtype=np.float32)
        # 一阶高通（去 DC 与低频嗡嗡声）
        rc = 1.0 / (2 * np.pi * 80.0)
        dt = 1.0 / rate
        alpha = rc / (rc + dt)
        y = np.empty_like(x)
        prev_x = 0.0
        prev_y = 0.0
        for i in range(len(x)):  # 16k 点级循环，最长 5 秒，开销可接受
            cur = x[i]
            prev_y = alpha * (prev_y + cur - prev_x)
            prev_x = cur
            y[i] = prev_y
        # 分帧软噪声门
        hop = int(rate * 0.02)
        n = len(y) // hop
        if n > 4:
            frames = y[: n * hop].reshape(n, hop)
            rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-9)
            # 取最小的 20% 帧作为底噪估计
            floor = float(np.percentile(rms, 20))
            peak_level = float(np.percentile(rms, 90))
            # 底噪估计接近语音本身（短词/整段都在说话）时不要开噪声门，否则会把语音一起压掉
            if floor < peak_level * 0.45:
                gate = max(floor * 2.5, peak_level * 0.08, 30.0)
                for i in range(n):
                    if rms[i] < gate:
                        frames[i] *= 0.25
                y[: n * hop] = frames.reshape(-1)
        out = np.clip(y, -32768, 32767).astype(np.int16)
        with wave.open(dst, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(out.tobytes())
    except Exception as e:  # noqa: BLE001
        print("denoise skip: %s" % e, flush=True)


def serve() -> None:
    """常驻模式：避免每次转码都付 5 秒的 python 启动+导入成本。
    读 stdin 每行 "src\tdst"，转好回 "ok"，失败回 "err:..."。
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            src, dst = line.split("\t")
        except ValueError:
            print("err:bad-line", flush=True)
            continue
        try:
            convert(src, dst)
            polish(dst)
            denoise(dst)
            print("ok", flush=True)
        except Exception as e:  # noqa: BLE001
            print("err:%s" % e, flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        serve()
    else:
        convert(sys.argv[1], sys.argv[2])
        polish(sys.argv[2])
