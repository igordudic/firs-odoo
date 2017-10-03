# -*- coding: utf-8 -*-
#################################################################################
# Author I-FIS llc
#################################################################################
{
  "name" : "FIRS i-FIS Integration",
  "summary" : "This module provides FIRS Integration with Odoo POS",
  "category" : "Point Of Sale",
  "sequence"  : 1,
  "depends" : ['point_of_sale'],
  "data"  : [
            'security/ir.model.access.csv',
            'views/models_views.xml',
            'views/template.xml',
            "notify_cron.xml"
          ],
  "qweb"  : ['static/src/xml/firs_report.xml'],
  "author" :  "I-FIS llc",
  "website" :  "https://i-fis.com/",
  "application" : True,
  "installable" : True,
  "auto_install"  : False
}