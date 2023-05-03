# -*- coding: utf-8 -*-
#################################################################################
# Author      : Techmayoreo (<https://techmayoreo.com/>)
# License     : AGPL-3
#
#################################################################################
{
    "name": "POS print kitchen order receipt KOT in browser",
    "summary": "Add option to print kitchen orders in the browser without POS box thermal printer",
    "category": "Point of Sale",
    "version": "1.0.0",
    "author": "Techmayoreo",
    "maintainer": "Anderson Martinez",
    "email": "anderson.martinez@techmayoreo.com",
    "website": "https://techmayoreo.com",
    "description": """Add option to print kitchen orders in the browser without POS box thermal printer""",
    "depends": [
        'point_of_sale',
        'pos_restaurant',
    ],
    "data": [
        'views/assets.xml',
        'views/pos_config.xml',
    ],
    'qweb': [
        'static/src/xml/kitchen_receipt.xml',
    ],
    "images": ['static/description/screenshot3.png'],
    "application": False,
    "installable": True,
    "auto_install": False,
    "price": 38,
    "currency": 'USD',
    "license":  "AGPL-3",
}