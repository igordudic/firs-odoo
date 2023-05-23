from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import timedelta, datetime
import json
import logging
_logger = logging.getLogger(__name__)


class FirsConfig(models.Model):
    """
     A model representing the configuration for interacting with the FIRS API.
    """
    _name = "firs.config"
    _rec_name = "user_name"

    user_name = fields.Char(string="Username")
    password = fields.Char(string="Password")
    client_id = fields.Char(string="Client ID")
    client_secret = fields.Char(string="Client Secret")

    vat_number = fields.Char(string="VAT number", help="Unique ID of the company")
    business_place = fields.Char(string="Business Place",
                                 help=" Short code of business place (given after registration)")
    business_device = fields.Char(string="Business Device",
                                  help="Serial number of POS device in a business place "
                                       "(given after registration)")
    active_till = fields.Datetime(string="Active Till")
    auth_type = fields.Char(string="Auth Type")
    auth_token = fields.Char(string="Auth Token")

    inv_session_id = fields.Integer(string="Business Device",
                                    help="Serial number of POS device in a business place"
                                         " (given after registration)")
    inv_business_place = fields.Char(string="Business Place",
                                     help=" Short code of business place "
                                          "(given after registration)")
    firs_type = fields.Selection([('production', 'Production'), ('sandbox', 'Sandbox')],
                                 string='FIRS Type')

    def test_connection(self):
        """
        Test the connection to the API server by trying to authenticate with the
        provided credentials.

        :return: A dictionary describing the result of the test, containing
         the following keys:
                 - name: the name of the view to display the result
                 - view_mode: the mode of the view to display the result (always 'form')
                 - view_id: the ID of the view to display the result (always False)
                 - res_model: the model of the record to display the result
                   (always 'info.message')
                 - res_id: the ID of the record to display the result (created by
                   this function)
                 - type: the type of the action to perform (always 'ir.actions.act_window')
                 - nodestroy: whether to keep the current view open after opening the
                   result (always True)
                 - target: the target window to open the result in (always 'new')
                 - domain: the domain to filter the records in the current view (always '[]')
                 - context: the context to use when opening the result (same as self._context)

                 The created 'info.message' record will contain a 'text' field with the
                  message describing the
                 result of the test. If the connection is authenticated successfully, the record
                  will also have
                 the 'active_till', 'auth_type', and 'auth_token' fields set to valid values.
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.user_name,
            'password': self.password,
            'grant_type': 'password'
        }
        if self.firs_type == 'production':
            request = requests.post('https://atrs-api.firs.gov.ng/oauth2/token', data=data)
        else:
            request = requests.post('https://api-dev.i-fis.com/oauth2/token', data=data)

        if request.status_code == 200:
            data1 = request.json()
            message = "Connection authenticated!!!"
            self.write({
                'active_till': datetime.now() + timedelta(hours=20),
                'auth_type': data1.get('token_type'),
                'auth_token': data1.get('access_token')
            })
        else:
            message = "Invalid Credentials!!!" + str(request.status_code)

        partial_id = self.env['info.message'].create({'text': message})
        return {
            'name': "Result",
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'info.message',
            'res_id': partial_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': self._context
        }

    @api.model
    def create(self, vals):
        """
        Overrides the create method of the model to ensure that only one connection record
         is allowed.

        :param vals: A dictionary of field values for the new record.
        :return: A new record for the model.
        :raises: UserError if there is already an existing connection record.
        """
        active_ids = self.search([])
        if active_ids:
            if active_ids:
                raise UserError(_("Sorry, Only one connection record is allowed!!!"))
        return super(FirsConfig, self).create(vals)

    @api.model
    def get_report(self, vals):
        print("helooooooo",vals)
        data_dict = {}
        rec_data = self.browse(int(vals['conf_id']))
        crr = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        active_till = str(rec_data.active_till.strftime('%Y-%m-%d %H:%M:%S'))

        if crr > active_till:
            rec_data.test_connection()

        auth = rec_data.auth_type + " " + rec_data.auth_token
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth
        }
        bill_taxes = []
        bill_tax_gst = []
        bill_tax_other = []
        if vals['taxes']:
            tax_obj = self.env['account.tax']
            for line in vals['taxes']:
                tax_rec = tax_obj.browse(line['tax']['id'])
                if tax_rec.tax_type == 'Vat':
                    bill_taxes.append({
                        "rate": "{:.2f}".format(line['tax']['amount']),
                        "base_value": "{:.2f}".format(eval(vals['total_without_tax'])),
                        "value": "{:.2f}".format(line['amount'])
                    })
                elif tax_rec.tax_type == 'Consumption':
                    bill_tax_gst.append({
                        "rate": "{:.2f}".format(line['tax']['amount']),
                        "base_value": "{:.2f}".format(eval(vals['total_without_tax'])),
                        "value": "{:.2f}".format(line['amount'])
                    })
                else:
                    bill_tax_other.append({
                        'tax_name': tax_rec.name,
                        "rate": "{:.2f}".format(line['tax']['amount']),
                        "base_value": "{:.2f}".format(eval(vals['total_without_tax'])),
                        "value": "{:.2f}".format(line['amount'])
                    })
        # 				taxesline.append({
        # 					"base_value": str(vals['total_without_tax']),
        # 					"rate": str(line['tax']['amount']),
        # 					"value": str(line['amount'])
        # 				})
        else:
            # 			taxesline = [{
            # 				"base_value": str(vals['total_without_tax']),
            # 				"rate": str(0.0),
            # 				"value": str(0.0),
            # 			}]
            bill_taxes = [{
                "base_value": "{:.2f}".format(eval(vals['total_without_tax'])),
                "rate": "{:.2f}".format(0),
                "value": "{:.2f}".format(0),
            }]
            bill_tax_gst = [{
                "base_value": "{:.2f}".format(eval(vals['total_without_tax'])),
                "rate": "{:.2f}".format(0),
                "value": "{:.2f}".format(0),
            }]

        data_dict.update({"bill_taxes": bill_taxes, 'bill_tax_gst': bill_tax_gst})
        if bill_tax_other:
            data_dict.update({'bill_tax_other': bill_tax_other})

        data_dict.update({"bill": {
            "bill_datetime": vals['bill_datetime'],
            "bill_number": str(vals['bill_number']),
            "business_device": str(vals['device']),
            "business_place": str(rec_data.business_place),
            "payment_type": str(vals['payment_type']),
            "security_code": str(vals['security_code']),
            "total_value": vals['total_value'],
            'vat_number': str(rec_data.vat_number)
        }
        })
        if not vals['taxes']:
            data_dict['bill'].update({'tax_free': vals['total_value'], })
        _logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
        # raise Warning(data_dict)
        try:
            if rec_data.firs_type == 'production':
                r = requests.post('https://atrs-api.firs.gov.ng/v1/bills/report', data=json.dumps(data_dict),
                                  headers=headers)
            else:
                r = requests.post('https://api-dev.i-fis.com/v1/bills/report', data=json.dumps(data_dict),
                                  headers=headers)
            _logger.warning('reason: %s', r.text)
            if r.status_code == 200:
                resp = r.json()
                if type(resp) == dict and 'payment_code' in resp:
                    return resp.get('payment_code')
                else:
                    raise Warning(r.text)
            else:
                raise Warning(r.text)
            return False
        except Exception as e:
            return False

    @api.model
    def fetch_taxes_cron(self):
        orders = self.env['pos.order'].search([('sk_uid', '=', False), ('state', '!=', 'cancel')])
        if orders:
            for order in orders:
                order.fetch_taxes()


class InfoMessage(models.TransientModel):
    """Model for displaying an informational message to the user.

       This class is a transient model, meaning that it is not persisted in the database.
       It is used to display a message to the user via a pop-up window. The message can be
        any text string, and is displayed in a text box in the pop-up window.

       Attributes:
           text (Text): The text of the message to be displayed.
       """
    _name = "info.message"

    text = fields.Text(string='Message')
