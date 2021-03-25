#-*- coding:utf-8 -*-

from odoo import api, models
import time
from datetime import datetime
import logging
log = logging.getLogger('Log')


class payslip_report_payroll(models.AbstractModel):
    _name = "report.nrt_payroll.report_payroll_neurotech"

    def get_sal_net(self, obj):
        vals = [obj[id].total for id in range(len(obj)) if obj[id].category_id.code == 'NET']
        for value in vals:
            return value
        return 0

    def get_ir(self, obj):
        vals = [obj[id].total for id in range(len(obj)) if obj[id].code == 'C2170']
        for value in vals:
            return value
        return 0

    def get_charge_salariale(self, obj):
        vals = [obj[id].total for id in range(len(obj)) if obj[id].code == 'C3005']
        for value in vals:
            return value
        return 0

    def get_payslip_imposable(self, lines):

        res = []
        for obj in lines:
            line = []
            if obj.category_id.code in ['INDM','BASE']:
                if obj.appears_on_payslip ==True and obj.amount !=0:

                    line.append(obj.code)
                    line.append(obj.name)
                    line.append(obj.quantity)
                    line.append(obj.amount)
                    line.append(obj.rate)
                    line.append(obj.total)
                    res.append(line)
        return res

    def get_payslip_retenu(self, lines):

        res = []

        for obj in lines:
            line = []
            if obj.category_id.code == 'DED'  and obj.code not in ['C2170','C2050']:
                if obj.appears_on_payslip == True and obj.amount != 0:
                    line.append(obj.code)
                    line.append(obj.name)
                    line.append(obj.quantity)
                    line.append(obj.amount)
                    line.append(obj.rate)
                    line.append(obj.total)
                    res.append(line)
        return res


    def get_payslip_cotisation_patronal(self, lines):

        res = []
        for obj in lines:
            line = []
            if obj.category_id.code =='COMP':
                if obj.appears_on_payslip ==True and obj.amount !=0:

                    line.append(obj.code)
                    line.append(obj.name)
                    line.append(obj.quantity)
                    line.append(obj.amount)
                    line.append(obj.rate)
                    line.append('')
                    line.append('')
                    line.append(obj.total)
                    res.append(line)
        return res

    def get_payslip_cotisation_salary(self, lines):

        res = []
        for obj in lines:
            line = []
            if obj.category_id.code in ['SALC','TRIMF','DED']:
                if obj.appears_on_payslip ==True and obj.code not in ['C2140','C2180','C2172','C2700','C2174','C2800','CP','NL','PT','TK','PL','AV','PRVHL'] and obj.amount !=0 :

                    line.append(obj.code)
                    line.append(obj.name)
                    line.append(obj.quantity)
                    line.append(obj.amount)
                    line.append(obj.rate)
                    line.append('')
                    line.append(obj.total)
                    res.append(line)
        return res

    def get_payslip_non_imposable(self, lines):
        res = []
        for obj in lines:
            line = []
            if obj.category_id.code =='NOIMP':
                if obj.appears_on_payslip ==True and obj.amount !=0 :

                    line.append(obj.code)
                    line.append(obj.name)
                    line.append(obj.quantity)
                    line.append(obj.amount)
                    line.append(obj.rate)
                    line.append(obj.total)
                    res.append(line)
        return res

    def get_payslip_lines(self, lines):

        payslip_line = self.pool.get('hr.payslip.line')
        res = []
        ids = []
        for id in range(len(lines)):
            if lines[id].appears_on_payslip is True and lines[id].amount != 0:
                ids.append(lines[id].id)
        nb_dynamic_lines = len(ids)
        log.error('Lines :'+str(nb_dynamic_lines))
        if nb_dynamic_lines >= 38:
            self._fill_empty_lines(res, 0, 0)
        elif 21<= nb_dynamic_lines <=38:
            self._fill_empty_lines(res, 0, 4)
        elif nb_dynamic_lines <25:

            self._fill_empty_lines(res, 0, 7)
        return res

    def _fill_empty_lines(self, res, nb_lines_dynamic, nb_lines_static):
        col = ['', '', '', '', '' , '']

        line_empty = nb_lines_static - nb_lines_dynamic
        line_new = range(line_empty)

        if line_empty >= 0:
            for i in line_new:
                res.append(col)


    def get_payment_mode(self, selection):

        payment_modes =self.env['hr.payslip'].fields_get(["typePaiement"])["typePaiement"]["selection"]
        for mode in payment_modes:
            if mode[0] == selection:
                return mode[1]

    def get_marital(self, selection):

        payment_modes = self.env['hr.employee'].fields_get(["marital"])["marital"]["selection"]
        for mode in payment_modes:
            if mode[0] == selection:
                return mode[1]

    def get_marital(self, selection):

        marital_modes = self.env['hr.employee'].fields_get(["marital"])["marital"]["selection"]
        for mode in marital_modes:
            if mode[0] == selection:
                return mode[1]

    def get_contract_type(self, selection):

        contract_modes = self.env['hr.employee'].fields_get(["contrat_type"])["contrat_type"]["selection"]
        for mode in contract_modes:
            if mode[0] == selection:
                return mode[1]

    def _get_total_brut_year(self, payslip):

        self.payslips = self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id),
                                                           ('state', '!=', 'cancel'),
                                                           ('date_from', '>=', datetime(
                                                               datetime.strptime(str(payslip.date_from),
                                                                                 "%Y-%m-%d").date().year,
                                                               1, 1)),
                                                           ('date_to', '<=',
                                                            datetime.strptime(str(payslip.date_to), "%Y-%m-%d"))
                                                           ])

        total_brut_year = 0
        for line in self.payslips:
            total_brut_year +=line.total_brut

        return total_brut_year

    def _get_brut_imp_year(self,payslip):
        total_brut_imp = 0
        for line in self.payslips:
            total_brut_imp +=line.total_imposable

        return total_brut_imp

    def _get_charge_patronale_year(self,payslip):
        total_charge_patronale = 0
        for line in self.payslips:
            total_charge_patronale +=line.total_charge_patronale

        return total_charge_patronale

    def _get_charge_salariale_year(self,lines):
        total_charge_salariale = 0
        for line in self.payslips:
            for l in self.env['hr.payslip.line'].search([('slip_id','=',line.id),('code','in',['C3005','C2170'])]):
                total_charge_salariale +=l.amount

        return total_charge_salariale

    def _get_work_time_year(self,payslip):
        total_work_year = 0
        for line in self.payslips:
            total_work_year += (173.33 / 30) * line.worked_days_line_ids[0].number_of_days

        return total_work_year

    def get_number_work_days(self, nb_work):
        return (173.33 / 30) * nb_work

    def get_period_payslip(self,payslip):
        return datetime.strftime(payslip.date_from, '%d/%m/%Y')


    @api.model
    def _get_report_values(self, docids, data=None):
        advice = self.env['hr.payslip'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'data': data,
            'docs': advice,
            'time': time,
            'get_contract_type': self.get_contract_type,
            'get_marital': self.get_marital,
            'get_payment_mode': self.get_payment_mode,
            'get_payslip_imposable':self.get_payslip_imposable,
            'get_payslip_cotisation_patronal':self.get_payslip_cotisation_patronal,
            'get_payslip_cotisation_salary':self.get_payslip_cotisation_salary,
            'get_payslip_non_imposable':self.get_payslip_non_imposable,
            'get_sal_net': self.get_sal_net,
            'get_ir':self.get_ir,
            'get_charge_salariale':self.get_charge_salariale,
            'get_payslip_retenu':self.get_payslip_retenu,
            'get_payslip_lines':self.get_payslip_lines,
            'get_total_brut_year':self._get_total_brut_year,
            'get_brut_imp_year':self._get_brut_imp_year,
            'get_charge_patronale_year':self._get_charge_patronale_year,
            'get_charge_salariale_year':self._get_charge_salariale_year,
            'get_work_time_year':self._get_work_time_year,
            'get_number_work_days':self.get_number_work_days,
            'get_marital': self.get_marital,
            'get_period_payslip':self.get_period_payslip
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
