# -*- coding: utf-8 -*-
#################################################################################
# Author Intelligent Fiscal Systems llc
#################################################################################
{
    "name": "Automated Tax Remittance System (ATRS) - FIRS NIGERIA",
    "summary": "This module provides ATRS Integration with Odoo POS",
    "category": "Point Of Sale",
    "sequence": 1,
    "version": '15.0.1.0.0',
    "depends": ['point_of_sale', 'account'],
    "data": [
        'security/ir.model.access.csv',
        'views/models_views.xml',
        'views/account_tax_view.xml',
        'views/report_invoice.xml',
        "notify_cron.xml"
    ],
    'assets': {
        'point_of_sale.assets': [
            '/firs_report/static/src/js/qrcodejs/qrcode.js',
            '/firs_report/static/src/js/jquery.md5.js',
            '/firs_report/static/src/js/main.js',
            '/firs_report/static/src/js/TaxFreeButton.js',
            '/firs_report/static/src/js/PaymentScreen.js',
            '/firs_report/static/src/js/OrderReceipt.js',
        ],
        'web.assets_qweb': [
            'firs_report/static/src/xml/firs_report.xml',
        ],
    },
    "qweb": ['firs_report/static/src/xml/firs_report.xml'],
    "images": ['static/description/icon.png'],
    "author": "Intelligent Fiscal Systems",
    "website": "https://i-fis.com/",
    "application": True,
    "installable": True,
    "auto_install": False
}
