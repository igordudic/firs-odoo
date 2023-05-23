{
  "name": "Automated Tax Remittance System (ATRS) - FIRS NIGERIA",
  "summary": "This module provides ATRS Integration with Odoo POS",
  "category": "Point Of Sale",
  "sequence": 1,
  "version": '15.0.1.0.0',
  "depends": ['base', 'point_of_sale', 'account'],
  "data": [
            'security/ir.model.access.csv',
            'data/notify_cron.xml',
            'views/firs_config_views.xml',
            'views/account_fiscal_position_view.xml',
            'views/account_move_views.xml',
            'views/account_tax_views.xml',
            'views/report_invoice.xml',
            'views/pos_order_views.xml',
          ],
  'assets': {
        'web.assets_qweb': [
            'firs_report/static/src/xml/firs_report.xml',
        ],
        'web.assets_backend': [
            "/firs_report/static/src/js/jquery.md5.js",
            "/firs_report/static/src/js/main.js",
            "/firs_report/static/src/js/TaxFreeButton.js",
            "/firs_report/static/src/js/PaymentScreen.js",
            "/firs_report/static/src/js/OrderReceipt.js"]},
  "images": ['static/description/icon.png'],
  # "author" :  "Intelligent Fiscal Systems",
  # "website" :  "https://i-fis.com/",
  "application": True,
  "installable": True,
  "auto_install": False
}
