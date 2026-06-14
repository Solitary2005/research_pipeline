import os
import asyncio
import tempfile
import subprocess
import threading
from pathlib import Path
from .config import Config, ConfigError


class TTSClient:
    def __init__(self, backend: str, config: Config) -> None:
        self.backend = backend
        self.config = config

    def generate_audio(self, text: str, output_path: str) -> float:
        if self.backend == "edge":
            self._run_async(self._generate_edge(text, output_path))
        elif self.backend == "openai":
            self._generate_openai(text, output_path)
        else:
            raise ConfigError(f"Unknown TTS backend: {self.backend}")

        duration = self._get_duration(output_path)
        return duration

    def _run_async(self, coro):
        """Run an async coroutine safely — even from within a running event loop.

        Uses a background thread with its own event loop when the calling context
        already has one (e.g. Jupyter notebooks, some CI environments).
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop — safe to call asyncio.run() directly
            return asyncio.run(coro)

        # Already inside a running event loop — spawn a dedicated thread
        result = None
        error: Exception | None = None

        def _runner() -> None:
            nonlocal result, error
            try:
                result = asyncio.run(coro)
            except Exception as e:
                error = e

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()
        if error is not None:
            raise error
        return result

    async def _generate_edge(self, text, output_path):
        import edge_tts

        chunks = self._split_text(text, max_chars=3000)
        chunk_files = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(tmpdir, f"chunk_{i:04d}.mp3")
                communicate = edge_tts.Communicate(
                    chunk,
                    self.config.tts_edge_voice,
                    rate=self.config.tts_edge_rate,
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
                    model=self.config.tts_openai_model,
                    voice=self.config.tts_openai_voice,
                    input=chunk,
                    speed=self.config.tts_openai_speed,
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
