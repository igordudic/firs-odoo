from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        if self.line_ids.move_id.fiscal_position_id.is_cash:
            self.line_ids.move_id.fetch_taxes()
        return res
