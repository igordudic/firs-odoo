{
  "name" : "Automated Tax Remittance System (ATRS) - FIRS NIGERIA",
  "summary" : "This module provides ATRS Integration with Odoo POS",
  "category" : "Point Of Sale",
  "sequence"  : 1,
  "version": '13.0.1.0.0',
  "depends" : ['base', 'point_of_sale', 'account'],
  "data"  : [
            'security/ir.model.access.csv',
            'data/notify_cron.xml',
            'views/firs_config_views.xml',
            'views/account_fiscal_position_view.xml',
            'views/account_move_views.xml',
            'views/account_tax_views.xml',
            'views/report_invoice.xml',
            # 'views/firs_report_templates.xml',

            # 'views/template.xml',
            # 'views/account_tax_view.xml',
            # 'views/report_invoice.xml',
            # 'views/account_fiscal_position_view.xml',
            # "notify_cron.xml"
          ],
  # "qweb"  : ['static/src/xml/firs_report.xml'],
  "images" : ['static/description/icon.png'],
  # "author" :  "Intelligent Fiscal Systems",
  # "website" :  "https://i-fis.com/",
  "application" : True,
  "installable" : True,
  "auto_install"  : False
}