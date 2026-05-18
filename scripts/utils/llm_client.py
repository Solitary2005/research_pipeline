import json
from .config import Config, ConfigError


class LLMClient:
    def __init__(self, backend, config: Config):
        self.backend = backend
        self.config = config

        if backend == "claude":
            api_key = config.require_key("anthropic_api_key")
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-6"
        elif backend == "openai":
            api_key = config.require_key("openai_api_key")
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o"
        elif backend == "deepseek":
            api_key = config.require_key("deepseek_api_key")
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            self.model = "deepseek-chat"
        else:
            raise ConfigError(f"Unknown LLM backend: {backend}")

    def generate_summary(self, paper_info, paper_text):
        system_prompt = (
            "You are a senior research assistant in robotics and computer vision. "
            "Read the provided paper and produce a structured summary in English. "
            "Be precise, use technical terminology, and avoid fluff. "
            "Return ONLY a JSON object with the following keys: "
            "motivation (why this problem matters), "
            "method (proposed approach and key innovation), "
            "key_results (main findings and metrics), "
            "takeaways (broader implications for the field). "
            "Each value should be 2-5 sentences in English."
        )

        title = paper_info.get("title", "Unknown")
        abstract = paper_info.get("abstract", "")
        text_excerpt = paper_text[:8000] if len(paper_text) > 8000 else paper_text

        user_prompt = f"""Paper Title: {title}
Abstract: {abstract}

Full text excerpt (first {len(text_excerpt)} chars):
{text_excerpt}

Based on the above, produce a structured JSON summary."""

        response = self._call_llm(system_prompt, user_prompt, max_tokens=1500)
        return self._parse_json_response(response)

    def generate_podcast_script(self, paper_info, summary, paper_text):
        import random
        target_words = random.randint(2500, 4000)

        system_prompt = (
            "You are a professional science communicator who creates engaging Chinese-language "
            "podcast scripts about robotics and AI research papers. "
            f"Write a podcast script in Chinese of approximately {target_words} Chinese characters. "
            "The script should be natural spoken Mandarin, mixing in English technical terms "
            "where appropriate (e.g., 'grasping', 'dexterous manipulation', 'reinforcement learning'). "
            "Structure the script as: "
            "1) Opening greeting and paper intro (~10% of length) "
            "2) Problem motivation and background (~20%) "
            "3) Method explanation in accessible terms (~30%) "
            "4) Key results and analysis (~20%) "
            "5) Strengths, limitations, and field impact (~15%) "
            "6) Closing remarks (~5%). "
            "Use conversational phrases like '各位听众朋友大家好', '我们来看一下', '值得注意的是', "
            "'总结一下', '感谢收听，我们下期再见'. "
            "Do NOT simply read the paper — explain and interpret it. "
            "Return ONLY the podcast script text, no meta-commentary."
        )

        title = paper_info.get("title", "Unknown")
        abstract = paper_info.get("abstract", "")
        summary_text = json.dumps(summary, ensure_ascii=False, indent=2)
        text_excerpt = paper_text[:5000] if len(paper_text) > 5000 else paper_text

        user_prompt = f"""Paper Title: {title}
Abstract: {abstract}

English Summary:
{summary_text}

Full text excerpt (first {len(text_excerpt)} chars):
{text_excerpt}

Write a Chinese podcast script (~{target_words} characters) based on the above."""

        return self._call_llm(system_prompt, user_prompt, max_tokens=6000)

    def _call_llm(self, system_prompt, user_prompt, max_tokens=1500):
        if self.backend == "claude":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content

    def _parse_json_response(self, text):
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if lines[0].startswith("```") else text
            if text.endswith("```"):
                text = text[:-3]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"raw_response": text}
