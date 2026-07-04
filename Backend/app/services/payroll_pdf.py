"""
HRMS Payroll PDF Service
WeasyPrint-based pay stub generation with Jinja2 templates.
"""

from __future__ import annotations

import calendar
import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.config import get_settings
from app.models.employee import Employee
from app.models.payroll import PayrollRun

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


async def generate_pay_stub(employee: Employee, payroll_run: PayrollRun) -> str:
    """
    Generate PDF pay stub using WeasyPrint.
    Returns the storage path of the generated PDF.
    """
    settings = get_settings()
    from weasyprint import HTML

    month_name = calendar.month_name[payroll_run.month]
    ref_id = f"PAY-{payroll_run.year}-{payroll_run.month:02d}-{employee.employee_id[-4:]}"

    template = jinja_env.get_template("pay_stub.html")
    html_content = template.render(
        employee_name=employee.name,
        employee_id=employee.employee_id,
        department=employee.department or "N/A",
        designation=employee.designation or "N/A",
        month_name=month_name,
        year=payroll_run.year,
        components=payroll_run.components_snapshot,
        gross_pay=payroll_run.gross_pay,
        deductions=payroll_run.deductions,
        net_pay=payroll_run.net_pay,
        ref_id=ref_id,
        generated_date=date.today().strftime("%b %d, %Y"),
        company_name=settings.COMPANY_NAME,
    )

    # Generate PDF bytes
    pdf_bytes = HTML(string=html_content).write_pdf()

    # Save to storage
    storage_dir = settings.STORAGE_PATH / "paystubs" / str(employee.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{payroll_run.year}-{payroll_run.month:02d}.pdf"
    filepath = storage_dir / filename
    filepath.write_bytes(pdf_bytes)

    logger.info("Generated pay stub: %s", filepath)
    return str(filepath)
