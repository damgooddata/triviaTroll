import argparse
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


URL = "https://kavafeud.netlify.app/feud-survey.html"
DEFAULT_ANSWERS = ("A used condom labeled “Fun Size.”", "Christian —already sucks me dry every month.", "Cum-filled Gushers", "You look just like my sister. That’s my favorite part.", "A butt plug where the gearshift should be")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--answers", nargs=5, metavar=("A1", "A2", "A3", "A4", "A5"),
        default=DEFAULT_ANSWERS, help="Five answers in survey order",
    )
    parser.add_argument(
        "--profile", type=Path, default=Path(__file__).resolve().parent / ".kava-feud-profile",
        help="Persistent browser profile directory (keep this between runs)",
    )
    args = parser.parse_args()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(args.profile), headless=True)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(URL, wait_until="domcontentloaded")
            fields = page.get_by_role("textbox", name="Your answer…")
            try:
                fields.first.wait_for(timeout=15000)
            except PlaywrightTimeoutError:
                if page.get_by_text("All done — thanks!", exact=True).is_visible():
                    print("This browser profile has already submitted a response.")
                    return 0
                print("The survey did not show any answer fields. Nothing was submitted.")
                return 1

            if fields.count() != len(args.answers):
                print(f"Expected {len(args.answers)} answer fields; found {fields.count()}. Nothing was submitted.")
                return 1

            # Fill positionally: field N gets answer N, regardless of the question wording.
            for index, answer in enumerate(args.answers):
                fields.nth(index).fill(answer)
                print(f"{index + 1}. → {answer}")

            page.get_by_role("button", name="Submit my answers").click()
            try:
                page.get_by_text("Submitted — thanks!", exact=True).wait_for(timeout=15000)
            except PlaywrightTimeoutError:
                print("Submission could not be confirmed. Inspect the browser before trying again.")
                return 1
            print("Submission confirmed by the site.")
            return 0
        finally:
            context.close()


if __name__ == "__main__":
    raise SystemExit(main())