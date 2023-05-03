from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    print_kot_in_browser = fields.Boolean('Print kot in browser')
