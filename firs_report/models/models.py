# -*- coding: utf-8 -*-
#################################################################################
# Author I-FIS llc
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError, Warning, RedirectWarning
import requests
from datetime import timedelta, datetime
import json
import md5
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.translate import _


class info_message(models.TransientModel):
	_name = "info.message"

	text =  fields.Text('Message')


class PosOrder(models.Model):
	_inherit = "pos.order"

	@api.model
	def create_from_ui(self,orders):
		res = super(PosOrder,self).create_from_ui(orders)
		if res:
			for order in self.browse(res):
				if order.invoice_id and order.sk_uid:
					order.invoice_id.sudo().write({
						'sk_sid' : order.sk_sid,
						'sk_uid' : order.sk_uid,
						'receipt_seq' : order.receipt_seq,
						'sk_uploaded': True
					})
		return res


	@api.multi
	def fetch_taxes(self):
		rec_data = self.env['firs.config'].search([])[0]
		crr = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		if crr > rec_data.active_till:
			rec_data.test_connection()

		auth = rec_data.auth_type+" "+ rec_data.auth_token
		headers = {
			"Content-Type": "application/json",
			"Authorization": auth
		}

		currency = self.pricelist_id.currency_id
		if self.amount_total!=0.0:
			data_dict = {}
			if self.amount_tax!=0.0:
				tax_rate = currency.round(float(self.amount_tax/(self.amount_total-self.amount_tax))*100.00)

				taxesline = [{
					"base_value": str(currency.round(self.amount_total-self.amount_tax)),
					"rate": str(tax_rate),
					"value": str(currency.round(self.amount_tax))
				}]
			else:
				taxesline = [{
					"base_value": str(currency.round(self.amount_total-self.amount_tax)),
					"rate": str(0.0),
					"value": str(0.0),
				}]
			st = rec_data.client_secret+rec_data.vat_number+rec_data.business_place+str(self.session_id.id)+str(self.receipt_seq)+str(self.date_order)+str(self.amount_total)
			security_code = md5.new(st).hexdigest()
			
			data_dict.update({"bill_taxes": taxesline})
			data_dict.update({"bill" : {
				"bill_datetime": str(self.date_order),
				"bill_number": str(self.receipt_seq),
				"business_device": str(self.session_id.id),
				"business_place": str(rec_data.business_place),
				"payment_type": "C",
				"security_code": str(security_code),
				"total_value": str(self.amount_total),
				'vat_number': str(rec_data.vat_number)
				}
			})
			_logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
			# raise Warning(data_dict)
			r = requests.post('https://firs-api.i-fis.com/v1/bills/report',  data=json.dumps(data_dict), headers=headers)
			if r.status_code==200:
				resp = r.json()
				if type(resp)==dict and resp.has_key('payment_code'):
					self.write({
						"sk_sid": security_code,
						"sk_uid": resp.get('payment_code'),
					})
				else:
					raise Warning(r.text)
			else:
				raise Warning(r.text)
			return True

	@api.model
	def _order_fields(self,ui_order):
		fields_return = super(PosOrder,self)._order_fields(ui_order)
		fields_return.update({
			'sk_sid':ui_order.get('sk_sid') or False,
			'receipt_seq':ui_order.get('sk_sequence') or False,
			'sk_uid':ui_order.get('sk_uid') or False
			})
		return fields_return

	sk_sid = fields.Char("SID", copy=False)
	sk_uid = fields.Char("UID", copy=False)
	receipt_seq = fields.Char("Order Sequence", copy=False)



