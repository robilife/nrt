# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

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
    ipres = fields.Char('Numero IPRES')
    mutuelle = fields.Char('Numero mutuelle')
    compte = fields.Char('Compte contribuable')
    num_chezemployeur = fields.Char('Numero chez l\'employeur')
    # relation_ids = fields.One2many('optesis.relation', 'employee_id', 'Relation')
    nb_part = fields.Float('Nombre de parts IR', default=1)
    trimf = fields.Float('Nombre de parts TRIMF', default=1)
    #ir_changed = fields.Integer(default=0)
    number_of_minor_children = fields.Integer(string="Nombre d’enfants mineurs")
    number_no_fourteen_children = fields.Integer(string="Nombre d’enfants moins de 14 ans")
    regime_type = fields.Selection([('cadre','CADRE'),('non_cadre','NON CADRE')], string='Statut')
    # grade = fields.Selection([('b2', 'BAC+2'), ('b3', 'BAC+3'), ('b4', 'BAC+4'), ('b5', 'BAC+5')], string="Niveau d'étude")
    # diplome = fields.Char(string="Diplôme")
    post_duration = fields.Char(string="Ancienneté à Neurotech")
    post_duration_year = fields.Integer(string="Ancienneté(Année)")
    debut = fields.Date("Date d'embauche")


    # def process_scheduler_check_employee_child_grown(self):
    #     for empl_obj in self.env['hr.employee'].search([]):
    #         empl_obj.get_ir_trimf()

    # @api.multi
    # @api.depends('relation_ids')
    # def get_ir_trimf(self):
    #     for value in self:
    #         old_ir = value.nb_part
    #         value.nb_part = 1
    #         value.trimf = 1
    #         nbj_sup = 0
    #         for line in value.relation_ids:
    #             if line.type == 'enfant':
    #                 now = datetime.now()
    #                 dur = now - line.birth
    #                 if dur.days < 7670:  # check if child is grown
    #                     value.nb_part += 0.5

    #                 if dur.days <= 5114 and value.gender == 'female':  # get extra days for holidays
    #                     nbj_sup += 1

    #             if line.type == 'conjoint':
    #                 if line.salari == 0:
    #                     value.nb_part += 1
    #                     value.trimf += 1
    #                 else:
    #                     value.nb_part += 0.5
    #                 value.marital = 'married'

    #         if value.contract_id:
    #             old_nbj_sup = value.contract_id.nbj_sup
    #             if nbj_sup > old_nbj_sup:
    #                 value.contract_id.write({'nbj_sup': nbj_sup})
    #                 # create leaves line allocation
    #                 self.env['hr.leave.allocation'].create({
    #                     'name': "Extra days Allowance",
    #                     'number_of_days': nbj_sup,
    #                     'state': 'validate',
    #                     'employee_id': value.id
    #                 })

    #         if value.nb_part >= 5:
    #             value.nb_part = 5
    #         if value.trimf >= 5:
    #             value.trimf = 5
    #         if old_ir != value.nb_part:
    #             value.ir_changed = 1


# class OptesisRelation(models.Model):
#     _name = 'optesis.relation'
#     _description = "les relations familiales"

#     type = fields.Selection([('conjoint', 'Conjoint'), ('enfant', 'Enfant'), ('autre', 'Autres parents')],
#                             'Type de relation')
#     nom = fields.Char('Nom')
#     prenom = fields.Char('Prenom')
#     birth = fields.Datetime('Date de naissance')
#     date_mariage = fields.Datetime('Date de mariage')
#     salari = fields.Boolean('Salarie', default=0)
#     employee_id = fields.Many2one('hr.employee')


