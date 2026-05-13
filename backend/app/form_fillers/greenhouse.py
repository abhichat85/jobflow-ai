import logging
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.form_fillers.base import ApplicationData, ApplyResult, BaseFormFiller

logger = logging.getLogger(__name__)


class GreenhouseFormFiller(BaseFormFiller):
    """Fills and submits applications on boards.greenhouse.io.

    Greenhouse uses consistent field IDs across customers:
      #first_name, #last_name, #email, #phone, #resume (file input),
      #cover_letter_text (textarea), question_*** for custom questions.
    """
    ats_name = "greenhouse"

    async def fill(self, apply_url: str, data: ApplicationData) -> ApplyResult:
        page = await self.browser.new_page()
        try:
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)

            # Split name
            first, _, last = data.name.partition(" ")
            await page.fill("#first_name", first)
            await page.fill("#last_name", last or first)
            await page.fill("#email", data.email)
            await page.fill("#phone", data.phone)

            # Resume upload
            resume_input = page.locator('input[type="file"][name*="resume"], #resume')
            await resume_input.set_input_files(data.resume_pdf_path)

            # Cover letter — Greenhouse uses either a textarea or a file input
            try:
                await page.fill("#cover_letter_text", data.cover_letter_text)
            except Exception:
                # Some Greenhouse forms expect a file
                pass

            # LinkedIn URL (best-effort)
            try:
                await page.fill('input[name*="linkedin" i], input[id*="linkedin" i]', data.linkedin_url)
            except Exception:
                pass

            # Submit
            await page.click('button[type="submit"], input[type="submit"]')

            # Wait for confirmation page
            await page.wait_for_selector(
                "text=/thanks|received|submitted|thank you/i",
                timeout=30000,
            )
            confirmation = await page.inner_text("body")

            # Screenshot the confirmation
            screenshot_path = self._screenshot_path(apply_url)
            await page.screenshot(path=screenshot_path, full_page=True)

            return ApplyResult(
                success=True,
                confirmation_text=confirmation[:500],
                screenshot_path=screenshot_path,
            )
        except Exception as e:
            logger.exception("Greenhouse fill failed: %s", e)
            try:
                screenshot_path = self._screenshot_path(apply_url, suffix="_error")
                await page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                screenshot_path = None
            return ApplyResult(
                success=False,
                error_message=str(e),
                screenshot_path=screenshot_path,
            )
        finally:
            await page.close()

    @staticmethod
    def _screenshot_path(apply_url: str, suffix: str = "") -> str:
        assets_dir = settings.data_dir / "assets" / "apply"
        assets_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        slug = apply_url.replace("/", "_").replace(":", "")[-60:]
        return str(assets_dir / f"{stamp}{suffix}_{slug}.png")
