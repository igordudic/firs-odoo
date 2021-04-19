# -*- coding: utf-8 -*-
#################################################################################
# Author I-FIS llc
#################################################################################
{
  "name" : "FIRS i-FIS Integration",
  "summary" : "This module provides FIRS Integration with Odoo POS",
  "category" : "Point Of Sale",
  "sequence"  : 1,
  "version": '14.0.0.1',
  "depends" : ['point_of_sale','account'],
  "data"  : [
            'security/ir.model.access.csv',
            'views/models_views.xml',
            'views/template.xml',
            'views/account_tax_view.xml',
            'views/report_invoice.xml',
            "notify_cron.xml"
          ],
  "qweb"  : ['static/src/xml/firs_report.xml'],
  "images" : ['static/description/Banner.png'],
  "author" :  "I-FIS LLC | i-fis.com",
  "website" :  "https://i-fis.com/",
  "application" : True,
  "installable" : True,
  "auto_install"  : False
}