class HrContractBonus(models.Model):
    _inherit = 'hr.contract'

    nb_days = fields.Float(string="Anciennete", compute="_get_duration")
    cumul_jour = fields.Float("Cumul jours anterieur")
    cumul_conges = fields.Float("Cumul conges anterieur")
    nbj_alloue = fields.Float("Nombre de jour alloue", default="2.5")
    nbj_travail = fields.Float("Nombre de jour de travail", default="30")
    nbj_aquis = fields.Float("Nombre de jour aquis", store=True)
    convention_id = fields.Many2one('line.optesis.convention', 'Categorie')
    nbj_pris = fields.Float("Nombre de jour pris", default="0")
    cumul_mensuel = fields.Float("Cumul mensuel conges")
    last_date = fields.Date("derniere date")
    alloc_conges = fields.Float("Allocation conges", compute="_get_alloc")
    motif = fields.Selection([('demission', 'Démission'), ('fin', 'Fin de contrat'), ('retraite', 'Retraite'),
                              ('licenciement', 'Licenciement'), ('deces', 'Décès'),
                              ('depart_nogicie', 'Départ négocié')], string='Motif de sortie')
    dateAnciennete = fields.Date("Date d'ancienneté", default=lambda self: fields.Date.to_string(date.today()))
    typeContract = fields.Selection([('cdi', 'CDI'), ('cdd', 'CDD'), ('others', 'Autres')], string="Type de contract")
    nbj_sup = fields.Float("Nombre de jour supplementaire")
    year_extra_day_anciennete = fields.Integer()

    sursalaire = fields.Float(string="Sursalaire")
    carburant = fields.Float(string="Carburant")
    carburant_non_imposable = fields.Float(string="Carburant non imposable")
    remboursement = fields.Float(string="Remboursement frais de formation")
    rapel_salaire = fields.Float(string="Rappel de Salaire")
    avantage_nature = fields.Float(string="Avantage en Nature")

    avance = fields.Float(string="Acompte sur salaire")
    avance_tabaski = fields.Float(string="Avance tabaski")
    avance_korite = fields.Float(string="Avance Korite")
    avance_noel = fields.Float(string="Avance Noel")

    indemite_preavis = fields.Float(string="Indemnite preavis")
    indemite_compensation_preavis = fields.Float(string="Compensation preavis")
    indemite_kilometrique = fields.Float(string="Indemnite Kilometrique")
    indemnite_conges = fields.Float(string="Indemnite conges")

    retenu_sport = fields.Float(string="Retenue de sport")
    retenu = fields.Float(string="Retenue pret")
    retenue_car = fields.Float(string="Retenue Car Plan")
    retenu_sante = fields.Float(string="Retenue assurance maladie")

    prime_exc = fields.Float(string="Prime Exceptionnelle")
    prime_rendement = fields.Float(string="Prime de Rendement")
    prime_resp = fields.Float(string="Prime de responsabilite")
    prime_risque = fields.Float(string="Prime de Risque")
    prime_salissure = fields.Float(string="Prime de salissure")
    prime_transport = fields.Float(string="Prime de transport")
    carburant_non_imposable = fields.Float(string="Carburant non imposable")
    restauration = fields.Float(string="Restauration")
    ticket_restau = fields.Float(string="Ticket restaurant")
    prime_logement = fields.Float(string="Prime de logement")
    remboursement_formation = fields.Float(string="remboursement formation")

    @api.cr_uid_ids_context
    def reinit(self, contract_ids):
        for record in self.browse(contract_ids):
            record.cumul_mensuel = record.cumul_mensuel - record.alloc_conges
            record.alloc_conges = 0
            record.nbj_aquis = record.nbj_aquis - record.nbj_pris
            record.nbj_pris = 0

    @api.onchange("convention_id")
    def onchange_categ(self):
        if self.convention_id:
            self.wage = self.convention_id.wage

    @api.multi
    def _get_droit(self, date):
        for record in self:
            code = "C1150"  # provision holidays
            query = "SELECT (case when hp.credit_note = False then (pl.total) else (-pl.total) end) \
                        FROM hr_payslip as hp, hr_payslip_line as pl \
                        WHERE pl.employee_id = %s \
                        AND pl.slip_id = hp.id \
                        AND hp.date_from <= %s AND hp.date_to >= %s AND pl.code = %s"
            self.env.cr.execute(query, (record.employee_id.id, date, date, code))
            result = self.env.cr.fetchone()[0] or 0.0
            cumul_mensuel = result

            if record.cumul_conges == 0:
                record.cumul_mensuel += cumul_mensuel
            else:
                val_pr = record.cumul_conges + cumul_mensuel
                record.cumul_mensuel += val_pr
                record.cumul_conges = 0

            if record.cumul_jour == 0:
                record.nbj_aquis += record.nbj_alloue
            else:
                nb_aquis = record.nbj_alloue + record.cumul_jour
                record.nbj_aquis += nb_aquis
                record.cumul_jour = 0

            # create leaves line allocation
            self.env['hr.leave.allocation'].create({
                'name': 'Leave allowance',
                'number_of_days': record.nbj_alloue,
                'state': 'validate',
                'employee_id': record.employee_id.id
            })

    @api.multi
    @api.depends("cumul_mensuel", "nbj_pris", "nbj_aquis")
    def _get_alloc(self):
        for record in self:
            if record.nbj_pris == 0 and record.cumul_mensuel == 0:
                return True
            if record.nbj_pris == 0 and record.cumul_mensuel != 0:
                return True
            if record.nbj_pris != 0 and record.cumul_mensuel == 0:
                return True
            if record.nbj_pris != 0 and record.cumul_mensuel != 0:
                if record.nbj_aquis == 0:
                    return True
                else:
                    record.alloc_conges = (record.cumul_mensuel * record.nbj_pris) / record.nbj_aquis
            if record.nbj_aquis >= record.nbj_travail:
                record.alloc_conges = (record.cumul_mensuel * record.nbj_pris) / record.nbj_travail

    @api.depends('dateAnciennete')
    def _get_duration(self):
        for record in self:
            server_dt = DEFAULT_SERVER_DATE_FORMAT
            today = datetime.now()
            dateAnciennete = datetime.strptime(str(record.dateAnciennete), server_dt)
            dur = today - dateAnciennete
            record.nb_days = dur.days
            # check if employee seniority is more than 10 years
            # if it is we add one day in nbj_aquis
            if dur.days >= 3653:
                if record.year_extra_day_anciennete:
                    if record.year_extra_day_anciennete != today.year:  # we must add it one time by year
                        record.year_extra_day_anciennete = today.year
                        record.nbj_aquis += 1
                        # create leaves line allocation
                        self.env['hr.leave.allocation'].create({
                            'name': 'Leave allowance for seniority',
                            'number_of_days': 1,
                            'state': 'validate',
                            'employee_id': record.employee_id.id
                        })
                else:
                    record.year_extra_day_anciennete = today.year
                    record.nbj_aquis += 1
                    # create leaves line allocation
                    self.env['hr.leave.allocation'].create({
                        'name': 'Leave allowance for seniority',
                        'number_of_days': 1,
                        'state': 'validate',
                        'employee_id': record.employee_id.id
                    })


