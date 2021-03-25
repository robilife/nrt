# -*- coding: utf-8 -*-
# by khk
import xlwt
import base64
from io import StringIO
import time
from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models, api
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)


class optesis_payslip_lines_cotisation_ipres(models.TransientModel):
    _name = 'optesis.payslip.lines.cotisation.ipres'
    _description = 'cotisation ipres modele wizard'

    date_from = fields.Date('Date de debut', required=True,
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date de fin', required=True,
                          default=lambda *a: str(
                              datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])

    @api.multi
    def print_report_ipres(self):

        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'hr.contribution.register',
            'form': self.read()[0]
        }
        return self.env.ref('nrt_payroll.cotisation_ipres').report_action([], data=datas)
