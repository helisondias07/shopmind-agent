"""Command line for a single turn, the eval suite, or a scripted demo."""

from __future__ import annotations

import argparse
import json
import sys

from shopmind.config import Settings
from shopmind.container import build_container
from shopmind.schemas import ChatRequest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shopmind", description="Talk to the Lume & Co. agent.")
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="Send one message")
    chat.add_argument("message")
    chat.add_argument("--session", default="cli")
    chat.add_argument("--locale", default="auto", choices=["auto", "pt", "en"])

    sub.add_parser("eval", help="Run the offline eval suite")
    demo = sub.add_parser("demo", help="Print scripted transcripts as JSON")
    demo.add_argument("--markdown", action="store_true")

    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.command == "eval":
        settings.llm_provider = "fake"
        settings.checkpoint_backend = "memory"
    container = build_container(settings)

    if args.command == "chat":
        response = container.agent.chat(
            ChatRequest(message=args.message, session_id=args.session, locale=args.locale)
        )
        json.dump(response.model_dump(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.command == "eval":
        report = container.evals.run()
        json.dump(report.model_dump(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0 if report.failed == 0 else 1

    transcript = _demo(container)
    if args.markdown:
        sys.stdout.write(_as_markdown(transcript))
    else:
        json.dump(transcript, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return 0


def _demo(container) -> list[dict]:
    scripts = [
        ("lamp", ["Quanto custa a luminária Lume?"]),
        ("order", ["Cadê o pedido LM-1042?", "Pode repetir o rastreio?"]),
        ("shipping", ["Quanto fica o frete do fone Nimbus para 01001-000?"]),
        ("handoff", ["Quero falar com uma pessoa"]),
    ]
    turns = []
    for name, messages in scripts:
        for index, message in enumerate(messages, start=1):
            response = container.agent.chat(
                ChatRequest(message=message, session_id=f"demo-{name}", locale="pt")
            )
            turns.append(
                {
                    "script": name,
                    "turn": index,
                    "message": message,
                    "reply": response.reply,
                    "intent": response.intent,
                    "confidence": response.confidence,
                    "handoff": response.handoff,
                    "nodes": [node.name for node in response.nodes],
                    "tools": [tool.tool for tool in response.tools],
                    "sources": [source.id for source in response.sources],
                }
            )
    return turns


def _as_markdown(turns: list[dict]) -> str:
    blocks = ["# ShopMind demo transcripts", ""]
    for turn in turns:
        blocks.append(f"## {turn['script']} · turn {turn['turn']}")
        blocks.append("")
        blocks.append(f"**Shopper:** {turn['message']}")
        blocks.append("")
        blocks.append(turn["reply"])
        blocks.append("")
        blocks.append(
            f"_intent `{turn['intent']}` · nodes {' → '.join(turn['nodes'])} · "
            f"tools {', '.join(turn['tools']) or '—'} · "
            f"sources {', '.join(turn['sources']) or '—'}_"
        )
        blocks.append("")
    return "\n".join(blocks)


if __name__ == "__main__":
    raise SystemExit(main())
