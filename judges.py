"""LLM-as-judge scoring. Every score ships with a one-line justification."""
import json
import os
import urllib.request

RUBRIC = """Score this vendor output for the task below, 0-5:
5: complete, correct, directly usable by an agent with no cleanup
4: correct with minor noise (boilerplate, truncation)
3: partially correct or incomplete but usable with retries
2: mostly unusable (wrong page, heavy noise)
0-1: missing, wrong, or hallucinated
Reply with JSON only: {"score": <int>, "why": "<one line>"}"""

JUDGE_URL = os.environ.get("JUDGE_BASE_URL", "https://api.openai.com/v1") + "/chat/completions"
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o-mini")


def judge(task: dict, output: str) -> dict:
    """Return {'score': int|None, 'why': str}. Score is None when unparseable."""
    key = os.environ["JUDGE_API_KEY"]
    body = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content":
                f"TASK: {json.dumps(task)}\nEXPECTED: {task.get('expect', '')}\n"
                f"VENDOR OUTPUT (truncated to 4000 chars):\n{output[:4000]}"},
        ],
        "temperature": 0,
    }
    req = urllib.request.Request(
        JUDGE_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = json.loads(r.read())["choices"][0]["message"]["content"]
    try:
        out = json.loads(text[text.find("{"): text.rfind("}") + 1])
        return {"score": int(out["score"]), "why": str(out.get("why", ""))[:200]}
    except (ValueError, KeyError):
        return {"score": None, "why": "judge output unparseable: " + text[:150]}
