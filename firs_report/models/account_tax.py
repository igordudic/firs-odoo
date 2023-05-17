from odoo import fields, models


class AccountTax(models.Model):
    """
     AccountTax represents a tax in the accounting system.

     :param models.Model: Parent model of the class.
     :param _inherit: Inherit the fields from the parent model.
     :param tax_type: Type of tax which can be either 'vat' or 'consumption'.
     :type tax_type: str
     :param string: Label of the field to be displayed in the UI.
     :type string: str
     """
    _inherit = 'account.tax'

    tax_type = fields.Selection([('vat', 'Vat'), ('consumption', 'Consumption')], string='Tax Type')
