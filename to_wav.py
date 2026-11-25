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
    """去底噪：一阶高通去低频嗡声 + 幅度谱减法（谱减法是给 ASR 提准确率最稳的一档）

    步骤：25ms 帧 / 10ms 移，汉宁窗；用能量最低的 20% 帧估噪声谱；
    每个频点按噪声幅度做软减（保留 25% 残量，避免"水声"和吞辅音）。
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
        # 1) 高通 80Hz
        rc = 1.0 / (2 * np.pi * 80.0)
        dt = 1.0 / rate
        alpha = rc / (rc + dt)
        y = np.empty_like(x)
        px = 0.0
        py = 0.0
        for i in range(len(x)):
            cur = x[i]
            py = alpha * (py + cur - px)
            px = cur
            y[i] = py

        # 2) 谱减法
        n_fft = 512
        hop = 256
        if len(y) >= n_fft:
            win = np.hanning(n_fft).astype(np.float32)
            frames = []
            for i in range(0, len(y) - n_fft + 1, hop):
                frames.append(y[i : i + n_fft])
            if len(frames) > 3:
                spec = np.fft.rfft(np.array(frames) * win, axis=1)
                mag = np.abs(spec)
                energy = mag.sum(axis=1)
                quiet = np.argsort(energy)[: max(1, int(len(energy) * 0.2))]
                noise = np.median(mag[quiet], axis=0)
                clean_mag = np.maximum(mag - noise * 1.2, mag * 0.25)
                cleaned = np.fft.irfft(clean_mag * np.exp(1j * np.angle(spec)), axis=1) * win
                # 重叠相加
                out = np.zeros(len(y), dtype=np.float32)
                for idx, fr in enumerate(cleaned):
                    i = idx * hop
                    out[i : i + n_fft] += fr
                # 补偿窗的重叠能量
                wsum = np.zeros(len(y), dtype=np.float32)
                for idx in range(len(cleaned)):
                    i = idx * hop
                    wsum[i : i + n_fft] += win ** 2
                wsum[wsum < 1e-6] = 1.0
                y = out / wsum
            y = np.clip(y, -32768, 32767)
        out_i = np.clip(y, -32768, 32767).astype(np.int16)
        with wave.open(dst, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(out_i.tobytes())
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
