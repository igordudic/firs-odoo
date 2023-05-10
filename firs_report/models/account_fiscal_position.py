from odoo import fields, models, api


class AccountTax(models.Model):
    _inherit = 'account.fiscal.position'

    is_accural = fields.Boolean("Accural")
    is_cash = fields.Boolean("Cash")

    @api.onchange("is_accural")
    def _onchange_is_accural(self):
        self.is_cash = False

    @api.onchange("is_cash")
    def _onchange_is_cash(self):
        self.is_accural = False
