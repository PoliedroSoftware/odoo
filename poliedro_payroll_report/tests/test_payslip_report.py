import secrets
from datetime import datetime
from io import BytesIO
from unittest.mock import patch

from lxml import html as html_parser

from odoo import Command, http
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tests.common import new_test_user
from odoo.tools.pdf import PdfFileReader


@tagged("post_install", "-at_install")
class TestPoliedroPayslipReport(TransactionCase):
    """Fictitious in-memory fixtures. No salary calculation or saved payroll."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.employee = self.env['hr.employee'].new({
            'name': 'PERSONA FICTICIA PARA PRUEBAS DE PRESENTACIÓN',
            'company_id': self.company.id, 'lang': 'es_CO',
        })
        self.version = self.env['hr.version'].new({
            'employee_id': self.employee, 'company_id': self.company.id,
            'identification_id': 'DEMO-0001', 'currency_id': self.company.currency_id.id,
        })

    def _slip(self, specs, state='draft', currency=None):
        lines = []
        for index, (name, category, amount) in enumerate(specs):
            cat = self.env['hr.salary.rule.category'].new({'name': category, 'code': category})
            rule = self.env['hr.salary.rule'].new({
                'name': name, 'code': 'NET' if category == 'NET' else 'TEST_%s' % index, 'category_id': cat,
                'sequence': index, 'appears_on_payslip': True,
                'appears_on_employee_cost_dashboard': category == 'COMP',
            })
            lines.append(Command.create({
                'name': name, 'salary_rule_id': rule,
                'employee_id': self.employee, 'version_id': self.version,
                'amount': amount, 'quantity': 1, 'rate': 100, 'total': amount,
            }))
        return self.env['hr.payslip'].new({
            'name': 'Recibo ficticio de presentación', 'company_id': self.company.id,
            'employee_id': self.employee, 'version_id': self.version,
            'date_from': '2026-10-01', 'date_to': '2026-10-31',
            'state': state, 'line_ids': lines,
            'currency_id': (currency or self.company.currency_id).id,
            'net_wage': sum(amount for _, cat, amount in specs if cat not in ('COMP', 'GROSS', 'NET')),
        })

    def _html(self, slip):
        return self.env['ir.actions.report'].with_context(lang='es_CO', tz='America/Bogota')._render_template(
            'hr_payroll.report_payslip_lang', {'docs': slip, 'doc_ids': [], 'doc_model': 'hr.payslip'}
        ).decode()

    def test_groups_exclude_subtotals_and_employer_costs(self):
        slip = self._slip([
            ('Salario básico', 'BASIC', 2000000), ('Auxilio transporte', 'ALW', 200000),
            ('Bonificación', 'ALW', 75000), ('Horas extra', 'ALW', 50000),
            ('Salario bruto', 'GROSS', 2325000), ('Salud empleado', 'DED', -80000),
            ('Pensión empleado', 'DED', -80000), ('Provisión cesantías', 'COMP', 100000),
            ('Salario neto', 'NET', 2165000),
        ])
        data = slip._get_poliedro_payroll_report_data()
        self.assertEqual(len(data['earnings']), 4)
        self.assertEqual(len(data['deductions']), 2)
        self.assertEqual(data['earnings_total'], 2325000)
        self.assertEqual(data['deductions_total'], 160000)
        self.assertEqual(data['net_total'], 2165000)

    def test_refund_reduces_deductions(self):
        slip = self._slip([('Salario', 'BASIC', 1000), ('Préstamo', 'DED', -100),
                           ('Devolución de préstamo', 'DED', 40), ('Ajuste negativo', 'DED', -10)])
        data = slip._get_poliedro_payroll_report_data()
        self.assertEqual(data['deductions_total'], 70)
        self.assertEqual(data['earnings_total'] - data['deductions_total'], data['net_total'])
        self.assertEqual([-line.total for line in data['deductions']], [100, -40, 10])

    def test_no_transport_bonus_vacation_and_sickness(self):
        slip = self._slip([('Salario', 'BASIC', 1000), ('Bonificación', 'ALW', 50),
                           ('Vacaciones', 'ALW', 30), ('Incapacidad', 'ALW', 20)])
        data = slip._get_poliedro_payroll_report_data()
        self.assertEqual(data['earnings_total'], 1100)
        self.assertFalse(data['deductions'])
        html = self._html(slip)
        self.assertIn('Sin deducciones', html)
        self.assertIn('Sin días o novedades registrados', html)

    def test_long_details_keep_every_line(self):
        slip = self._slip([('Concepto ficticio %02d con descripción extensa' % i, 'ALW', i + 1)
                           for i in range(45)] + [('Préstamo', 'DED', -10)])
        data = slip._get_poliedro_payroll_report_data()
        self.assertEqual(len(data['detail_rows']), 45)
        self.assertFalse(data['detail_rows'][-1]['deduction'])
        self.assertIn('Concepto ficticio 44', self._html(slip))

    def test_exceptional_description_continues_without_repeating_amounts(self):
        name = ('Texto de prueba para continuidad. ' * 200).strip()
        data = self._slip([(name, 'ALW', 100)])._get_poliedro_payroll_report_data()
        self.assertEqual(' '.join(row['earning_name'] for row in data['detail_rows']), name)
        self.assertTrue(all(len(row['earning_name']) <= 350 for row in data['detail_rows']))
        self.assertEqual(sum(bool(row['earning']) for row in data['detail_rows']), 1)

    def test_state_warning_is_native(self):
        for state in ('draft', 'cancel', 'validated', 'paid'):
            slip = self._slip([], state=state)
            self.assertEqual(bool(slip._is_invalid()), state in ('draft', 'cancel'))
            self.assertEqual('class="ppr-warning"' in self._html(slip), state in ('draft', 'cancel'))

    def test_long_html_notes_continue_once_without_repeating_amounts(self):
        slip = self._slip([('Salario ficticio', 'BASIC', 1000)])
        paragraphs = ['Nota ficticia %02d con contenido que debe conservarse.' % i for i in range(30)]
        slip.line_ids[0].salary_rule_id.note = ''.join('<p>%s</p>' % text for text in paragraphs)
        rows = slip._get_poliedro_payroll_report_data()['detail_rows']
        self.assertEqual(sum(bool(row['earning']) for row in rows), 1)
        joined = ' '.join(row['earning_note_text'] for row in rows if row['earning_note_text'])
        self.assertEqual(joined, ' '.join(paragraphs))
        self.assertTrue(all(len(row['earning_note_text']) <= 250 for row in rows))
        rendered = html_parser.fromstring(self._html(slip)).text_content()
        self.assertEqual(rendered.count(paragraphs[0]), 1)
        self.assertEqual(rendered.count(paragraphs[-1]), 1)

    def test_worked_days_and_overtime_quantity(self):
        slip = self._slip([('Salario ficticio', 'BASIC', 1000), ('Horas extras ficticias', 'ALW', 80)])
        slip.line_ids[1].update({'amount': 20, 'quantity': 4, 'total': 80})
        days = []
        for name, code, count, hours in [('Asistencia ficticia', 'WORK', 22, 176),
                                         ('Vacaciones ficticias', 'VAC', 3, 24),
                                         ('Incapacidad ficticia', 'SICK', 2, 16),
                                         ('Excluido de presentación', 'OUT', 1, 8)]:
            kind = self.env['hr.work.entry.type'].new({'name': name, 'code': code})
            days.append(Command.create({'work_entry_type_id': kind,
                                         'number_of_days': count, 'number_of_hours': hours}))
        slip.worked_days_line_ids = days
        html = self._html(slip)
        for text in ('Asistencia ficticia', 'Vacaciones ficticias', 'Incapacidad ficticia', '176.0', '24.0', '16.0'):
            self.assertIn(text, html)
        self.assertNotIn('Excluido de presentación', html)
        self.assertEqual(slip.line_ids[1].quantity, 4)
        self.assertEqual(slip._get_poliedro_payroll_report_data()['earnings_total'], 1080)

    def test_currency_color_timezone_and_company_isolation(self):
        company = self.env['res.company'].new({
            'name': 'EMPRESA FICTICIA SIN MARCA', 'currency_id': self.env.ref('base.USD').id,
            'poliedro_payroll_report_color': 'red; color: transparent', 'logo': False,
        })
        self.assertEqual(company._get_poliedro_payroll_report_color(), '#155E63')
        slip = self._slip([('Salario ficticio', 'BASIC', 123.45)], currency=self.env.ref('base.USD'))
        slip.company_id = company
        html = self._html(slip)
        self.assertIn('EMPRESA FICTICIA SIN MARCA', html)
        self.assertNotIn('Cabecera corporativa', html)
        self.assertEqual(slip.currency_id, self.env.ref('base.USD'))
        self.assertTrue(slip.with_context(tz='America/Bogota')._get_poliedro_payroll_report_data()['printed_at'].endswith('-05'))

    def test_existing_action_and_xml_ids(self):
        report = self.env.ref('hr_payroll.action_report_payslip')
        self.assertEqual(report.model, 'hr.payslip')
        self.assertEqual(report.report_name, 'hr_payroll.report_payslip_lang')
        self.assertEqual(report.paperformat_id.format, 'A4')
        self.assertEqual(report.paperformat_id.orientation, 'Landscape')
        self.assertEqual(report.paperformat_id.margin_top, 7.8)
        self.assertEqual(report.paperformat_id.margin_left, 8.5)
        self.assertTrue(report.paperformat_id.disable_shrinking)
        self.assertFalse(report.attachment_use)
        self.assertEqual(report.paperformat_id, self.env.ref('poliedro_payroll_report.paperformat_poliedro_payslip_landscape'))
        self.assertFalse(self.env['ir.model.data'].search_count([
            ('module', '=', 'poliedro_payroll_report'), ('model', '=', 'ir.actions.report')]))

    def test_internal_user_has_no_payroll_access(self):
        user = new_test_user(self.env, login='payroll_layout_test', groups='base.group_user',
                             password=secrets.token_urlsafe(24), context={'no_reset_password': True})
        with self.assertRaises(AccessError):
            self.env['hr.payslip'].with_user(user).search([])

    def test_render_uses_same_effective_dpi_on_linux_and_windows(self):
        report = self.env.ref('hr_payroll.action_report_payslip')
        rendered = self._html(self._slip([('Salario ficticio', 'BASIC', 1000)]))
        args = report._prepare_html(rendered)[4]
        self.assertEqual(args['data-report-dpi'], '96')
        self.assertEqual(report.paperformat_id.dpi, 90)

    def test_integrated_header_and_optional_background(self):
        self.company = self.env['res.company'].new({
            'name': 'EMPRESA FICTICIA CON FONDO',
            'currency_id': self.env.company.currency_id.id,
            'logo': self.env.company.logo,
            'poliedro_payroll_header_background': self.env.company.logo,
            'poliedro_payroll_banner': self.env.company.logo,
        })
        slip = self._slip([('Salario ficticio', 'BASIC', 1000)])
        tree = html_parser.fromstring(self._html(slip))
        hero = tree.xpath('//*[contains(concat(" ", @class, " "), " ppr-hero ")]')
        self.assertEqual(len(hero), 1)
        self.assertIn(self.company.name, hero[0].text_content())
        self.assertIn(self.employee.name, hero[0].text_content())
        self.assertIn('background-image:', hero[0].get('style'))
        self.assertFalse(tree.xpath('//*[@class="ppr-title" or @class="ppr-parties" or @class="ppr-banner"]'))
        self.company.poliedro_payroll_header_background = False
        self.company.logo = False
        tree = html_parser.fromstring(self._html(slip))
        hero = tree.xpath('//section[@class="ppr-hero"]')[0]
        self.assertNotIn('background-image:', hero.get('style'))
        self.assertFalse(hero.xpath('.//img'))
        self.assertIn(self.company.name, hero.text_content())

    def test_printed_dates_share_the_same_localized_instant(self):
        slip = self._slip([]).with_context(tz='America/Bogota')
        with patch('odoo.addons.poliedro_payroll_report.models.hr_payslip.fields.Datetime.now', return_value=datetime(2026, 10, 25, 2, 30)):
            data = slip._get_poliedro_payroll_report_data()
        self.assertEqual(data['printed_at'], '24/10/2026 21:30 -05')
        self.assertEqual(data['printed_at_display'], '24/10/2026 21:30')

    def test_render_is_read_only_and_keeps_signed_amounts(self):
        signed = self._slip([('Salario ficticio', 'BASIC', 1000), ('Descuento', 'DED', -100), ('Devolución', 'DED', 40)])
        signed_text = html_parser.fromstring(self._html(signed)).text_content()
        self.assertIn('-40', signed_text.replace('\ufeff', ''))
        self.assertEqual(signed._get_poliedro_payroll_report_data()['deductions_total'], 60)
        # Stored QA records exercise native computed fields without the NewId cache
        # invalidation caused by patching an ORM model class. No write is performed.
        slip = self.env['hr.payslip'].search([('line_ids', '!=', False)], limit=1)
        if not slip:
            slip = self._slip([('Salario ficticio', 'BASIC', 1000)], state='paid')
        before = (slip.state, slip.net_wage, slip.line_ids.mapped('total'), slip.compute_date)
        with patch.object(type(slip), 'compute_sheet', side_effect=AssertionError('Printing must not calculate payroll')):
            text = html_parser.fromstring(self._html(slip)).text_content()
        self.assertEqual(before, (slip.state, slip.net_wage, slip.line_ids.mapped('total'), slip.compute_date))


@tagged('post_install', '-at_install')
class TestPoliedroPayslipPrintRoute(HttpCase):
    def test_native_print_route(self):
        slip = self.env['hr.payslip'].search([('line_ids', '!=', False)], limit=1)
        if not slip:
            self.skipTest('The native HTTP integration check needs a computed QA payslip.')
        password = secrets.token_urlsafe(24)
        user = new_test_user(
            self.env, login='payroll_pdf_http_test', password=password,
            context={'no_reset_password': True},
            groups='hr_payroll.group_hr_payroll_user',
            company_id=slip.company_id.id,
            company_ids=[Command.set(slip.company_id.ids)],
            lang='es_CO', tz='America/Bogota',
        )
        session = self.authenticate(user.login, password)
        # Odoo normally returns HTML instead of PDF in test mode. Exercise the real engine.
        session.context['force_report_rendering'] = True
        http.root.session_store.save(session)
        # Include the older receipt as well: it may have a bonus plus the draft warning.
        slips = self.env['hr.payslip'].search([
            ('company_id', '=', slip.company_id.id), ('line_ids', '!=', False),
        ], order='id', limit=2)
        for receipt in slips:
            response = self.url_open('/print/payslips?list_ids=%s' % receipt.id)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(b'%PDF'))
            reader = PdfFileReader(BytesIO(response.content))
            self.assertEqual(reader.getNumPages(), 1)
            self.assertAlmostEqual(float(reader.pages[0].mediabox.width), 842, delta=2)
            self.assertAlmostEqual(float(reader.pages[0].mediabox.height), 595, delta=2)
            text = ' '.join(page.extract_text() or '' for page in reader.pages)
            self.assertIn('NETO A PAGAR', text)
            self.assertIn(receipt.employee_id.name, text)
            if receipt.company_id.poliedro_payroll_footer_phrase:
                self.assertIn(receipt.company_id.poliedro_payroll_footer_phrase, text)
