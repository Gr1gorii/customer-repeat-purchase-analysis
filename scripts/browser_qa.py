"""Standalone local browser QA; the host Browser tool was unavailable for this task."""

import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def main():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/web/"
    errors = []
    checks = []
    try:
        with sync_playwright() as browser_runtime:
            browser = browser_runtime.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator("#content").wait_for(state="visible")
            assert page.title() == "customer-repeat-purchase-analysis"
            assert page.locator("h1").inner_text() == "customer-repeat-purchase-analysis"
            assert "PORTFOLIO PROJECT" not in page.locator("body").inner_text()
            assert page.locator("#net").inner_text() == "£9,748,131"
            assert page.locator("#customers").inner_text() == "4,338"
            assert "22.3%" in page.locator("#repeat").inner_text()
            assert page.locator("#monthly svg rect").count() == 13
            assert page.locator("td.unobserved").count() > 0
            assert page.locator("#monthly svg rect").first.get_attribute("fill") == "#276f61"
            assert page.locator("#monthly svg rect").last.get_attribute("fill") == "#b46036"
            assert "hsl(162 35% 30%)" in page.locator("#cohort-table td").first.get_attribute(
                "style"
            )
            checks.append("default real metrics, monthly chart and incomplete-month cells")
            checks.append("public name and original chart/heatmap colors")
            # Capture only application content; browser chrome and desktop cursors are excluded.
            start = page.locator("header").bounding_box()
            end = page.locator(".columns").bounding_box()
            page.screenshot(
                path=str(ROOT / "reports/dashboard-overview.png"),
                full_page=True,
                clip={
                    "x": start["x"] - 24,
                    "y": start["y"] - 24,
                    "width": start["width"] + 48,
                    "height": end["y"] + end["height"] - start["y"] + 48,
                },
            )
            page.locator(".cohort-panel").screenshot(path=str(ROOT / "reports/cohort-activity.png"))
            checks.append("README screenshots contain application content only")
            page.locator("#country").select_option("United Kingdom")
            page.locator("#cohort").select_option("2011-01")
            first = page.locator("#repeat").inner_text()
            page.locator("#cohort").select_option("2011-02")
            page.locator("#cohort").select_option("2011-01")
            assert page.locator("#repeat").inner_text() == first
            assert page.locator("#cohort-table tbody tr").count() == 1
            assert page.locator("#customers").inner_text() == "358"
            assert "19.8%" in first and "36.0%" in first and "49.2%" in first
            checks.append("country/cohort filtering and repeated selection are stable")
            page.locator("#country").select_option("Saudi Arabia")
            page.locator("#cohort").select_option("2010-12")
            assert page.locator("#empty").is_visible()
            assert page.locator("#customers").inner_text() == "0"
            assert "0 eligible customers" in page.locator("#repeat").inner_text()
            assert page.locator("#repeat .repeat-row strong").all_text_contents() == ["-", "-", "-"]
            assert page.locator("#cohort-table table").count() == 0
            checks.append("empty filter combination has explicit state and null rates")
            page.screenshot(path=str(ROOT / "reports/qa-empty.png"), full_page=True)
            for _ in range(3):
                page.locator("#reset").click()
                assert page.locator("#customers").inner_text() == "4,338"
                assert not page.locator("#empty").is_visible()
            checks.append("three repeated resets restore the baseline")
            page.locator("details summary").click()
            assert page.locator("#quality").is_visible()
            assert "135,080" in page.locator("#quality").inner_text()
            for link in [
                "../reports/management_summary.md",
                "../docs/metrics.md",
                "../reports/results.json",
            ]:
                assert page.request.get(url + link).status == 200
            checks.append("quality panel and supporting artifact links")
            page.locator("details summary").click()
            (ROOT / "reports/net_sales.svg").write_text(
                page.locator("#monthly svg").evaluate(
                    'node => {node.setAttribute("xmlns", "http://www.w3.org/2000/svg");'
                    " return node.outerHTML;}"
                )
            )
            page.screenshot(path=str(ROOT / "reports/qa-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert page.locator("#reset").is_visible()
            page.screenshot(path=str(ROOT / "reports/qa-mobile.png"), full_page=True)
            checks.append("390px mobile layout has no page-level horizontal overflow")
            page.route("**/data.json", lambda route: route.fulfill(status=404, body="missing"))
            page.reload()
            page.locator("#error").wait_for(state="visible")
            assert "Could not load reviewed data" in page.locator("#error").inner_text()
            checks.append("missing data presents a readable recovery instruction")
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    result = {
        "status": "passed",
        "browser": "Playwright Chromium 140 headless",
        "checks": checks,
        "javascript_errors": errors,
        "screenshots": [
            "dashboard-overview.png",
            "cohort-activity.png",
            "qa-desktop.png",
            "qa-mobile.png",
            "qa-empty.png",
        ],
        "host_browser_tool": "unavailable: node_repl js not exposed",
    }
    (ROOT / "reports/browser_qa.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
