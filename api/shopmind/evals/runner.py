"""Run the checked-in questions against a fake-mode agent."""

from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path

from shopmind.agent.runner import ShopMindAgent
from shopmind.schemas import ChatRequest, ChatResponse, EvalCaseResult, EvalReport

CASES_PATH = Path(__file__).with_name("cases.json")


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


class EvalRunner:
    def __init__(self, agent: ShopMindAgent) -> None:
        self.agent = agent
        self._lock = threading.Lock()

    def run(self) -> EvalReport:
        with self._lock:
            run_id = uuid.uuid4().hex[:8]
            results = [self._run_case(case, run_id) for case in load_cases()]
        passed = sum(1 for result in results if result.passed)
        return EvalReport(
            provider=self.agent.provider,
            total=len(results),
            passed=passed,
            failed=len(results) - passed,
            results=results,
        )

    def _run_case(self, case: dict, run_id: str) -> EvalCaseResult:
        response: ChatResponse | None = None
        session_id = f"eval-{run_id}-{case['id']}"
        for turn in case["turns"]:
            response = self.agent.chat(
                ChatRequest(
                    message=turn,
                    session_id=session_id,
                    locale=case.get("locale", "auto"),
                )
            )
        assert response is not None
        errors = _check(case, response)
        return EvalCaseResult(
            id=case["id"],
            passed=not errors,
            intent=response.intent,
            handoff=response.handoff,
            errors=errors,
            reply=response.reply,
        )


def _check(case: dict, response: ChatResponse) -> list[str]:
    errors: list[str] = []
    reply = response.reply
    folded = reply.casefold()
    if "intent" in case and response.intent != case["intent"]:
        errors.append(f"intent {response.intent} != {case['intent']}")
    if "handoff" in case and response.handoff != case["handoff"]:
        errors.append(f"handoff {response.handoff} != {case['handoff']}")
    if case.get("blocked") and not response.blocked:
        errors.append("expected the input guard to block the turn")
    if case.get("redacted_card") and not response.redacted_card:
        errors.append("expected the card number to be redacted")
    if case.get("cites") and not response.sources:
        errors.append("expected at least one cited source")
    if case.get("sku"):
        skus = [product.sku for product in response.products]
        if case["sku"] not in skus:
            errors.append(f"sku {case['sku']} not in {skus}")
    if case.get("price_cents") is not None:
        prices = [product.price_cents for product in response.products]
        if case["price_cents"] not in prices:
            errors.append(f"price {case['price_cents']} not in {prices}")
    for text in case.get("contains", []):
        if text.casefold() not in folded:
            errors.append(f"missing {text!r}")
    for text in case.get("excludes", []):
        if text.casefold() in folded:
            errors.append(f"forbidden {text!r}")
    return errors
