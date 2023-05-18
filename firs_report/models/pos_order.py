from odoo import api, fields, models
from odoo.exceptions import Warning
import requests
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json
import pytz
import time
import hashlib
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    firs_bill_number = fields.Char('FIRS Bill Number')

    def _create_invoice(self, move_vals):
        print(move_vals,"vals")
        move_vals.update({
            'sk_sid': self.sk_sid,
            'sk_uid': self.sk_uid,
            'receipt_seq': self.receipt_seq,
        })
        return super(PosOrder, self)._create_invoice(move_vals)

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(PosOrder, self).create_from_ui(orders, draft)
        if res:
            print("res")
            for r in res:
                order = self.browse(r.get('id'))
                print(order,"ooooooo")
                print(order.sk_uid,"oool")
                print(order.sk_sid,"oool")
                if order.account_move and order.sk_uid:
                    print(order.sk_sid)
                    print(order.sk_uid)
                    order.account_move.sudo().write({
                        'sk_sid': order.sk_sid,
                        'sk_uid': order.sk_uid,
                        'receipt_seq': order.receipt_seq,
                        'sk_uploaded': True
                    })
        return res

    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        self.account_move.fetch_taxes()
        return res

    def convert_datetime_timezone(self, order_date):
        local = pytz.timezone("UTC")
        local_dt = local.localize(order_date, is_dst=None)

        to_zone = pytz.timezone("Africa/Lagos")
        wat_datetime = local_dt.astimezone(to_zone)

        wat_datetime = wat_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        wat_datetime = datetime.strptime(wat_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
        return wat_datetime.isoformat()

    # 	@api.multi
    def fetch_without_taxes(self):
        rec_data = self.env['firs.config'].search([])[0]
        crr = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        active_till = str(rec_data.active_till.strftime('%Y-%m-%d %H:%M:%S'))
        if crr > active_till:
            rec_data.test_connection()

        auth = rec_data.auth_type + " " + rec_data.auth_token
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth
        }
        if self.amount_total != 0.0:
            data_dict = {}
            date_order = self.convert_datetime_timezone(self.date_order)
            # date_order = self.date_order.strftime("%Y-%m-%d %H:%M:%S")
            # date_order = datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)
            # date_order = date_order.isoformat()
            amount_total = self.amount_total - self.amount_tax
            amount_total = "{:0.2f}".format(amount_total)
            timestamp = int(time.time())
            bill_number = str(timestamp)
            self.write({'firs_bill_number': bill_number})
            if type(bill_number) != str:
                bill_number = ''.join(list(bill_number))
            st = rec_data.client_secret + rec_data.vat_number + rec_data.business_place + str(self.session_id.id) + str(
                bill_number) + str(date_order) + str(amount_total)
            # 			security_code = md5.new(st).hexdigest()
            security_code = hashlib.md5(st.encode(encoding='utf_8', errors='strict')).hexdigest()

            data_dict.update({"bill": {
                "bill_datetime": date_order,
                "bill_number": bill_number,
                "business_device": str(self.session_id.id),
                "business_place": str(rec_data.business_place),
                "payment_type": "C",
                "security_code": str(security_code),
                "total_value": amount_total,
                'vat_number': str(rec_data.vat_number),
                'tax_free': amount_total,
            }
            })

            if rec_data.firs_type == 'production':
                r = requests.post('https://atrs-api.firs.gov.ng/v1/bills/report', data=json.dumps(data_dict),
                                  headers=headers)
            else:
                r = requests.post('https://api-dev.i-fis.com/v1/bills/report', data=json.dumps(data_dict),
                                  headers=headers)
            if r.status_code == 200:
                resp = r.json()
                if type(resp) == dict and 'payment_code' in resp:
                    self.write({
                        "sk_sid": security_code,
                        "sk_uid": resp.get('payment_code'),
                    })
                else:
                    raise Warning(r.text)
            else:
                raise Warning(r.text)
            return True

    def fetch_taxes(self):
        rec_data = self.env['firs.config'].search([])[0]
        crr = datetime.now()
        if crr > rec_data.active_till:
            rec_data.test_connection()

        auth = rec_data.auth_type + " " + rec_data.auth_token
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth
        }

        currency = self.session_id.currency_id or self.pricelist_id.currency_id
        if self.amount_total != 0.0:
            data_dict = {}
            bill_taxes = []
            bill_tax_gst = []
            bill_tax_other = []
            if self.amount_tax != 0.0:
                tax_grouped = {}
                for line in self.lines:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(
                        line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty,
                        product=line.product_id, partner=line.order_id.partner_id or False)
                    income_account = False
                    if line.product_id.property_account_income_id.id:
                        income_account = line.product_id.property_account_income_id.id
                    elif line.product_id.categ_id.property_account_income_categ_id.id:
                        income_account = line.product_id.categ_id.property_account_income_categ_id.id
                    for tax in line_taxes['taxes']:
                        val = {
                            'account_id': tax['account_id'] or income_account,
                            'tax_id': tax['id'],
                            'amount': tax['amount'],
                            'base': tax['base'],
                        }
                        if tax['account_id']:
                            key = str(tax['id']) + '-' + str(tax['account_id'])
                        elif income_account:
                            key = str(tax['id']) + '-' + str(income_account)
                        else:
                            key = str(tax['id'])
                        if key not in tax_grouped:
                            tax_grouped[key] = val
                        else:
                            tax_grouped[key]['amount'] += val['amount']
                            tax_grouped[key]['base'] += val['base']
                # return tax_grouped
                tax_obj = self.env['account.tax']
                for k, tax_info in tax_grouped.items():
                    tax_rec = tax_obj.browse(tax_info['tax_id'])
                    if tax_rec.tax_type == 'Vat':
                        bill_taxes.append({
                            "rate": "{:.2f}".format(tax_rec.amount),
                            "base_value": "{:.2f}".format(currency.round(tax_info['base'])),
                            "value": "{:.2f}".format(currency.round(tax_info['amount']))
                        })
                    elif tax_rec.tax_type == 'Consumption':
                        bill_tax_gst.append({
                            "rate": "{:.2f}".format(tax_rec.amount),
                            "base_value": "{:.2f}".format(currency.round(tax_info['base'])),
                            "value": "{:.2f}".format(currency.round(tax_info['amount']))
                        })
                    else:
                        bill_tax_other.append({
                            'tax_name': tax_rec.name,
                            "rate": "{:.2f}".format(tax_rec.amount),
                            "base_value": "{:.2f}".format(currency.round(tax_info['base'])),
                            "value": "{:.2f}".format(currency.round(tax_info['amount']))
                        })
            # 				tax_rate = currency.round(float(self.amount_tax/(self.amount_total-self.amount_tax))*100.00)
            # 				taxesline = [{
            # 					"base_value": str(currency.round(self.amount_total-self.amount_tax)),
            # 					"rate": str(tax_rate),
            # 					"value": str(currency.round(self.amount_tax))
            # 				}]
            else:
                # 				taxesline = [{
                # 					"base_value": str(currency.round(self.amount_total-self.amount_tax)),
                # 					"rate": str(0.0),
                # 					"value": str(0.0),
                # 				}]
                bill_taxes = [{
                    "base_value": "{:.2f}".format(currency.round(self.amount_total - self.amount_tax)),
                    "rate": "{:.2f}".format(0),
                    "value": "{:.2f}".format(0),
                }]
                bill_tax_gst = [{
                    "base_value": "{:.2f}".format(currency.round(self.amount_total - self.amount_tax)),
                    "rate": "{:.2f}".format(0),
                    "value": "{:.2f}".format(0),
                }]
            date_order = self.convert_datetime_timezone(self.date_order)
            # date_order = self.date_order.strftime("%Y-%m-%d %H:%M:%S")
            # date_order = datetime.strptime(date_order,DEFAULT_SERVER_DATETIME_FORMAT)
            # date_order = date_order.isoformat()
            # 			date_order = datetime.strptime(self.date_order,"%Y-%m-%d %H:%M:%S").isoformat()
            amount_total = "{:0.2f}".format(self.amount_total)
            timestamp = int(time.time())
            bill_number = str(timestamp)
            self.write({'firs_bill_number': bill_number})
            if type(bill_number) != str:
                bill_number = ''.join(list(bill_number))
            st = rec_data.client_secret + rec_data.vat_number + rec_data.business_place + str(self.session_id.id) + str(
                bill_number) + str(date_order) + str(amount_total)
            # 			security_code = md5.new(st).hexdigest()
            security_code = hashlib.md5(st.encode(encoding='utf_8', errors='strict')).hexdigest()

            data_dict.update({"bill_taxes": bill_taxes, 'bill_tax_gst': bill_tax_gst})
            if bill_tax_other:
                data_dict.update({'bill_tax_other': bill_tax_other})
            data_dict.update({"bill": {
                "bill_datetime": date_order,
                "bill_number": bill_number,
                "business_device": str(self.session_id.id),
                "business_place": str(rec_data.business_place),
                "payment_type": "C",
                "security_code": str(security_code),
                "total_value": amount_total,
                'vat_number': str(rec_data.vat_number)
            }
            })
            if self.amount_tax == 0.0:
                data_dict['bill'].update({'tax_free': amount_total, })
            _logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
            # raise Warning(data_dict)
            if rec_data.firs_type == 'production':
                r = requests.post('https://atrs-api.firs.gov.ng/v1/bills/report', data=json.dumps(data_dict),
                                  headers=headers)
            else:
                r = requests.post('https://api-dev.i-fis.com/v1/bills/report', data=json.dumps(data_dict),
                                  headers=headers)
            if r.status_code == 200:
                resp = r.json()
                if type(resp) == dict and 'payment_code' in resp:
                    self.write({
                        "sk_sid": security_code,
                        "sk_uid": resp.get('payment_code'),
                    })
                    if self.account_move:
                        self.account_move.sudo().write({
                            'sk_sid': self.sk_sid,
                            'sk_uid': self.sk_uid,
                            'receipt_seq': self.receipt_seq,
                            'sk_uploaded': True
                        })
                else:
                    raise Warning(r.text)
            else:
                raise Warning(r.text)
            return True

    @api.model
    def _order_fields(self, ui_order):
        fields_return = super(PosOrder, self)._order_fields(ui_order)
        fields_return.update({
            'sk_sid': ui_order.get('sk_sid') or False,
            'receipt_seq': ui_order.get('sk_sequence') or False,
            'sk_uid': ui_order.get('sk_uid') or False
        })
        return fields_return

    # 	@api.multi
    def upload_order_bills(self):
        for record in self:
            if not record.sk_uid:
                record.fetch_taxes()

    @api.depends('sk_uid')
    def _compute_firs_order_status(self):
        for order in self:
            if order.sk_uid:
                order.firs_status = 'Uploaded'
            else:
                order.firs_status = 'Not uploaded'

    sk_sid = fields.Char("SID", copy=False)
    sk_uid = fields.Char("UID", copy=False)
    receipt_seq = fields.Char("Order Sequence", copy=False)
    firs_status = fields.Selection([('Uploaded', 'Uploaded'), ('Not uploaded', 'Not uploaded')],
                                   compute='_compute_firs_order_status', string='FIRS Status', store=True)
