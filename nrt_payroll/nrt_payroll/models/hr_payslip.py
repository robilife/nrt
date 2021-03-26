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
log = logging.getLogger('Log')

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('validate', 'Validé'),
        ('done', 'clôturer'),
        ('cancel', 'Rejected'),
    ])

    typePaiement = fields.Selection([('espece','Espèces'),('cheque','Chèque'),('virement','Virement')], string="Type de paiement", states={'done': [('readonly', True)]}, default='virement')
    seniority_year = fields.Integer(string="Ancienneté(Année)", compute='_get_seniorty', states={'done': [('readonly', True)]})
    seniority_char = fields.Char(string="Ancienneté", compute='_get_seniorty', states={'done': [('readonly', True)]})
    nb_part_of_payslip = fields.Float(string="Nb part", compute="_get_nb_part_of_payslip", states={'done': [('readonly', True)]}, store=True)
    net = fields.Float(string="Salaire net", compute='_get_salary_rules', store=True)
    total_imposable = fields.Float(string="Total imposable", compute='_get_salary_rules', store=True)
    total_non_imposable = fields.Float(string="Total non imposable", compute='_get_salary_rules', store=True)
    salaire_base = fields.Float(string="Salaire de base", compute='_get_salary_rules', store=True)
    total_brut = fields.Float(string='Total brut', compute='_get_total_brut', store=True)
    nap = fields.Float(string='Net à payer', compute='_get_salary_rules', store=True)
    total_charge_salary = fields.Float(string="Total charge salariale", compute='_get_salary_rules', store=True)
    total_charge_patronale = fields.Float(string="Total charge patronale", compute='_get_salary_rules', store=True)

    @api.one
    @api.depends('line_ids')
    def _get_salary_rules(self):
        if self.line_ids:
            for line in self.line_ids:
                if line.code == 'C5000':
                    self.net = line.amount
                if line.code == 'C1000':
                    self.salaire_base = line.amount
                if line.code == 'C5000':
                    self.nap = line.amount
                if line.code == 'C3005':
                    total_charge_salary_1 = line.amount
                if line.code == 'C2170':
                    self.total_charge_salary = line.amount

                if line.code == 'C3010':
                    self.total_charge_patronale = line.amount

            self.total_imposable = sum(line.amount for line in self.env['hr.payslip.line'].search(
                [('slip_id', '=', self.id), ('code', 'in',
                                             ['C1000', 'C1010', 'C1015', 'C1020', 'C1030', 'C1035', 'C1043', 'C1044',
                                              'C1045', 'C1047', 'C1076', 'C1076', 'C1078', 'C1079', 'C1080',
                                              'C1140','C1041'])]))

            self.total_non_imposable = sum(line.amount for line in self.env['hr.payslip.line'].search(
                [('slip_id', '=', self.id), ('category_id.code', '=', 'NOIMP')]))

    @api.one
    @api.depends('total_imposable', 'total_non_imposable')
    def _get_total_brut(self):
        self.total_brut = self.total_imposable + self.total_non_imposable


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
            if payslip.employee_id.contract_start:
                    server_dt = DEFAULT_SERVER_DATE_FORMAT
                    date_start_contract = datetime.strptime(str(payslip.employee_id.contract_start), server_dt)
                    date_stop_period_payslip = datetime.strptime(str(payslip.date_to), server_dt)
                    timedelta = date_stop_period_payslip - date_start_contract
                    diff_day = timedelta.days / float(365)
                    payslip.seniority_char = str(timedelta.days // 365) + ' An(s) et  ' + str(int(diff_day % 1 * 12)) + ' Mois'
                    payslip.seniority_year = timedelta.days // 365


    @api.model
    def create(self, vals):
        res = super(HrPayslip, self).create(vals)
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
    def update_recompute_ir(self):
        server_dt = DEFAULT_SERVER_DATE_FORMAT
        for payslip in self:
            year = datetime.strptime(str(payslip.date_from), server_dt).year

            ir_changed = 0
            two_last_payslip = self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)], order="date_from desc", limit=2)
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
                                        obj = self.env['hr.payslip.line'].search([('code', '=', payslip_line.code), ('slip_id', '=', line.id)], limit=1)
                                        if obj:
                                            obj.write({'amount': round(ir_val_recal)})
            # end compute ir_recal

            ir_payslip = 0.0
            net_payslip = 0.0
            ir_payslip += sum(payslip_line.total for payslip_line in payslip.line_ids if payslip_line.code == "C2140")
            net_payslip += sum(payslip_line.total for payslip_line in payslip.line_ids if payslip_line.code == "C5000")

            # update the ir_regul of current payslip by doing sum(ir) - sum(ir_recal) of previous payslip
            if ir_changed == 1:
                ir_annuel = 0.0
                ir_recal_annuel = 0.0
                for line in self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)]):
                    if datetime.strptime(str(line.date_from), server_dt).year == year:
                            ir_annuel += sum(payslip_line.total for payslip_line in line.line_ids if payslip_line.code == "C2140")
                            ir_recal_annuel += sum(payslip_line.total for payslip_line in line.line_ids if payslip_line.code == "C2150")
                            ######" Test code #####

                            for payslip_line in line.line_ids :
                                if payslip_line.code == "C2150":

                                    log.error('C2150: '+str(payslip_line.total))
                            [obj.write({'amount': round(ir_annuel - ir_recal_annuel)}) for obj in payslip.line_ids if obj.code == "C2160"]

                    [obj.write({'amount': round(ir_payslip - (ir_annuel - ir_recal_annuel))}) for obj in payslip.line_ids if obj.code == "C2170"]

            else:
                [obj.write({'amount': round(ir_payslip)}) for obj in payslip.line_ids if obj.code == "C2170"]

            # defalquer ir_fin du net
            ir_fin = 0.0
            ir_fin += sum(payslip_line.total for payslip_line in payslip.line_ids if payslip_line.code == "C2170")
            [obj.write({'amount': round(net_payslip - ir_fin)}) for obj in payslip.line_ids if obj.code == "C5000"]

            # compute and update salary rule provision de fin de contract
            if payslip.contract_id.typeContract == "cdd":
                val = payslip.compute_end_contract_provision()
                [obj.write({'amount': round(val)}) for obj in payslip.line_ids if obj.code == "C1200"]

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

                        if rule.code == 'C1130':  # indemnite de fin de contrat
                            amount = payslip.compute_end_contract_allowance()
                        elif rule.code == 'C1120':  # indemnite de retraite
                            amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                        elif rule.code == 'C1145':  # indemnite de licenciement
                            amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                        elif rule.code == 'C1146':  # indemnite de deces
                            amount = payslip.compute_retirement_balance(brut_of_current_payslip)
                        elif rule.code == 'C1110':  # provision de retraite
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

    @api.multi
    def compute_provision_retraite(self, brut_of_current_payslip):
        """salaire_brut_val is the value of current payslip
        i use it like argument because i can not get the value of payslip line"""
        for payslip in self:
            # get last 12 payslip of employee
            payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)], order='id desc',
                                                        limit=12)
            #if len(payslip_ids) >= 11:
            cumul_brut = 0
            for line in payslip_ids:
                cumul_brut += sum(line.total for line in line.details_by_salary_rule_category if
                                      line.code in ['C1000', 'C1010', 'C1020', 'C1043', 'C1047',
                                       'C1076', 'C1078', 'C1079', 'C1080', 'C1090'])  # get salary brut of previous payslip

                # after the cumulates of last salary brut i add the value of current payslip and compute the average
            cumul_brut += brut_of_current_payslip
            moy_brut = cumul_brut / len(payslip_ids)

            diff = relativedelta.relativedelta(payslip.contract_id.dateAnciennete, payslip.date_to)
            if diff.years <= 5:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, -diff.years, -diff.months,
                                                                   -diff.days)  # moy_brut*(dur.days/360)*0.25

            elif 5 < diff.years <= 10:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_cinq(moy_brut, -diff.years - 5, -diff.months,
                                                                    -diff.days)  # moy_brut*(dur.days/360)*0.3
            else:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_cinq(moy_brut, -diff.years - 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_dix(moy_brut, -diff.years - 10, -diff.months, -diff.days)

            return round(provision_retraite)
        return 0.0


    def compute_pr_moin_cinq(self, moyb, years, months, days):
        amount_for_year = (moyb * 0.25) * float(years)
        amount_for_month = moyb * 0.25 * (float(months) / 12)
        amount_for_days = moyb * 0.25 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_pr_plus_cinq(self, moyb, years, months, days):
        amount_for_year = (moyb * 0.3) * float(years)
        amount_for_month = moyb * 0.3 * (float(months) / 12)
        amount_for_days = moyb * 0.3 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_pr_plus_dix(self, moyb, years, months, days):
        amount_for_year = (moyb * 0.4) * float(years)
        amount_for_month = moyb * 0.4 * (float(months) / 12)
        amount_for_days = moyb * 0.4 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    @api.multi
    def compute_retirement_balance(self, brut_of_current_payslip):
        for payslip in self:
            if payslip.contract_id.motif:
                return self.compute_provision_retraite(brut_of_current_payslip)

    @api.multi
    def compute_end_contract_provision(self):
        _logger.info("dans la function provision de fin de contract")
        payslip_line_ids = self.env['hr.payslip.line'].search(
            [('contract_id', '=', self.contract_id.id), ('employee_id', '=', self.employee_id.id),
             ('slip_id', '=', self.id)])
        amount = sum(line.total for line in payslip_line_ids if line.code in ['C1000', 'C1010', 'C1020', 'C1043',
         'C1047', 'C1076', 'C1078', 'C1079', 'C1080', 'C1090'])
        return amount * 0.07

    @api.multi
    def compute_end_contract_allowance(self):
        for payslip in self:
            cumul_provision = 0
            payslip_line_ids = self.env['hr.payslip.line'].search(
                [('contract_id', '=', payslip.contract_id.id), ('employee_id', '=', payslip.employee_id.id)])
            for line in payslip_line_ids:
                if line.code in ['C1200']:
                    cumul_provision += line.total
            log.error('Cumul :'+str(cumul_provision*0.07))
            return round(cumul_provision*0.07)

    @api.multi
    def loan_balance(self):
        for payslip in self:
            amount = 0
            loan_lines = self.env['hr.loan.line'].search(
                [('employee_id', '=', payslip.employee_id.id), ('paid', '=', False)])
            for loan_line in loan_lines:
                # on ne prend pas en compte les loans du mois courant
                if not payslip.date_from <= loan_line.paid_date <= payslip.date_to:
                    amount += loan_line.paid_amount
            return round(amount)

class HrPayslipRunExtend(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Confirmé'),
        ('done', 'Comptabilisé'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def validate_payslip(self):
        for slip in self.slip_ids:
            for slip in self.slip_ids:
                if slip.state != 'validate' and slip.state != 'done':
                    slip.action_payslip_validate()
        self.write({'state': 'validate'})

    def pay_payslip(self):
        self.write({'state':'done'})

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    fonction_employee = fields.Char(string='Fonction Employe', related='employee_id.job_id.name', store=True)
    categorie_employee = fields.Char(string="Categorie Employe", related='employee_id.contract_id.convention_id.name', store=True)
    payslip_date_from = fields.Date(string="Date de debut", related="slip_id.date_from", store=True)
    payslip_date_to = fields.Date(string="Date de fin", related="slip_id.date_to", store=True)
    department_id = fields.Many2one('hr.department','Département', related='employee_id.department_id', store=True)
    serial_number = fields.Char('Matricule', related='employee_id.serial_number', store=True)
    identification_id = fields.Char('N° Identification nationale', related='employee_id.identification_id', store=True)
    num_passport = fields.Char('N° Passeport', related='employee_id.passport_id', store=True)
    civility = fields.Selection('Civilité', related='employee_id.marital', store=True)
    gender = fields.Selection('Sexe',related='employee_id.gender', store=True)
    address = fields.Char('Adresse', store=True)
    number_children = fields.Integer('Nombre enfant(s)', related='employee_id.children', store=True)
    nb_part = fields.Float('Nombre de parts sociales', related='employee_id.nb_part', store=True)
    nationality = fields.Many2one(related='employee_id.country_id', string='Nationalité', store=True)


    @api.one
    def set_nb_part(self):
        number_of_part = 1
        number_of_part = number_of_part + self.employee_id.children * 0.5

        if self.employee_id.status_husband_wife == 'employee':
            number_of_part = number_of_part + 0.5
        if self.employee_id.status_husband_wife == 'non-employee':
            number_of_part = number_of_part + 1

        self.nb_part = number_of_part





