# -*- coding: utf-8 -*-
# by khk
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HrSalaryRuleInherit(models.Model):
    _inherit = 'hr.salary.rule'

    is_prorata = fields.Boolean(string='Prorata', default=True,
                                help="Used to check if we apply prorata")
