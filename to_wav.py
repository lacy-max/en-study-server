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


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
