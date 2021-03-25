#-*- coding:utf-8 -*-
import time
from datetime import datetime, date, time as t
from odoo import models, fields, api, _


class HrContractBonus(models.Model):
    _inherit = 'hr.contract'

    nb_days = fields.Float(string="Anciennete", compute="_get_duration")
    convention_id = fields.Many2one('line.optesis.convention', 'Catégorie')
    last_date = fields.Date("Dernière date")
    motif = fields.Selection([('demission', 'Démission'), ('fin', 'Fin de contrat'), ('retraite', 'Retraite'),
                              ('licenciement', 'Licenciement'), ('deces', 'Décès'),
                              ('depart_nogicie', 'Départ négocié')], string='Motif de sortie')
    dateAnciennete = fields.Date("Date d'ancienneté", default=lambda self: fields.Date.to_string(date.today()))
    typeContract = fields.Selection([('cdi', 'CDI'), ('cdd', 'CDD'), ('others', 'Autres')], string="Type de contract")

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
