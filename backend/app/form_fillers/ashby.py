import logging
from datetime import datetime

from app.config import settings
from app.form_fillers.base import ApplicationData, ApplyResult, BaseFormFiller

logger = logging.getLogger(__name__)


class AshbyFormFiller(BaseFormFiller):
    """Fills jobs.ashbyhq.com application forms.

    Ashby uses labeled inputs without stable IDs; we target by associated label text.
    """
    ats_name = "ashby"

    async def fill(self, apply_url: str, data: ApplicationData) -> ApplyResult:
        page = await self.browser.new_page()
        try:
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)

            # Ashby uses placeholder-targeted fields
            await page.fill('input[placeholder*="name" i], input[name="name"]', data.name)
            await page.fill('input[type="email"], input[placeholder*="email" i]', data.email)
            await page.fill('input[type="tel"], input[placeholder*="phone" i]', data.phone)

            try:
                await page.fill('input[placeholder*="linkedin" i]', data.linkedin_url)
            except Exception:
                pass

            await page.locator('input[type="file"]').set_input_files(data.resume_pdf_path)

            try:
                await page.fill('textarea[placeholder*="cover" i], textarea[name*="cover" i]', data.cover_letter_text)
            except Exception:
                pass

            await page.click('button[type="submit"]')

            await page.wait_for_selector(
                "text=/thank you|submitted|received|application sent/i",
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
            logger.exception("Ashby fill failed: %s", e)
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
