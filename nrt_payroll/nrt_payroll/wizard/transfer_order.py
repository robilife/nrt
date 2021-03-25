# -*- coding: utf-8 -*-
# by khk

import time
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class optesis_transfer_order(models.TransientModel):
    _name = 'optesis.transfer.order'
    _description = 'order de virement'

    date_from = fields.Date('Date de la paie', required=True, default=lambda *a: time.strftime('%Y-%m-01'))

    def print_report_transfer_order(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'hr.contribution.register',
            'form': self.read()[0]
        }
        return self.env.ref('nrt_payroll.transfer_order').report_action([], data=datas)