class firsConfig(models.Model):
	_name = "firs.config"
	_rec_name = "username"

	@api.model
	def create(self, vals):	
		active_ids = self.search([])	
		if active_ids:	
			if active_ids:
				raise UserError(_("Sorry, Only one connection record is allowed!!!"))
		return super(firsConfig, self).create(vals)

	@api.model
	def get_report(self, vals):
		data_dict = {}
		rec_data = self.browse(int(vals['conf_id']))
		crr = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		if crr > rec_data.active_till:
			rec_data.test_connection()

		auth = rec_data.auth_type+" "+ rec_data.auth_token
		headers = {
			"Content-Type": "application/json",
			"Authorization": auth
		}
		taxesline = []
		if vals['taxes']:
			for line in vals['taxes']:
				taxesline.append({
					"base_value": str(vals['total_without_tax']),
					"rate": str(line['tax']['amount']),
					"value": str(line['amount'])
				})
		else:
			taxesline = [{
				"base_value": str(vals['total_without_tax']),
				"rate": str(0.0),
				"value": str(0.0),
			}]

		data_dict.update({"bill_taxes": taxesline})
		data_dict.update({"bill" : {
			"bill_datetime": str(vals['bill_datetime']),
			"bill_number": str(vals['bill_number']),
			"business_device": str(vals['device']),
			"business_place": str(rec_data.business_place),
			"payment_type": str(vals['payment_type']),
			"security_code": str(vals['security_code']),
			"total_value": str(vals['total_value']),
			'vat_number': str(rec_data.vat_number)
			}
		})
		_logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
		# raise Warning(data_dict)
		try:
			r = requests.post('https://firs-api.i-fis.com/v1/bills/report',  data=json.dumps(data_dict), headers=headers)
			if r.status_code==200:
				resp = r.json()
				if type(resp)==dict and resp.has_key('payment_code'):
					return resp.get('payment_code')
				else:
					raise Warning(r.text)
			else:
				raise Warning(r.text)
			return False
		except Exception,e:
			return False

	
	@api.model
	def fetch_taxes_cron(self):
		orders = self.env['pos.order'].search([('sk_uid','=',False),('state','!=','cancel')])
		if orders:
			for order in orders:
				order.fetch_taxes()
	
	@api.multi
	def test_connection(self):
		data = {
			'client_id': self.client_id,
			'client_secret': self.client_secret,
			'username': self.username,
			'password': self.password,
			'grant_type':'password'
		}
		r = requests.post('https://firs-api.i-fis.com/oauth2/token', data=data)
		if r.status_code == 200:
			data1 = r.json()
			message = "Connection authenticated!!!"
			self.write({
				'active_till': datetime.now()+timedelta(hours=20),
				'auth_type': data1.get('token_type'),
				'auth_token': data1.get('access_token')
			})
		else:
			message = "Invalid Credentials!!!"

		partial_id = self.env['info.message'].create({'text':message})
		return {
				'name':"Result",
				'view_mode': 'form',
				'view_id': False,
				'view_type': 'form',
				'res_model': 'info.message',
				'res_id': partial_id.id,
				'type': 'ir.actions.act_window',
				'nodestroy': True,
				'target': 'new',
				'domain': '[]',
				'context': self._context
			}


	username = fields.Char("Username")
	password = fields.Char("Password")
	client_id = fields.Char("Client ID")
	client_secret = fields.Char("Client Secret")

	vat_number = fields.Char("VAT number", help="Unique ID of the company")
	business_place = fields.Char("Business Place", help=" Short code of business place (given after registration)")
	business_device = fields.Char("Business Device", help="Serial number of POS device in a business place (given after registration)")
	active_till = fields.Datetime("Active Till")
	auth_type = fields.Char("Auth Type")
	auth_token = fields.Char("Auth Token")

	inv_session_id = fields.Integer("Business Device", help="Serial number of POS device in a business place (given after registration)")
	inv_business_place = fields.Char("Business Place", help=" Short code of business place (given after registration)")



# Update in invoice

class accountInvoice(models.Model):
	_inherit = "account.invoice"

	@api.multi
	def write(self, values):
		result = super(accountInvoice, self).write(values)
		if values.has_key('state') and values.get('state',False)=="paid":
			try:
				self.fetch_taxes()
			except Exception,e:
				pass
		return result

	@api.multi
	def fetch_taxes(self):
		if self.sk_uploaded:
			return True
		rec_data = self.env['firs.config'].search([])[0]
		if not rec_data:
			raise UserError(_("Please configure the FIRS app before you could upload the report!"))
		crr = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		if crr > rec_data.active_till:
			rec_data.test_connection()

		auth = rec_data.auth_type+" "+ rec_data.auth_token
		headers = {
			"Content-Type": "application/json",
			"Authorization": auth
		}

		currency = self.currency_id
		if self.amount_total!=0.0:
			taxesline = []
			data_dict = {}
			if self.amount_tax!=0.0:
				for tl in self.tax_line_ids:
					taxesline.append({
						"base_value": str(currency.round(tl.base)),
						"rate": str(tl.tax_id.amount),
						"value": str(currency.round(tl.amount))
					})				
			else:
				taxesline = [{
					"base_value": str(currency.round(self.amount_total-self.amount_tax)),
					"rate": str(0.0),
					"value": str(0.0),
				}]

			st = rec_data.client_secret+rec_data.vat_number+rec_data.inv_business_place+str(rec_data.inv_session_id)+str(self.id)+str(self.date_invoice)+str(self.amount_total)
			security_code = md5.new(st).hexdigest()
			
			data_dict.update({"bill_taxes": taxesline})
			data_dict.update({"bill" : {
				"bill_datetime": str(self.date_invoice),
				"bill_number": str(self.id),
				"business_device": str(rec_data.inv_session_id),
				"business_place": str(rec_data.inv_business_place),
				"payment_type": "C",
				"security_code": str(security_code),
				"total_value": str(self.amount_total),
				'vat_number': str(rec_data.vat_number)
				}
			})
			_logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
			# raise Warning(data_dict)
			r = requests.post('https://firs-api.i-fis.com/v1/bills/report',  data=json.dumps(data_dict), headers=headers)
			if r.status_code==200:
				resp = r.json()
				if type(resp)==dict and resp.has_key('payment_code'):
					self.write({
						"sk_sid": security_code,
						"sk_uid": resp.get('payment_code'),
						"receipt_seq": self.id,
						"sk_uploaded":True
					})
				else:
					raise Warning(r.text)
			else:
				raise Warning(r.text)
			return True

	sk_sid = fields.Char("SID", copy=False)
	sk_uid = fields.Char("UID", copy=False)
	receipt_seq = fields.Char("Order Sequence", copy=False)
	sk_uploaded = fields.Boolean("Uploaded", copy=False)