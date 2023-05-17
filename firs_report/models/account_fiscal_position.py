from odoo import fields, models, api


class AccountTax(models.Model):
    """
      This class extends the 'account.fiscal.position' model and adds two
      boolean fields: 'is_accural' and 'is_cash'
      """
    _inherit = 'account.fiscal.position'

    is_accural = fields.Boolean("Accural")
    is_cash = fields.Boolean("Cash")

    @api.onchange("is_accural")
    def _onchange_is_accural(self):
        """
        This function is called when the 'is_accural' field is changed, and sets
         the 'is_cash' field to False.
        """
        self.is_cash = False

    @api.onchange("is_cash")
    def _onchange_is_cash(self):
        """
        This function is called when the 'is_cash' field is changed, and sets
        the 'is_accural' field to False.
        """
        self.is_accural = False
