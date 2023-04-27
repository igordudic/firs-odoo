# -*- coding: utf-8 -*-
from odoo import models,fields

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    tax_type = fields.Selection([('Vat','Vat'),('Consumption','Consumption')],string='Tax Type')