class BonusRuleInput(models.Model):
    _inherit = 'hr.payslip'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('validate', 'Validé'),
        ('done', 'clôturer'),
        ('cancel', 'Rejected'),
    ])
    typePaiement = fields.Selection([('espece','Especes'),
    ('cheque','Cheque'),
    ('virement','Virement')],
     string="Type de paiement", states={'done': [('readonly', True)]})
    seniority_year = fields.Integer(string="Ancienneté(Année)", compute='_get_seniorty', store=True, states={'done': [('readonly', True)]})
    seniority_char = fields.Char(string="Ancienneté", compute='_get_seniorty', store=True, states={'done': [('readonly', True)]})



    @api.one
    @api.depends('employee_id')
    def _get_nb_part_of_payslip(self):
        for payslip in self:
            if payslip.employee_id:
                payslip.nb_part_of_payslip = payslip.employee_id.nb_part

    @api.one
    @api.depends('employee_id')
    def _get_seniorty(self):
        for payslip in self:
            if payslip.employee_id.debut:
                if payslip.employee_id.debut:
                    server_dt = DEFAULT_SERVER_DATE_FORMAT
                    date_start_contract = datetime.strptime(str(payslip.employee_id.debut), server_dt)
                    date_stop_period_payslip = datetime.strptime(str(payslip.date_to), server_dt)
                    timedelta = date_stop_period_payslip - date_start_contract
                    diff_day = timedelta.days / float(365)
                    if timedelta.days // 365 == 0:
                        payslip.seniority_char = str(int(diff_day % 1 * 12)) + ' Mois'
                    else:
                        payslip.seniority_char = str(timedelta.days // 365) + ' An(s) et  ' + str(int(diff_day % 1 * 12)) + ' Mois'
                    payslip.seniority_year = timedelta.days // 365


    @api.model
    def create(self, vals):
        res = super(BonusRuleInput, self).create(vals)
        if not res.credit_note:
            cr = self._cr
            if res.contract_id.state == 'open':
                if not res.contract_id.date_start <= res.date_from:  # <= res.contract_id.date_end:
                    raise ValidationError(_("You cannot create payslip for the dates out of the contract period"))
                if res.contract_id.date_end:
                    if not res.date_to <= res.contract_id.date_end:
                        raise ValidationError(_("You cannot create payslip for the dates out of the contract period"))

                query = """SELECT date_from, date_to FROM "hr_payslip" WHERE employee_id = %s AND state = 'done'"""
                cr.execute(query, ([res.employee_id.id]))
                date_from_to = cr.fetchall()
                for items in date_from_to:
                    if res.date_from == items[0] and res.date_to == items[1]:
                        raise ValidationError(_("You cannot create payslip for the same period"))
                    else:
                        if not (items[1] <= res.date_from >= items[0] or items[0] >= res.date_to <= items[1]):
                            raise ValidationError(_("You cannot create payslip for the same period"))
            else:
                raise ValidationError(_("You cannot create payslip with status not open "))

        return res

    @api.multi
    def action_payslip_validate(self):
        for payslip in self:
            contract_ids = payslip.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            for line in payslip.line_ids:
                if line.code == "C1060":
                    self.env['hr.contract'].reinit(contract_ids)
                    break
            return payslip.write({'state': 'validate'})

    @api.multi
    def action_payslip_done(self):
        for payslip in self:
            payslip.contract_id._get_droit(payslip.date_from)
        return super(BonusRuleInput, self).action_payslip_done()

    @api.multi
    def update_recompute_ir(self):
        server_dt = DEFAULT_SERVER_DATE_FORMAT
        for payslip in self:
            year = datetime.strptime(str(payslip.date_from), server_dt).year

            ir_changed = 0
            two_last_payslip = self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)], order="id desc", limit=2)
            # compute ir recal
            if len(two_last_payslip) > 1:
                if two_last_payslip[1].nb_part_of_payslip != payslip.employee_id.nb_part:
                    ir_changed = 1
                    for line in self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)], limit=12):
                        if datetime.strptime(str(line.date_from), server_dt).year == year:
                            cumul_tranche_ipm = 0.0
                            deduction = 0.0
                            payslip_line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', line.id)])
                            cumul_tranche_ipm += sum(
                                payslip_line.total for payslip_line in payslip_line_ids if payslip_line.code == "C2110")

                            for payslip_line in payslip_line_ids:
                                if payslip_line.code == "C2150":
                                    obj_empl = self.env['hr.employee'].browse(payslip.employee_id.id)
                                    if obj_empl:
                                        if payslip.employee_id.nb_part == 1:
                                            deduction = 0.0

                                        if payslip.employee_id.nb_part == 1.5:
                                            if cumul_tranche_ipm * 0.1 < 8333:
                                                deduction = 8333
                                            elif cumul_tranche_ipm * 0.1 > 25000:
                                                deduction = 25000
                                            else:
                                                deduction = cumul_tranche_ipm * 0.1

                                        if payslip.employee_id.nb_part == 2:
                                            if cumul_tranche_ipm * 0.15 < 16666.66666666667:
                                                deduction = 16666.66666666667
                                            elif cumul_tranche_ipm * 0.15 > 54166.66666666667:
                                                deduction = 54166.66666666667
                                            else:
                                                deduction = cumul_tranche_ipm * 0.15

                                        if payslip.employee_id.nb_part == 2.5:
                                            if cumul_tranche_ipm * 0.2 < 25000:
                                                deduction = 25000
                                            elif cumul_tranche_ipm * 0.2 > 91666.66666666667:
                                                deduction = 91666.66666666667
                                            else:
                                                deduction = cumul_tranche_ipm * 0.2

                                        if payslip.employee_id.nb_part == 3:
                                            if cumul_tranche_ipm * 0.25 < 33333.33333333333:
                                                deduction = 33333.33333333333
                                            elif cumul_tranche_ipm * 0.25 > 137500:
                                                deduction = 137500
                                            else:
                                                deduction = cumul_tranche_ipm * 0.25

                                        if payslip.employee_id.nb_part == 3.5:
                                            if cumul_tranche_ipm * 0.3 < 41666.66666666667:
                                                deduction = 41666.66666666667
                                            elif cumul_tranche_ipm * 0.3 > 169166.6666666667:
                                                deduction = 169166.6666666667
                                            else:
                                                deduction = cumul_tranche_ipm * 0.3

                                        if payslip.employee_id.nb_part == 4:
                                            if cumul_tranche_ipm * 0.35 < 50000:
                                                deduction = 50000
                                            elif cumul_tranche_ipm * 0.35 > 207500:
                                                deduction = 207500
                                            else:
                                                deduction = cumul_tranche_ipm * 0.35

                                        if payslip.employee_id.nb_part == 4.5:
                                            if cumul_tranche_ipm * 0.4 < 58333.33333:
                                                deduction = 58333.33333
                                            elif cumul_tranche_ipm * 0.4 > 229583.3333:
                                                deduction = 229583.3333
                                            else:
                                                deduction = cumul_tranche_ipm * 0.4

                                        if payslip.employee_id.nb_part == 5:
                                            if cumul_tranche_ipm * 0.45 < 66666.66667:
                                                deduction = 66666.66667
                                            elif cumul_tranche_ipm * 0.45 > 265000:
                                                deduction = 265000
                                            else:
                                                deduction = cumul_tranche_ipm * 0.45

                                        if cumul_tranche_ipm - deduction > 0:
                                            ir_val_recal = cumul_tranche_ipm - deduction
                                        else:
                                            ir_val_recal = 0
                                        # update ir_recal
                                        obj = self.env['hr.payslip.line'].search(
                                            [('code', '=', payslip_line.code), ('slip_id', '=', line.id)], limit=1)
                                        if obj:
                                            obj.write({'amount': round(ir_val_recal)})
            # end compute ir_recal

            ir_payslip = 0.0
            net_payslip = 0.0
            ir_payslip += sum(payslip_line.total for payslip_line in payslip.line_ids if
                              payslip_line.code == "C2140")
            net_payslip += sum(payslip_line.total for payslip_line in payslip.line_ids if
                               payslip_line.code == "C5000")

            # update the ir_regul of current payslip by doing sum(ir) - sum(ir_recal) of previous payslip
            if ir_changed == 1:
                ir_annuel = 0.0
                ir_recal_annuel = 0.0
                for line in self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)]):
                    if datetime.strptime(str(line.date_from), server_dt).year == year:
                        ir_annuel += sum(payslip_line.total for payslip_line in line.line_ids if
                                         payslip_line.code == "C2140")
                        ir_recal_annuel += sum(
                            payslip_line.total for payslip_line in line.line_ids if
                            payslip_line.code == "C2150")

                        [obj.write({'amount': round(ir_annuel - ir_recal_annuel)}) for obj in
                         payslip.line_ids if obj.code == "C2160"]

                [obj.write({'amount': round(ir_payslip - (ir_annuel - ir_recal_annuel))}) for obj in
                 payslip.line_ids if obj.code == "C2170"]

            else:
                [obj.write({'amount': round(ir_payslip)}) for obj in
                 payslip.line_ids if obj.code == "C2170"]

            # defalquer ir_fin du net
            ir_fin = 0.0
            ir_fin += sum(payslip_line.total for payslip_line in payslip.line_ids if
                          payslip_line.code == "C2170")
            [obj.write({'amount': round(net_payslip - ir_fin)}) for obj in
             payslip.line_ids if obj.code == "C5000"]

            # compute and update salary rule provision de fin de contract
            if payslip.contract_id.typeContract == "cdd":
                val = payslip.compute_end_contract_provision()
                [obj.write({'amount': round(val)}) for obj in payslip.line_ids if obj.code == "C1130"]

            # compute_loan_balance
            if payslip.contract_id.motif:
                val_loan_balance = payslip.loan_balance()
                if val_loan_balance != 0:
                    [payslip_line.write({'amount': round(net_payslip - val_loan_balance)}) for payslip_line in
                     payslip.line_ids if payslip_line.code == "C5000"]

    @api.multi
    def compute_sheet(self):
        for payslip in self:
            if payslip.state == "draft":
                if payslip.contract_id.date_end:
                    if payslip.date_from > payslip.contract_id.date_end:
                        raise ValidationError(
                            _("La date du bulletin ne peut pas être supérieur à la date de sortie du contract"))

                number = payslip.number or self.env['ir.sequence'].sudo().next_by_code('salary.slip')
                # delete old payslip lines
                payslip.line_ids.unlink()
                # set the list of contract for which the rules have to be applied
                # if we don't give the contract, then the rules to apply should be
                # for all current contracts of the employee
                contract_ids = payslip.contract_id.ids or \
                               self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
                payslip.contract_id._get_duration()
                lines = [(0, 0, line) for line in self.get_payslip_lines(contract_ids, payslip.id)]
                payslip.write({'line_ids': lines, 'number': number})

                payslip.update_recompute_ir()

        return True

    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        for record in self:
            def _sum_salary_rule_category(localdict, category, amount):
                if category.parent_id:
                    localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
                if category.code in localdict['categories'].dict:
                    amount += localdict['categories'].dict[category.code]
                localdict['categories'].dict[category.code] = amount
                return localdict

            class BrowsableObject(object):
                def __init__(record, employee_id, dict, env):
                    record.employee_id = employee_id
                    record.dict = dict
                    record.env = env

                def __getattr__(record, attr):
                    return attr in record.dict and record.dict.__getitem__(attr) or 0.0

            class InputLine(BrowsableObject):
                """a class that will be used into the python code, mainly for usability purposes"""

                def sum(record, code, from_date, to_date=None):
                    if to_date is None:
                        to_date = fields.Date.today()
                    record.env.cr.execute("""
                            SELECT sum(amount) as sum
                            FROM hr_payslip as hp, hr_payslip_input as pi
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                          (record.employee_id, from_date, to_date, code))
                    return self.env.cr.fetchone()[0] or 0.0

            class WorkedDays(BrowsableObject):
                """a class that will be used into the python code, mainly for usability purposes"""

                def _sum(record, code, from_date, to_date=None):
                    if to_date is None:
                        to_date = fields.Date.today()
                    record.env.cr.execute("""
                            SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                          (record.employee_id, from_date, to_date, code))
                    return record.env.cr.fetchone()

                def sum(record, code, from_date, to_date=None):
                    res = record._sum(code, from_date, to_date)
                    return res and res[0] or 0.0

                def sum_hours(record, code, from_date, to_date=None):
                    res = record._sum(code, from_date, to_date)
                    return res and res[1] or 0.0

            class Payslips(BrowsableObject):
                """a class that will be used into the python code, mainly for usability purposes"""

                def sum(record, code, from_date, to_date=None):
                    if to_date is None:
                        to_date = fields.Date.today()
                    record.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                                    FROM hr_payslip as hp, hr_payslip_line as pl
                                    WHERE hp.employee_id = %s AND hp.state = 'done'
                                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                          (record.employee_id, from_date, to_date, code))
                    res = record.env.cr.fetchone()
                    return res and res[0] or 0.0

            # we keep a dict with the result because a value can be overwritten by another rule with the same code
            result_dict = {}
            rules_dict = {}
            worked_days_dict = {}
            inputs_dict = {}
            blacklist = []
            payslip = record.env['hr.payslip'].browse(payslip_id)
            for worked_days_line in payslip.worked_days_line_ids:
                worked_days_dict[worked_days_line.code] = worked_days_line
            for input_line in payslip.input_line_ids:
                inputs_dict[input_line.code] = input_line

            categories = BrowsableObject(payslip.employee_id.id, {}, record.env)
            inputs = InputLine(payslip.employee_id.id, inputs_dict, record.env)
            worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, record.env)
            payslips = Payslips(payslip.employee_id.id, payslip, record.env)
            rules = BrowsableObject(payslip.employee_id.id, rules_dict, record.env)

            baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days,
                             'inputs': inputs}
            # get the ids of the structures on the contracts and their parent id as well
            contracts = record.env['hr.contract'].browse(contract_ids)
            structure_ids = contracts.get_all_structures()
            # get the rules of the structure and thier children
            rule_ids = record.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()

            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
            sorted_rules = record.env['hr.salary.rule'].browse(sorted_rule_ids)

            brut_of_current_payslip = 0.0
            for contract in contracts:
                employee = contract.employee_id
                localdict = dict(baselocaldict, employee=employee, contract=contract)
                for rule in sorted_rules:
                    key = rule.code + '-' + str(contract.id)
                    localdict['result'] = None
                    localdict['result_qty'] = 1.0
                    localdict['result_rate'] = 100
                    # check if the rule can be applied
                    if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                        # compute the amount of the rule
                        amount, qty, rate = rule._compute_rule(localdict)

                        #
                        if rule.category_id.code == 'INDM' or rule.category_id.code == 'BASE' or \
                                rule.category_id.code == 'NOIMP':
                            brut_of_current_payslip += amount

                        if rule.code == 'C1040':  # indemnite de fin de contrat
                            amount = payslip.compute_end_contract_allowance(brut_of_current_payslip)
                        elif rule.code == 'C1120':  # indemnite de retraite
                            amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                        elif rule.code == 'C1145':  # indemnite de licenciement
                            amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                        elif rule.code == 'C1146':  # indemnite de deces
                            amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                        elif rule.code == 'C1147':  # provision de retraite
                            amount = payslip.compute_provision_retraite(brut_of_current_payslip)
                        else:
                            pass
                        # check if there is already a rule computed with that code
                        previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                        # set/overwrite the amount computed for this rule in the localdict
                        tot_rule = amount * qty * rate / 100.0
                        localdict[rule.code] = tot_rule
                        rules_dict[rule.code] = rule
                        # sum the amount for its salary category
                        localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                        # create/overwrite the rule in the temporary results
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': rule.name,
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                        }
                    else:
                        # blacklist this rule and its children
                        blacklist += [id for id, seq in rule._recursive_search_of_rules()]
                # payslips.contract_id._get_duration(payslips.date_from)

            return [value for code, value in result_dict.items()]

    # for changing the number
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract
         between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), t.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), t.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name,
                    'sequence': 5,
                    'code': holiday.holiday_status_id.name,
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, t.min)),
                    tz.localize(datetime.combine(day, t.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

            # compute worked days
            # work_data = contract.employee_id.get_work_days_data(day_from,
            # day_to, calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 30,
                'number_of_hours': 173.33,
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res


class HrPayslipRunExtend(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validé'),
        ('done', 'Done'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def validate_payslip(self):
        for slip in self.slip_ids:
            for slip in self.slip_ids:
                if slip.state != 'validate' and slip.state != 'done':
                    slip.action_payslip_validate()
        self.write({'state': 'validate'})

    def pay_payslip(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        line_ids = []
        dict = {}

        index_deb = 0
        index_cred = 0
        for slip in self.slip_ids:
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            if slip.state != 'done':
                for line in slip.details_by_salary_rule_category:
                    amount = slip.credit_note and -line.total or line.total
                    if float_is_zero(amount, precision_digits=precision):
                        continue
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id

                    if debit_account_id:
                        # if account code start with 421 we do not regroup
                        if line.salary_rule_id.account_debit.code[:3] == "421" or \
                                line.salary_rule_id.account_debit.code[:3] == "422":
                            index_deb += 1
                            dict[debit_account_id + index_deb] = {}
                            dict[debit_account_id + index_deb]['name'] = line.name
                            dict[debit_account_id + index_deb]['partner_id'] = line._get_partner_id(
                                credit_account=True)
                            dict[debit_account_id + index_deb]['account_id'] = debit_account_id
                            dict[debit_account_id + index_deb]['journal_id'] = slip.journal_id.id
                            dict[debit_account_id + index_deb]['date'] = date
                            dict[debit_account_id + index_deb]['debit'] = amount > 0.0 and amount or 0.0
                            dict[debit_account_id + index_deb]['credit'] = amount < 0.0 and -amount or 0.0
                            dict[debit_account_id + index_deb]['analytic_account_id'] = \
                                line.salary_rule_id.analytic_account_id.id
                            dict[debit_account_id + index_deb]['tax_line_id'] = line.salary_rule_id.account_tax_id.id
                        # else we regroup
                        else:
                            _logger.info(' in debit condition ' + str(debit_account_id))
                            if debit_account_id in dict:
                                dict[debit_account_id]['debit'] += amount > 0.0 and amount or 0.0
                                dict[debit_account_id]['credit'] += amount < 0.0 and -amount or 0.0
                            else:
                                dict[debit_account_id] = {}
                                dict[debit_account_id]['name'] = line.name
                                dict[debit_account_id]['partner_id'] = line._get_partner_id(credit_account=False)
                                dict[debit_account_id]['account_id'] = debit_account_id
                                dict[debit_account_id]['journal_id'] = slip.journal_id.id
                                dict[debit_account_id]['date'] = date
                                dict[debit_account_id]['debit'] = amount > 0.0 and amount or 0.0
                                dict[debit_account_id]['credit'] = amount < 0.0 and -amount or 0.0
                                dict[debit_account_id][
                                    'analytic_account_id'] = line.salary_rule_id.analytic_account_id.id
                                dict[debit_account_id]['tax_line_id'] = line.salary_rule_id.account_tax_id.id

                        debit_sum += amount > 0.0 and amount or 0.0 - amount < 0.0 and -amount or 0.0

                    if credit_account_id:
                        # if account code start with 421 we do not regroup
                        if line.salary_rule_id.account_credit.code[:3] == "421" or \
                                line.salary_rule_id.account_credit.code[:3] == "422":
                            index_cred += 1
                            dict[credit_account_id + index_cred] = {}
                            dict[credit_account_id + index_cred]['name'] = line.name
                            dict[credit_account_id + index_cred]['partner_id'] = line._get_partner_id(
                                credit_account=True)
                            dict[credit_account_id + index_cred]['account_id'] = credit_account_id
                            dict[credit_account_id + index_cred]['journal_id'] = slip.journal_id.id
                            dict[credit_account_id + index_cred]['date'] = date
                            dict[credit_account_id + index_cred]['debit'] = amount < 0.0 and -amount or 0.0
                            dict[credit_account_id + index_cred]['credit'] = amount > 0.0 and amount or 0.0
                            dict[credit_account_id + index_cred]['analytic_account_id'] = \
                                line.salary_rule_id.analytic_account_id.id
                            dict[credit_account_id + index_cred]['tax_line_id'] = \
                                line.salary_rule_id.account_tax_id.id
                        # else we regroup
                        else:
                            _logger.info(' in credit condition ' + str(credit_account_id))
                            if credit_account_id in dict:
                                dict[credit_account_id]['debit'] += amount < 0.0 and -amount or 0.0
                                dict[credit_account_id]['credit'] += amount > 0.0 and amount or 0.0
                            else:
                                dict[credit_account_id] = {}
                                dict[credit_account_id]['name'] = line.name
                                dict[credit_account_id]['partner_id'] = line._get_partner_id(credit_account=False)
                                dict[credit_account_id]['account_id'] = credit_account_id
                                dict[credit_account_id]['journal_id'] = slip.journal_id.id
                                dict[credit_account_id]['date'] = date
                                dict[credit_account_id]['debit'] = amount < 0.0 and -amount or 0.0
                                dict[credit_account_id]['credit'] = amount > 0.0 and amount or 0.0
                                dict[credit_account_id][
                                    'analytic_account_id'] = line.salary_rule_id.analytic_account_id.id
                                dict[credit_account_id]['tax_line_id'] = line.salary_rule_id.account_tax_id.id

                        credit_sum += amount > 0.0 and amount or 0.0 - amount < 0.0 and -amount or 0.0

                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_credit_account_id.id
                    if not acc_id:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                slip.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_debit_account_id.id
                    if not acc_id:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                                slip.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)

        for key, value in dict.items():
            move_line = (0, 0, {
                # 'name': dict[key]['name'],
                'partner_id': dict[key]['partner_id'],
                'account_id': dict[key]['account_id'],
                'journal_id': dict[key]['journal_id'],
                'date': dict[key]['date'],
                'debit': dict[key]['debit'],
                'credit': dict[key]['credit'],
                'analytic_account_id': dict[key]['analytic_account_id'],
                'tax_line_id': dict[key]['tax_line_id'],
            })
            line_ids.append(move_line)

        name = _('Payslips of  Batch %s') % self.name
        move_dict = {
            'narration': name,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'date': date,
            'line_ids': line_ids
        }

        move = self.env['account.move'].create(move_dict)
        move.write({'batch_id': slip.payslip_run_id.id})
        for slip_obj in self.slip_ids:
            if slip_obj.state != 'done':
                slip_obj.contract_id._get_droit(slip.date_from)
                slip_obj.write({'move_id': move.id, 'date': date, 'state': 'done'})
        # move.post()
        self.write({'state': 'done'})


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    fonction_employee = fields.Char(string='Fonction Employe', related='employee_id.job_id.name', store=True)
    categorie_employee = fields.Char(string="Categorie Employe", related='employee_id.contract_id.convention_id.name',
                                     store=True)
    payslip_date_from = fields.Date(string="Date de debut", related="slip_id.date_from", store=True)
    payslip_date_to = fields.Date(string="Date de fin", related="slip_id.date_to", store=True)


class HolidaysTypeInherit(models.Model):
    _inherit = "hr.leave.type"

    @api.multi
    def _compute_leaves(self):
        data_days = {}
        employee_id = self._get_contextual_employee_id()

        if employee_id:
            data_days = self.get_days(employee_id)

        for holiday_status in self:
            result = data_days.get(holiday_status.id, {})
            holiday_status.max_leaves = result.get('max_leaves', 0)
            holiday_status.leaves_taken = result.get('leaves_taken', 0)
            holiday_status.remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)

