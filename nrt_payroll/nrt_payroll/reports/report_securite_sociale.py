# -*- coding:utf-8 -*-
# by khk

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SecuriteSociale(models.AbstractModel):
    _name = 'report.nrt_payroll.report_css_view'
    _description = 'Rapport securite sociale'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        register_ids = self.env.context.get('active_ids', [])
        contrib_registers = self.env['hr.contribution.register'].browse(register_ids)

        date_from = datetime.strptime(data['form'].get('date_from', fields.Date.today()), '%Y-%m-%d')
        date_to = datetime.strptime(
            data['form'].get('date_to', str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10]),
            '%Y-%m-%d')

        dico = {}
        lines_data_male = []
        lines_data_female = []
        self.total_brut_male = 0.0
        self.total_base_male = 0.0
        self.total_prestfam_male = 0.0
        self.total_acw_male = 0.0
        self.total_cotisation_male = 0.0
        self.total_brut_female = 0.0
        self.total_base_female = 0.0
        self.total_prestfam_female = 0.0
        self.total_acw_female = 0.0
        self.total_cotisation_female = 0.0

        self.env.cr.execute("SELECT DISTINCT hr_payslip_line.id,\
                            hr_employee.num_chezemployeur,\
                            hr_employee.name from\
                            hr_payslip_line as hr_payslip_line,\
                            hr_employee as hr_employee,\
                            hr_payslip as hr_payslip where\
                            hr_employee.id = hr_payslip_line.employee_id AND\
                            hr_employee.id = hr_payslip.employee_id AND\
                            hr_payslip_line.payslip_date_from >=  %s AND\
                            hr_payslip_line.payslip_date_to <= %s AND \
                            hr_employee.company_id = %s AND \
                            hr_payslip_line.code IN ('C1200','C1000','C2010','C2020')\
                            ORDER BY hr_employee.num_chezemployeur  ASC, hr_employee.name ASC",
                            (date_from, date_to, self.env.user.company_id.id))
        line_ids = [x[0] for x in self.env.cr.fetchall()]

        self.nb_male_brut = 0
        self.nb_female_brut = 0
        self.nb_male_prestfam = 0
        self.nb_female_prestfam = 0
        self.nb_male_awc = 0
        self.nb_female_awc = 0

        for line in self.env['hr.payslip.line'].browse(line_ids):
            if line.code == 'C1200':  # brut
                if line.employee_id.gender == "male":
                    if line.employee_id.id not in dico:
                        dico[line.employee_id.id] = {}
                        self.nb_male_brut += 1
                self.total_brut_male += line.total
                if line.employee_id.gender == "female":
                    if line.employee_id.id not in dico:
                        dico[line.employee_id.id] = {}
                        self.nb_female_brut += 1
                    self.total_brut_female += line.total
            elif line.code == 'C2010':  # prestfam
                if line.employee_id.gender == "male":
                    self.total_base_male += line.amount
                    self.total_prestfam_male += line.total
                    self.total_cotisation_male += line.total
                    self.nb_male_prestfam += 1
                if line.employee_id.gender == "female":
                    self.total_base_female += line.amount
                    self.total_prestfam_female += line.total
                    self.total_cotisation_female += line.total
                    self.nb_female_prestfam += 1
            elif line.code == 'C2020':  # acw
                if line.employee_id.gender == "male":
                    self.total_acw_male += line.total
                    self.total_cotisation_male += line.total
                    self.nb_male_awc += 1
                if line.employee_id.gender == "female":
                    self.total_acw_female += line.total
                    self.total_cotisation_female += line.total
                    self.nb_female_awc += 1
        else:
            pass

        lines_data_male = [{
            'brut': int(self.total_brut_male),
            'base': int(self.total_base_male),
            'prestfam': int(self.total_prestfam_male),
            'acw': int(self.total_acw_male),
            'cotisation': int(self.total_cotisation_male),
        }]

        lines_data_female = [{
            'brut': int(self.total_brut_female),
            'base': int(self.total_base_female),
            'prestfam': int(self.total_prestfam_female),
            'acw': int(self.total_acw_female),
            'cotisation': int(self.total_cotisation_male),
        }]

        lines_total = [{
            'total_brut': int(round(self.total_brut_male + self.total_brut_female)),
            'total_base': int(round(self.total_base_male + self.total_base_female)),
            'total_prestfam': int(round(self.total_prestfam_male + self.total_prestfam_female)),
            'total_acw': int(round(self.total_acw_male + self.total_acw_female)),
            'total_cotisation': int(round(self.total_cotisation_male + self.total_cotisation_female)),
        }]

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_data_male': lines_data_male,
            'lines_data_female': lines_data_female,
            'lines_total': lines_total,
            'nb_male_brut': self.nb_male_brut,
            'nb_female_brut': self.nb_female_brut,
            'nb_male_prestfam': self.nb_male_prestfam,
            'nb_female_prestfam': self.nb_female_prestfam,
            'nb_male_awc': self.nb_male_awc,
            'nb_female_awc': self.nb_female_awc,
            'nb_total_brut': self.nb_male_brut + self.nb_female_brut,
            'nb_total_prestfam': self.nb_male_prestfam + self.nb_female_prestfam,
            'nb_total_awc': self.nb_male_awc + self.nb_female_awc,
            'date_from': datetime.strftime(date_from, '%d/%m/%Y'),
            'date_to': datetime.strftime(date_to, '%d/%m/%Y')
        }