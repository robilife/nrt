# -*- coding: utf-8 -*-
# by khk
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HrPayslipEmployeeInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            for empl_contract in self.env['hr.contract'].search(
                    [('employee_id', '=', employee.id)], order='id desc', limit=1):  # add by khk
                if empl_contract.date_start <= from_date:  # add by khk
                    slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id,
                                                                            contract_id=False)
                    res = {
                        'employee_id': employee.id,
                        'name': slip_data['value'].get('name'),
                        'struct_id': slip_data['value'].get('struct_id'),
                        'contract_id': slip_data['value'].get('contract_id'),
                        'payslip_run_id': active_id,
                        'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                        'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                        'date_from': from_date,
                        'date_to': to_date,
                        'credit_note': run_data.get('credit_note'),
                        'company_id': employee.company_id.id,
                    }
                    if empl_contract.date_end:
                        if from_date <= empl_contract.date_end:
                            payslips += self.env['hr.payslip'].create(res)
                    else:
                        payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
