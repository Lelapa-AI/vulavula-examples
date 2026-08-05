import sys

from checks import run_accuracy_checks, run_live_streaming_checks, run_performance_checks, run_sanity_checks
from client import VulavulaClient
from report import Report
from settings import get_settings


def main() -> int:
    settings = get_settings()
    client = VulavulaClient(
        base_url=settings.BASE_URL,
        username=settings.BASIC_AUTH_USERNAME,
        password=settings.BASIC_AUTH_PASSWORD,
    )

    print(f"Qualifying Vulavula deployment at {settings.BASE_URL}\n")

    report = Report()

    for result in run_sanity_checks(client, settings):
        report.add(result)

    # If the deployment isn't even reachable/authenticated, accuracy and
    # performance numbers are meaningless - stop early.
    if not report.passed:
        report.print()
        return 1

    for result in run_accuracy_checks(client, settings):
        report.add(result)

    for result in run_performance_checks(client, settings):
        report.add(result)

    for result in run_live_streaming_checks(client, settings):
        report.add(result)

    report.print()
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
