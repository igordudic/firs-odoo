# -*- coding: utf-8 -*-
#################################################################################
# Author I-FIS llc
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
import requests
from datetime import datetime
import json
import time
import hashlib
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    """Model for representing an invoice in the Odoo accounting system.

      This class extends the functionality of the base `account.move` class to include fields
      specific to invoices,such as payment type and fiscal position accruals. Fetch tax information
      for the invoice and upload it to the external system via an API.

       Attributes:
            sk_sid (Char): A unique identifier for the invoice.
            sk_uid (Char): A unique identifier for the user who created the invoice.
            receipt_seq (Char): The order sequence of the invoice.
            sk_uploaded (Boolean): Whether the invoice has been uploaded.
            accural_payment_type (Selection): The payment type of the invoice, including bank
             transfer, credit card,debit card, post payment, and other.
            is_fiscal_position_accural (Boolean): Whether the fiscal position of the invoice
             should be taken into account for the accruals.
            firs_inv_bill_number (Char): The bill number of the invoice.
    """
    _inherit = "account.move"

    sk_sid = fields.Char("SID", copy=False)
    sk_uid = fields.Char("UID", copy=False)
    receipt_seq = fields.Char("Order Sequence", copy=False)
    sk_uploaded = fields.Boolean("Uploaded", copy=False)
    accural_payment_type = fields.Selection([('T', 'Bank Transfer'),
                                             ('K', 'Credit Card'),
                                             ('D', 'Debit Card'),
                                             ('P', 'Post Payment'),
                                             ('O', 'Other')],
                                            string='Payment Type',
                                            default='O')
    is_fiscal_position_accural = fields.Boolean(string="Fiscal position accural")
    firs_inv_bill_number = fields.Char('FIRS INV Bill Number')

    @api.model
    def get_office_no_device_no_bill_no(self, invoice):
        """
        Get the office number, device number, and bill number for the
         given invoice.
        :param invoice: The invoice for which to retrieve the office number,
         device number, and bill number.
        :type invoice: recordset of the account.move model
        :return: A string representing the office number, device number,
         and bill number for the given invoice.
        :rtype: str
        """
        conf_info = self.env['firs.config'].search([], limit=1)
        report_name = ''
        if conf_info.inv_business_place:
            report_name += conf_info.inv_business_place + ' / '
        if conf_info.inv_session_id:
            report_name += str(conf_info.inv_session_id) + ' / '
        report_name += str(invoice.id)
        return report_name

    @api.model
    def get_firs_report_url(self, invoice):
        """
        Generate the URL for the FIRS report associated with the given invoice.

        If the invoice has a `sk_uid` field, the URL will be for payment code
         verification.
        If the invoice has a `sk_sid` field, the URL will be for security
        code verification.
        If the invoice has neither field, the URL will be the base FIRS website.

        :param invoice: The invoice for which to generate the FIRS report URL.
        :type invoice: recordset of the account.move model

        :raises UserError: If the FIRS app is not configured and the invoice has
         an `sk_sid` field.

        :return: A string representing the URL for the FIRS report associated with
         the given invoice.
        :rtype: str
        """
        if invoice.sk_uid:
            url = "https://ecitizen.firs.gov.ng/en/payment-code-verify/" + invoice.sk_uid
        elif invoice.sk_sid:
            conf_info = self.env['firs.config'].search([], limit=1)
            if not conf_info:
                raise UserError(_("Please configure the FIRS app before "
                                  "you could upload the report!"))

            date_invoice = invoice.invoice_date.strftime("%Y-%m-%d")
            date_invoice = datetime.strptime(date_invoice, "%Y-%m-%d")
            date_invoice = date_invoice.isoformat()
            amount_total = f"{invoice.amount_total:.2f}"
            url = "https://ecitizen.firs.gov.ng/en/security-code-verify/"
            url += conf_info.vat_number + "~" + str(invoice.id) + "~" + \
                   conf_info.inv_business_place + "~" + str(
                conf_info.inv_session_id) + "~" + date_invoice + "~" + \
                   str(amount_total) + "~" + str(invoice.sk_sid)
        else:
            url = "https://ecitizen.firs.gov.ng"
        return url

    def action_post(self):
        """Override of the default method to ensure that a fiscal position is
         selected before posting an invoice.

        If a fiscal position has not been selected, a UserError is raised.
        If the selected fiscal position is an accrual position, the taxes on
        the invoice are fetched.

        :return: The result of the super method.
        :rtype: dict
        """
        res = super(AccountInvoice, self).action_post()
        if not self.fiscal_position_id:
            raise UserError("Please select fiscal position.")
        if self.fiscal_position_id.is_accural:
            self.fetch_taxes()
        return res

    def action_tax_free(self):
        """Remove taxes from all invoice lines that belong to a required tax group,
         and delete the associated journal items.

        For each invoice line, we collect the tax groups of its tax lines,
         and store them in a list.
        We then filter out the tax groups that are None or False.
        The resulting list contains the required tax group IDs.

        We then find all journal items that are associated with a tax group in the
         required list, and delete them.
        Finally, we remove all taxes from the invoice lines that belong to the required
         tax groups.

        :return: None
        """
        required_tax_group = []
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                required_tax_group.append(tax.mapped('tax_group_id').id)
        required_account = [i for i in required_tax_group if i]
        line_to_remove = self.line_ids.filtered(lambda x: x.tax_group_id.id in required_account)
        for line in self.invoice_line_ids:
            line.write({'tax_ids': [(5, 0, 0)]})
        line_to_remove.sudo().with_context(check_move_validity=False).unlink()

    def fetch_taxes(self):
        """Fetch tax information for the invoice and upload it to the external
        system via an API.
        Returns: True if the tax information was successfully uploaded."""
        if self.sk_uploaded:
            return True
        rec_data = self.env['firs.config'].search([], limit=1)
        if not rec_data:
            raise UserError(_("Please configure the FIRS app before you could upload the report!"))
        active_till = rec_data.active_till.strftime('%Y-%m-%d %H:%M:%S')
        if datetime.now() > datetime.strptime(active_till, '%Y-%m-%d %H:%M:%S'):
            rec_data.test_connection()
        auth = rec_data.auth_type + " " + rec_data.auth_token
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth
        }
        currency = self.currency_id
        if self.amount_total != 0.0:
            bill_taxes = []
            bill_tax_gst = []
            bill_tax_other = []
            data_dict = {}
            if self.amount_tax != 0.0:
                for line in self.line_ids:
                    if line.tax_line_id:
                        tax_type = line.tax_line_id.tax_type
                        bill_tax = {
                            "rate": f"{line.tax_line_id.amount:.2f}",
                            "base_value": f"{currency.round(line.tax_base_amount):.2f}",
                            "value": f"{currency.round(line.price_subtotal):.2f}"
                        }
                        if tax_type == 'vat':
                            bill_taxes.append(bill_tax)
                        elif tax_type == 'consumption':
                            bill_tax_gst.append(bill_tax)
                        else:
                            bill_tax_other.append({
                                'tax_name': line.tax_line_id.name,
                                **bill_tax
                            })
            else:
                base_value = f"{currency.round(self.amount_total - self.amount_tax):.2f}"
                bill_taxes = [{
                    "base_value": base_value,
                    "rate": f"{0:.2f}",
                    "value": f"{0:.2f}",
                }]
                bill_tax_gst = [bill_taxes[0]]

            amount_total = f"{self.amount_total:0.2f}"
            date_invoice = self.invoice_date.strftime("%Y-%m-%d")
            date_invoice = datetime.strptime(date_invoice, "%Y-%m-%d")
            date_invoice = date_invoice.isoformat()
            timestamp = int(time.time())
            bill_num = str(timestamp) + str('0') + str(self.id)
            self.write({'firs_inv_bill_number': bill_num})
            code_security = rec_data.client_secret + rec_data.vat_number + \
                            rec_data.inv_business_place + str(rec_data.inv_session_id) \
                            + str(bill_num) + str(date_invoice) \
                            + str(amount_total)
            security_code = hashlib.md5(code_security.encode(
                encoding='utf_8', errors='strict')).hexdigest()
            data_dict.update({"bill_taxes": bill_taxes, 'bill_tax_gst': bill_tax_gst})
            if bill_tax_other:
                data_dict.update({'bill_tax_other': bill_tax_other})
            data_dict.update({"bill": {
                "bill_datetime": date_invoice,
                "bill_number": bill_num,
                "business_device": str(rec_data.inv_session_id),
                "business_place": str(rec_data.inv_business_place),
                "security_code": str(security_code),
                "total_value": amount_total,
                'vat_number': str(rec_data.vat_number),
                "client_vat_number": self.partner_id.vat,
                "tax_free": f"{currency.round(self.amount_untaxed):.2f}"
            }})

            if self.is_fiscal_position_accural:
                data_dict["bill"]["payment_type"] = str(self.accural_payment_type)
            else:
                data_dict["bill"]["payment_type"] = "C"
            if self.amount_tax == 0.0:
                data_dict['bill'].update({'tax_free': amount_total})
            _logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
            url = 'https://atrs-api.firs.gov.ng/v1/bills/report' if \
                rec_data.firs_type == 'production' else 'https://api-dev.i-fis.com/v1/bills/report'
            request = requests.post(url, data=json.dumps(data_dict), headers=headers, timeout=10)
            if request.status_code == 200:
                resp = request.json()
                if isinstance(resp, dict) and 'payment_code' in resp:
                    self.write({
                        "sk_sid": security_code,
                        "sk_uid": resp.get('payment_code'),
                        "receipt_seq": self.id,
                        "sk_uploaded": True
                    })
                else:
                    raise Warning(request.text)
            else:
                raise Warning(request.text)

    def cancel_invoice_firs(self):
        """
          This function cancels an invoice in the system and sends a report to the FIRS API.
           It first checks that the FIRS app has been
          properly configured. If not, it raises a UserError with the message "Please configure
           the FIRS app before you could upload the report!".
          The function then retrieves authentication details and currency information from the
          configuration data. It constructs a JSON payload
          based on the invoice data and sends it to the appropriate FIRS API endpoint based on the
           environment (production or development).

          Raises:
              UserError: If the FIRS app has not been properly configured.
              Warning: If there is an issue sending the request to the FIRS API, or if the response
              contains an error message.

          Returns:
              None
          """
        self.button_draft()
        self.button_cancel()
        rec_data = self.env['firs.config'].search([], limit=1)
        if not rec_data:
            raise UserError(_("Please configure the FIRS app before you could upload the report!"))
        active_till = rec_data.active_till.strftime('%Y-%m-%d %H:%M:%S')
        if datetime.now() > datetime.strptime(active_till, '%Y-%m-%d %H:%M:%S'):
            rec_data.test_connection()
        auth = rec_data.auth_type + " " + rec_data.auth_token
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth
        }
        currency = self.currency_id
        if self.amount_total != 0.0:
            bill_taxes = []
            bill_tax_gst = []
            bill_tax_other = []
            data_dict = {}
            if self.amount_tax != 0.0:
                for line in self.line_ids:
                    if line.tax_line_id:
                        tax_type = line.tax_line_id.tax_type
                        bill_tax = {
                            "rate": f"{line.tax_line_id.amount:.2f}",
                            "base_value": f"{currency.round(-abs(line.tax_base_amount)):.2f}",
                            "value": f"{currency.round(-abs(line.price_subtotal)):.2f}"
                        }
                        if tax_type == 'vat':
                            bill_taxes.append(bill_tax)
                        elif tax_type == 'consumption':
                            bill_tax_gst.append(bill_tax)
                        else:
                            bill_tax_other.append({
                                'tax_name': line.tax_line_id.name,
                                **bill_tax
                            })
            else:
                base_value = f"{currency.round(-abs(self.amount_total - self.amount_tax)):.2f}"
                bill_taxes = [{
                    "base_value": base_value,
                    "rate": f"{0:.2f}",
                    "value": f"{0:.2f}",
                }]
                bill_tax_gst = [bill_taxes[0]]

            amount_total = f"{-abs(self.amount_total):0.2f}"
            date_invoice = self.invoice_date.strftime("%Y-%m-%d")
            date_invoice = datetime.strptime(date_invoice, "%Y-%m-%d")
            date_invoice = date_invoice.isoformat()
            timestamp = int(time.time())
            bill_num = str(timestamp) + str('0') + str(self.id)
            self.write({'firs_inv_bill_number': bill_num})
            code_security = rec_data.client_secret + rec_data.vat_number + \
                            rec_data.inv_business_place + str(rec_data.inv_session_id) \
                            + str(bill_num) + str(date_invoice) \
                            + str(amount_total)
            security_code = hashlib.md5(code_security.encode(
                encoding='utf_8', errors='strict')).hexdigest()
            data_dict.update({"bill_taxes": bill_taxes, 'bill_tax_gst': bill_tax_gst})
            if bill_tax_other:
                data_dict.update({'bill_tax_other': bill_tax_other})
            data_dict.update({"bill": {
                "bill_datetime": date_invoice,
                "bill_number": bill_num,
                "business_device": str(rec_data.inv_session_id),
                "business_place": str(rec_data.inv_business_place),
                "security_code": str(security_code),
                "total_value": amount_total,
                'vat_number': str(rec_data.vat_number),
                "client_vat_number": self.partner_id.vat,
                "tax_free": f"{currency.round(-abs(self.amount_untaxed)):.2f}"
            }})

            if self.is_fiscal_position_accural:
                data_dict["bill"]["payment_type"] = str(self.accural_payment_type)
            else:
                data_dict["bill"]["payment_type"] = "C"
            if self.amount_tax == 0.0:
                data_dict['bill'].update({'tax_free': amount_total})
            _logger.warning('XXXXXXXXXXXXXX: %s', data_dict)
            url = 'https://atrs-api.firs.gov.ng/v1/bills/report' if \
                rec_data.firs_type == 'production' else 'https://api-dev.i-fis.com/v1/bills/report'
            request = requests.post(url, data=json.dumps(data_dict), headers=headers, timeout=10)
            if request.status_code == 200:
                resp = request.json()
                if isinstance(resp, dict) and 'payment_code' in resp:
                    self.write({
                        "sk_sid": security_code,
                        "sk_uid": resp.get('payment_code'),
                        "receipt_seq": self.id,
                        "sk_uploaded": True
                    })
                else:
                    raise Warning(request.text)
            else:
                raise Warning(request.text)

    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position_id(self):
        self.is_fiscal_position_accural = False
        if self.fiscal_position_id.is_accural:
            self.is_fiscal_position_accural = True



