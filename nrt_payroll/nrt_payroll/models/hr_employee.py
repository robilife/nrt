# -*- coding: utf-8 -*-
import time
from datetime import datetime, date, time as t
from dateutil import relativedelta
from odoo.tools import float_compare, float_is_zero
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError
from pytz import timezone
import logging

_logger = logging.getLogger(__name__)

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    matricule_cnss = fields.Char('Matricule CNSS')
    mutuelle = fields.Char('Numero mutuelle')
    compte = fields.Char('Compte contribuable')
    num_chezemployeur = fields.Char('Numero chez l\'employeur')
    contract_start = fields.Date(string="Date d'embauche")
    regime_type = fields.Selection([('cadre','CADRE'),('non_cadre','NON CADRE')], string='Statut')
    ipres_number = fields.Char('N° IPRES')
    trimf = fields.Float('Valeur TRIMF', default=1)
    serial_number = fields.Char('N° Matricule')
    personal_email = fields.Char('Email personnel')
    nb_part = fields.Float('Nb. parts sociales')