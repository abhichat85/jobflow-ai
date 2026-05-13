import logging
from datetime import datetime

from app.config import settings
from app.form_fillers.base import ApplicationData, ApplyResult, BaseFormFiller

logger = logging.getLogger(__name__)


class LeverFormFiller(BaseFormFiller):
    """Fills jobs.lever.co application forms.

    Lever uses single full-name field (`name`), and stable form selectors
    `input[name="name"]`, `input[name="email"]`, etc.
    """
    ats_name = "lever"

    async def fill(self, apply_url: str, data: ApplicationData) -> ApplyResult:
        page = await self.browser.new_page()
        try:
            # Lever apply URLs end in /apply
            url = apply_url.rstrip("/")
            if not url.endswith("/apply"):
                url = f"{url}/apply"

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            await page.fill('input[name="name"]', data.name)
            await page.fill('input[name="email"]', data.email)
            await page.fill('input[name="phone"]', data.phone)

            try:
                await page.fill('input[name="urls[LinkedIn]"]', data.linkedin_url)
            except Exception:
                pass

            # Resume upload
            await page.locator('input[type="file"][name="resume"]').set_input_files(data.resume_pdf_path)

            # Cover letter
            try:
                await page.fill('textarea[name="comments"], textarea[name="cover_letter"]', data.cover_letter_text)
            except Exception:
                pass

            await page.click('button[type="submit"], button[data-qa="submit"]')

            await page.wait_for_selector(
                "text=/submitted|thank you|received|application sent/i",
                timeout=30000,
            )
            confirmation = await page.inner_text("body")
            screenshot_path = self._screenshot_path(apply_url)
            await page.screenshot(path=screenshot_path, full_page=True)
            return ApplyResult(
                success=True,
                confirmation_text=confirmation[:500],
                screenshot_path=screenshot_path,
            )
        except Exception as e:
            logger.exception("Lever fill failed: %s", e)
            try:
                screenshot_path = self._screenshot_path(apply_url, suffix="_error")
                await page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                screenshot_path = None
            return ApplyResult(success=False, error_message=str(e), screenshot_path=screenshot_path)
        finally:
            await page.close()

    @staticmethod
    def _screenshot_path(apply_url: str, suffix: str = "") -> str:
        assets_dir = settings.data_dir / "assets" / "apply"
        assets_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        slug = apply_url.replace("/", "_").replace(":", "")[-60:]
        return str(assets_dir / f"{stamp}{suffix}_{slug}.png")
