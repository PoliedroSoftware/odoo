import re
import unicodedata

from odoo import fields, models
from odoo.tools import html2plaintext


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @staticmethod
    def _poliedro_payroll_text_parts(value, limit=350):
        """Bound presentation row height for wkhtmltopdf's repeated table headers."""
        parts = []
        value = value or ""
        while len(value) > limit:
            end = value.rfind(" ", 0, limit) or limit
            if end < 0:
                end = limit
            parts.append(value[:end])
            value = value[end:].lstrip()
        return parts + [value]

    @staticmethod
    def _poliedro_normalize_payroll_label(value):
        value = unicodedata.normalize("NFKD", value or "")
        value = "".join(char for char in value if not unicodedata.combining(char))
        return re.sub(r"\s+", " ", value.casefold()).strip()

    def _poliedro_payroll_note_parts(self, line):
        """Keep short HTML notes; paginate long notes as escaped readable text."""
        if not line or not line.salary_rule_id.note:
            return []
        text = html2plaintext(line.salary_rule_id.note)
        if len(text) <= 250 and len(text.splitlines()) <= 5:
            return []
        return self._poliedro_payroll_text_parts(re.sub(r"\s+", " ", text).strip(), limit=250)

    def _get_poliedro_payroll_report_data(self):
        """Prepare display-only groups from the already computed payslip lines."""
        self.ensure_one()
        earnings = self.env["hr.payslip.line"]
        deductions = self.env["hr.payslip.line"]

        subtotal_codes = {"GROSS", "NET"}
        subtotal_terms = (
            "taxable salary", "gross salary", "gross wage", "salario bruto",
            "sueldo bruto", "sueldo imponible", "total devengado",
            "net salary", "net wage", "salario neto", "sueldo neto",
            "total neto", "net amount",
        )
        employer_terms = (
            "company contribution", "employer contribution", "employer cost",
            "contribucion de la empresa", "aporte patronal", "costo empleador",
            "provision", "provision laboral", "provisiones",
        )
        deduction_terms = (
            "deduction", "deduccion", "descuento", "withholding", "retencion",
        )

        for line in self.line_ids.filtered(lambda item: item.appears_on_payslip).sorted(
            key=lambda item: (item.sequence, item.id)
        ):
            category = line.category_id
            category_labels = []
            category_codes = set()
            while category:
                category_labels.extend((category.name or "", category.code or ""))
                category_codes.add((category.code or "").upper())
                category = category.parent_id
            rule = line.salary_rule_id
            labels = [self._poliedro_normalize_payroll_label(value) for value in (
                *category_labels, rule.name, rule.code,
            )]
            searchable = " ".join(labels)
            code = (line.code or "").upper()

            # Exclude native and custom subtotal rules, employee net rules,
            # employer contributions and provisions from employee earnings.
            if code in subtotal_codes or any(term in searchable for term in subtotal_terms):
                continue
            if category_codes.intersection({"COMP", "COMPANY"}) or rule.appears_on_employee_cost_dashboard or any(
                term in searchable for term in employer_terms
            ):
                continue

            is_deduction = (
                "DED" in category_codes
                or any(term in searchable for term in deduction_terms)
                or line.total < 0
            )
            if is_deduction:
                deductions |= line
            else:
                earnings |= line

        detail_rows = []
        for index in range(max(len(earnings), len(deductions))):
            earning, deduction = earnings[index:index + 1], deductions[index:index + 1]
            earning_parts = self._poliedro_payroll_text_parts(earning.name if earning else "")
            deduction_parts = self._poliedro_payroll_text_parts(deduction.name if deduction else "")
            earning_notes = self._poliedro_payroll_note_parts(earning)
            deduction_notes = self._poliedro_payroll_note_parts(deduction)
            for part in range(max(len(earning_parts), len(deduction_parts))):
                detail_rows.append({
                    "earning": earning if part == 0 else earnings[:0],
                    "deduction": deduction if part == 0 else deductions[:0],
                    "earning_name": earning_parts[part] if part < len(earning_parts) else "",
                    "deduction_name": deduction_parts[part] if part < len(deduction_parts) else "",
                    "earning_short_note": part == 0 and not earning_notes,
                    "deduction_short_note": part == 0 and not deduction_notes,
                    "earning_note_text": "", "deduction_note_text": "",
                })
            for part in range(max(len(earning_notes), len(deduction_notes))):
                detail_rows.append({
                    "earning": earnings[:0], "deduction": deductions[:0],
                    "earning_name": "", "deduction_name": "",
                    "earning_short_note": False, "deduction_short_note": False,
                    "earning_note_text": earning_notes[part] if part < len(earning_notes) else "",
                    "deduction_note_text": deduction_notes[part] if part < len(deduction_notes) else "",
                })
        currency = self.currency_id
        printed_at = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return {
            "printed_at": printed_at.strftime("%d/%m/%Y %H:%M %Z"),
            "printed_at_display": printed_at.strftime("%d/%m/%Y %H:%M"),
            "earnings": earnings,
            "deductions": deductions,
            "earnings_total": currency.round(sum(earnings.mapped("total"))),
            # A positive deduction line is a refund, and must reduce deductions.
            "deductions_total": currency.round(-sum(deductions.mapped("total"))),
            "detail_rows": detail_rows,
            # This is Odoo's stored/computed net result; the report never recalculates it.
            "net_total": self.net_wage,
        }
