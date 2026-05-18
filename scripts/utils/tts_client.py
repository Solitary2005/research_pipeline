import os
import asyncio
import tempfile
import subprocess
from pathlib import Path
from .config import Config, ConfigError


class TTSClient:
    def __init__(self, backend, config: Config):
        self.backend = backend
        self.config = config

    def generate_audio(self, text, output_path):
        if self.backend == "edge":
            asyncio.run(self._generate_edge(text, output_path))
        elif self.backend == "openai":
            self._generate_openai(text, output_path)
        else:
            raise ConfigError(f"Unknown TTS backend: {self.backend}")

        duration = self._get_duration(output_path)
        return duration

    async def _generate_edge(self, text, output_path):
        import edge_tts

        chunks = self._split_text(text, max_chars=3000)
        chunk_files = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(tmpdir, f"chunk_{i:04d}.mp3")
                communicate = edge_tts.Communicate(
                    chunk,
                    "zh-CN-XiaoxiaoNeural",
                    rate="-5%",
                )
                await communicate.save(chunk_path)
                chunk_files.append(chunk_path)

            if len(chunk_files) == 1:
                os.rename(chunk_files[0], output_path)
            else:
                concat_list = os.path.join(tmpdir, "concat.txt")
                with open(concat_list, "w") as f:
                    for cf in chunk_files:
                        f.write(f"file '{cf}'\n")
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                     "-i", concat_list, "-acodec", "libmp3lame",
                     "-b:a", "64k", output_path],
                    capture_output=True, check=True
                )

    def _generate_openai(self, text, output_path):
        api_key = self.config.require_key("openai_api_key")
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        chunks = self._split_text(text, max_chars=4000)
        chunk_files = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(tmpdir, f"chunk_{i:04d}.mp3")
                response = client.audio.speech.create(
                    model="tts-1-hd",
                    voice="nova",
                    input=chunk,
                    speed=0.95,
                )
                response.stream_to_file(chunk_path)
                chunk_files.append(chunk_path)

            if len(chunk_files) == 1:
                os.rename(chunk_files[0], output_path)
            else:
                concat_list = os.path.join(tmpdir, "concat.txt")
                with open(concat_list, "w") as f:
                    for cf in chunk_files:
                        f.write(f"file '{cf}'\n")
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                     "-i", concat_list, "-acodec", "libmp3lame",
                     "-b:a", "64k", output_path],
                    capture_output=True, check=True
                )

    def _split_text(self, text, max_chars=3000):
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n")
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 1 <= max_chars:
                current = (current + "\n" + para).strip()
            else:
                if current:
                    chunks.append(current)
                if len(para) > max_chars:
                    sentences = para.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n")
                    for sent in sentences:
                        if len(current) + len(sent) + 1 <= max_chars:
                            current = (current + sent).strip()
                        else:
                            if current:
                                chunks.append(current)
                            current = sent
                else:
                    current = para

        if current:
            chunks.append(current)

        return chunks

    def _get_duration(self, audio_path):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                 audio_path],
                capture_output=True, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0
