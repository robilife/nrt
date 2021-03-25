# -*- coding:utf-8 -*-
# by khk
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class CotisationIpresReport(models.AbstractModel):
    _name = 'report.nrt_payroll.report_ipres_view'
    _description = 'Rapport cotisation ipres'

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

        self.total_brut_male = 0.0
        self.total_ipres_rc_male = 0.0
        self.total_ipres_rg_male = 0.0
        self.total_ipres_rc_pat_male = 0.0
        self.total_ipres_rg_pat_male = 0.0
        self.total_base_rc_male = 0.0
        self.total_base_rg_male = 0.0

        self.total_brut_female = 0.0
        self.total_ipres_rc_female = 0.0
        self.total_ipres_rg_female = 0.0
        self.total_ipres_rc_pat_female = 0.0
        self.total_ipres_rg_pat_female = 0.0
        self.total_base_rc_female = 0.0
        self.total_base_rg_female = 0.0

        dico = {}
        lines_data_male = []
        lines_data_female = []
        self.env.cr.execute("SELECT DISTINCT hr_payslip_line.id, " \
                            "hr_employee.num_chezemployeur," \
                            "hr_employee.name from " \
                            "hr_payslip_line as hr_payslip_line," \
                            "hr_employee as hr_employee," \
                            "hr_payslip as hr_payslip where " \
                            "hr_employee.id = hr_payslip_line.employee_id AND " \
                            "hr_employee.id = hr_payslip.employee_id AND " \
                            "hr_payslip_line.payslip_date_from >=  %s AND " \
                            "hr_payslip_line.payslip_date_to <= %s AND " \
                            "hr_employee.company_id = %s AND " \
                            "hr_payslip_line.code IN ('C1200','C1000','C2040','C2030','C2041','C2031') " \
                            "ORDER BY hr_employee.num_chezemployeur  ASC, hr_employee.name ASC",
                            (date_from, date_to, self.env.user.company_id.id))
        line_ids = [x[0] for x in self.env.cr.fetchall()]

        self.nb_total_brut = 0
        self.nb_total_ipres_rc = 0
        self.nb_total_ipres_rg = 0
        self.nb_male_brut = 0
        self.nb_male_ipres_rc = 0
        self.nb_male_ipres_rg = 0
        self.nb_female_brut = 0
        self.nb_female_ipres_rc = 0
        self.nb_female_ipres_rg = 0

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
                self.nb_total_brut += 1
            elif line.code == 'C2040':  # ipres rc
                if line.employee_id.gender == 'male':
                    self.total_ipres_rc_male += line.total
                    self.total_base_rc_male += line.amount
                    self.nb_male_ipres_rc += 1
                if line.employee_id.gender == 'female':
                    self.total_ipres_rc_female += line.total
                    self.total_base_rc_female += line.amount
                    self.nb_female_ipres_rc += 1
                self.nb_total_ipres_rc += 1
            elif line.code == 'C2030':  # ipres_rg
                if line.employee_id.gender == 'male':
                    self.total_ipres_rg_male += line.total
                    self.total_base_rg_male += line.amount
                    self.nb_male_ipres_rg += 1
                if line.employee_id.gender == 'female':
                    self.total_ipres_rg_female += line.total
                    self.total_base_rg_female += line.amount
                    self.nb_female_ipres_rg += 1
                self.nb_total_ipres_rg += 1
            elif line.code == 'C2041':  # ipres_rc_pat
                if line.employee_id.gender == 'male':
                    self.total_ipres_rc_pat_male += line.total
                if line.employee_id.gender == 'female':
                    self.total_ipres_rc_pat_female += line.total
            elif line.code == 'C2031':  # ipres_rg_pat
                if line.employee_id.gender == 'male':
                    self.total_ipres_rg_pat_male += line.total
                if line.employee_id.gender == 'female':
                    self.total_ipres_rg_pat_female += line.total
            else:
                pass

        _logger.info("TOTAL IPRES RC MALE " + str(self.total_ipres_rc_male))
        _logger.info("TOTAL IPRES RC PAT MALE " + str(self.total_ipres_rc_pat_male))
        _logger.info("TOTAL IPRES RG MALE " + str(self.total_ipres_rg_male))
        _logger.info("TOTAL IPRES RG PAT MALE " + str(self.total_ipres_rg_pat_male))

        _logger.info("TOTAL IPRES RC FEMALE " + str(self.total_ipres_rc_female))
        _logger.info("TOTAL IPRES RC PAT FEMALE " + str(self.total_ipres_rc_pat_female))
        _logger.info("TOTAL IPRES RG FEMALE " + str(self.total_ipres_rg_female))
        _logger.info("TOTAL IPRES RG PAT FEMALE " + str(self.total_ipres_rg_pat_female))

        lines_data_male.append({
            'Brut': int(self.total_brut_male),
            'Ipres_rc': int(self.total_ipres_rc_male),
            'Ipres_rg': int(self.total_ipres_rg_male),
            'Ipres_rc_pat': int(self.total_ipres_rc_pat_male),
            'Ipres_rg_pat': int(self.total_ipres_rg_pat_male),
            'Base_rc': int(self.total_base_rc_male),
            'Base_rg': int(self.total_base_rg_male),
            'Total_rc': int(self.total_ipres_rc_male + self.total_ipres_rc_pat_male),
            'Total_rg': int(self.total_ipres_rg_male + self.total_ipres_rg_pat_male),
            'Cotisation_totale': int(self.total_ipres_rc_male + self.total_ipres_rc_pat_male +
                                     self.total_ipres_rg_male + self.total_ipres_rg_pat_male),
        })

        lines_data_female.append({
            'Brut': int(self.total_brut_female),
            'Ipres_rc': int(self.total_ipres_rc_female),
            'Ipres_rg': int(self.total_ipres_rg_female),
            'Ipres_rc_pat': int(self.total_ipres_rc_pat_female),
            'Ipres_rg_pat': int(self.total_ipres_rg_pat_female),
            'Base_rc': int(self.total_base_rc_female),
            'Base_rg': int(self.total_base_rg_female),
            'Total_rc': int(self.total_ipres_rc_female + self.total_ipres_rc_pat_female),
            'Total_rg': int(self.total_ipres_rg_female + self.total_ipres_rg_pat_female),
            'Cotisation_totale': int(self.total_ipres_rc_female + self.total_ipres_rc_pat_female +
                                     self.total_ipres_rg_female + self.total_ipres_rg_pat_female),
        })

        lines_total = []
        lines_total.append({
            'total_cotisation': int(round(self.total_ipres_rc_male + self.total_ipres_rc_pat_male +
                                          self.total_ipres_rg_male + self.total_ipres_rg_pat_male + self.total_ipres_rc_female +
                                          self.total_ipres_rc_pat_female + self.total_ipres_rg_female + self.total_ipres_rg_pat_female)),
            'total_rc': int(round(self.total_ipres_rc_male + self.total_ipres_rc_pat_male +
                                  self.total_ipres_rc_female + self.total_ipres_rc_pat_female)),
            'total_rg': int(round(self.total_ipres_rg_male + self.total_ipres_rg_pat_male +
                                  self.total_ipres_rg_female + self.total_ipres_rg_pat_female)),
            'total_base_rc': int(round(self.total_base_rc_male + self.total_base_rc_female)),
            'total_base_rg': int(round(self.total_base_rg_male + self.total_base_rg_female)),
            'total_brut': int(round(self.total_brut_male + self.total_brut_female)),
            'total_ipres_rc': int(round(self.total_ipres_rc_male + self.total_ipres_rc_female)),
            'total_ipres_rg': int(round(self.total_ipres_rg_male + self.total_ipres_rg_female)),
            'total_ipres_rc_pat': int(round(self.total_ipres_rc_pat_male + self.total_ipres_rc_pat_female)),
            'total_ipres_rg_pat': int(round(self.total_ipres_rg_pat_male + self.total_ipres_rg_pat_female)),
        })

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_data_male': lines_data_male,
            'lines_data_female': lines_data_female,
            'lines_total': lines_total,
            'nb_male_brut': self.nb_male_brut,
            'nb_total_brut': self.nb_total_brut,
            'nb_total_ipres_rc': self.nb_total_ipres_rc,
            'nb_total_ipres_rg': self.nb_total_ipres_rg,
            'nb_male_ipres_rc': self.nb_male_ipres_rc,
            'nb_male_ipres_rg': self.nb_male_ipres_rg,
            'nb_female_brut': self.nb_female_brut,
            'nb_female_ipres_rc': self.nb_female_ipres_rc,
            'nb_female_ipres_rg': self.nb_female_ipres_rg,
            'date_from': datetime.strftime(date_from, '%d/%m/%Y'),
            'date_to': datetime.strftime(date_to, '%d/%m/%Y')
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: