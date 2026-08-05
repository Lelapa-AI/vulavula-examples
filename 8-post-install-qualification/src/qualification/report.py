from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    category: str
    name: str
    status: Status
    detail: str = ""


@dataclass
class Report:
    results: List[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    @property
    def passed(self) -> bool:
        return all(r.status != Status.FAIL for r in self.results)

    def print(self) -> None:
        width = max((len(r.name) for r in self.results), default=0)

        # Group by category in order-of-first-appearance, regardless of how
        # interleaved the underlying check functions added results in - e.g.
        # the live-streaming checks append an Accuracy result after several
        # Performance ones since they're derived from a single shared run.
        by_category = defaultdict(list)
        for result in self.results:
            by_category[result.category].append(result)

        for category, results in by_category.items():
            print(f"\n{category}")
            print("-" * len(category))
            for result in results:
                print(f"  [{result.status.value:<4}] {result.name:<{width}}  {result.detail}")

        print()
        passed = sum(1 for r in self.results if r.status == Status.PASS)
        failed = sum(1 for r in self.results if r.status == Status.FAIL)
        skipped = sum(1 for r in self.results if r.status == Status.SKIP)
        print(f"Summary: {passed} passed, {failed} failed, {skipped} skipped")
        print("Overall: " + ("QUALIFIED" if self.passed else "NOT QUALIFIED"))
