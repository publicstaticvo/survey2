import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utility.tool_config import LLMServerInfo


def main():
    # info = LLMServerInfo(
    #     base_url="https://api.minimaxi.com",
    #     api_key="sk-cp-ABpuEQq2ZgE3Qx7vDg_fqXO23VrQ1nhYM3eyBeYtPRuOWoUffj_IDXA-efdcWvR3dVKnjPob5mBTRJbm0tkKlN4FzDugS71GscR-_uuiQQ6wUorBb0zGaH4",
    #     model="MiniMax-M3"
    # )
    info = LLMServerInfo(
        base_url="https://uni-api.cstcloud.cn",
        api_key="7868485c0ca1d66880fdb72e06b77ebfc6daf07faf61638e81e7a79adf7e309d",
        model="minimax-m27"
    )
    payload = {
        "model": info.model,
        "messages": [{"role": "user", "content": "Reply with one word: ok"}],
        "temperature": 0,
        "max_tokens": 16,
    }
    response = requests.post(
        f"{info.base_url.rstrip('/')}/v1/chat/completions",
        headers={"Authorization": f"Bearer {info.api_key}"},
        json=payload,
        verify=False,
        timeout=60,
    )
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
