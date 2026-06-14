import json
import sys
import time
from .config import Config, ConfigError

# Default model per backend — used when user has not overridden in settings.yaml
_DEFAULT_MODELS: dict[str, str] = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "deepseek": "deepseek-chat",
}


def _is_retryable(error: Exception) -> bool:
    """True if this error is likely transient (network / rate-limit / server).

    Authentication errors and invalid-request errors are NOT retryable — retrying
    would just waste attempts on a problem that will not self-repair.
    """
    error_str = str(error).lower()
    transient_markers = [
        "timeout", "timed out", "connection", "rate limit", "rate_limit",
        "server error", "503", "502", "504", "overloaded", "capacity",
        "too many requests", "429", "internal server error",
    ]
    non_retryable = [
        "401", "403", "invalid api key", "authentication", "not found",
        "invalid request", "permission",
    ]
    for marker in non_retryable:
        if marker in error_str:
            return False
    for marker in transient_markers:
        if marker in error_str:
            return True
    # Default to retryable for unknown errors (safer than silently failing)
    return True


class LLMClient:
    def __init__(self, backend: str, config: Config) -> None:
        self.backend = backend
        self.config = config

        if backend == "claude":
            api_key = config.require_key("anthropic_api_key")
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        elif backend == "openai":
            api_key = config.require_key("openai_api_key")
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif backend == "deepseek":
            api_key = config.require_key("deepseek_api_key")
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        else:
            raise ConfigError(f"Unknown LLM backend: {backend}")

        # Model name: user override > per-backend default
        self.model: str = config.llm_models.get(backend, _DEFAULT_MODELS.get(backend, ""))
        if not self.model:
            raise ConfigError(f"No model configured for LLM backend: {backend}")

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
            "You are a senior AI researcher hosting a deeply technical, objective podcast in Chinese. "
            "Your goal is to deliver a precise, fact-based, and detail-rich summary and analysis of a "
            "research paper. You must not add personal emotions, hype, or storytelling fluff. "
            "Every statement should be grounded in the paper's content."
            "Write a podcast script in Chinese of approximately 3000-4000 Chinese characters (about 15-20 "
            "minutes spoken). The script must be natural spoken Mandarin, mixing in English technical terms "
            "where appropriate (e.g., 'grasping', 'dexterous manipulation', 'reinforcement learning', "
            "'transformer', 'latent space')."
            "Structure the script as follows:"
            "1) Opening and precise paper introduction (title, authors, core contribution) (~8%)"
            "2) Problem formulation and background: clearly define the problem setting, notations if crucial, "
            "and prior work with specific limitations this paper addresses (~15%)"
            "3) In-depth technical method explanation (~40%):"
            "- Elaborate the overall pipeline or system architecture"
            "- Describe key components (e.g., network modules, perception pipelines, control policies) "
                "with concrete configurations (layers, dimensions, activation functions, etc.)"
            "- Detail the training procedure (e.g., reinforcement learning algorithm, loss functions, "
                "optimization settings, dataset sizes, simulation environments)"
            "- If the paper introduces a new algorithm or mathematical formulation, explain it step by "
                "step in accessible yet rigorous terms, not skipping the logic"
            "- Avoid vague metaphors; use the paper's own precise descriptions where possible"
            "4) Key results and quantitative analysis (~22%):"
            "- Report main results with exact numbers (success rates, accuracy, time, etc.) and "
                "comparison with baselines"
            "- Cover ablation studies and their conclusions to show which components matter"
            "- Explain any surprising or counter-intuitive findings objectively"
            "5) Strengths, limitations, and impact (~10%):"
            "- State strengths strictly supported by evidence in the paper"
            "- Mention limitations as acknowledged by the authors, and any design choices that may " 
                "affect generalization"
            "- Discuss field impact based on the paper's claims and your objective view of where it "
                "moves the community, without exaggeration"
            "6) Closing remarks (~5%): succinct summary of the take-home message."

            "Style requirements:"
            "- Use conversational but restrained phrases: '各位听众朋友大家好', '我们来看一下', '值得注意的是'," 
            "'总结一下', '感谢收听，我们下期再见'."
            "- Do NOT say things like “这是令人兴奋的突破” or “非常惊人”. Just present the facts."
            "- If the paper compares methods A and B, present the numbers and let the comparison speak "
            "for itself."
            "- Keep the language clear and professional, as in a serious technical seminar."

            "CRITICAL: Do NOT simply read the paper; explain it with full technical depth. "
            "Do NOT dilute the content for a general audience. Assume the listener is familiar with "
            "machine learning/robotics fundamentals."

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

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        max_retries: int = 3,
        timeout: float = 120.0,
    ) -> str:
        """Call the LLM with retry on transient failures.

        Uses exponential backoff (3s, 6s, 12s) between retries. Network errors,
        rate limits, and server errors trigger a retry; authentication errors
        and invalid requests do not and will raise immediately.
        """
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                if self.backend == "claude":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                        timeout=timeout,
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
                        timeout=timeout,
                    )
                    return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1 and _is_retryable(e):
                    wait = 2 ** attempt * 3
                    print(
                        f"[llm] API call failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait}s: {e}",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                elif not _is_retryable(e):
                    raise
        raise ConfigError(
            f"LLM API call failed after {max_retries} attempts: {last_error}"
        )

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
