from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "data" / "templates"


def generate_resume_pdf(
    name: str,
    email: str,
    phone: str,
    summary: str,
    experiences: list[dict],
    skills: list[str],
    output_path: str,
    template_name: str = "resume_base.html",
) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)

    html_content = template.render(
        name=name,
        email=email,
        phone=phone,
        summary=summary,
        experiences=experiences,
        skills=skills,
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    HTML(string=html_content).write_pdf(str(output))

    html_path = output.with_suffix(".html")
    html_path.write_text(html_content)

    return str(output)
