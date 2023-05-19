from odoo import models


class AccountPayment(models.Model):
    """
    This class extends the 'account.payment' model to add custom functionality for posting payments.
    """

    _inherit = "account.payment"

    def post(self):
        """
        Post the payment and perform additional custom logic.

        :return: A dictionary containing the result of the original 'post' method.
        :rtype: dict
        """
        res = super(AccountPayment, self).post()
        if self.invoice_ids.fiscal_position_id.is_cash:
            self.invoice_ids.fetch_taxes()
        return res