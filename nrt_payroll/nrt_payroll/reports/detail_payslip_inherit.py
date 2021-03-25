from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class PayslipInherit(models.AbstractModel):
    _inherit = "report.hr_payroll.report_payslipdetails"

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip'].browse(docids)
        for payslip in payslips:
            return {
                'doc_ids': docids,
                'doc_model': 'hr.payslip',
                'docs': payslip,
                'data': data,
                'get_details_by_rule_category': self.get_details_by_rule_category(payslip.mapped(
                    'details_by_salary_rule_category').filtered(lambda r: r.appears_on_payslip)),
                'get_lines_by_contribution_register': self.get_lines_by_contribution_register(
                    payslip.mapped('line_ids').filtered(lambda r: r.appears_on_payslip)),
            }
