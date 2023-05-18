odoo.define('firs_report.OrderReceipt', function (require) {
  'use strict';

  var screens = require('point_of_sale.screens');

  screens.ReceiptScreenWidget.include({
    render_receipt: function () {
      this._super();
      this.$('.pos-receipt-qr-code').attr('src', this.getReceiptQRCodeValue());
    },

    getReceiptQRCodeValue: function () {
      var order = this.pos.get_order();
      if (order && order.sk_uid !== undefined && order.sk_uid !== null && order.sk_uid !== false) {
        var url = "https://ecitizen.firs.gov.ng/en/payment-code-verify/" + order.sk_uid;
      } else {
        var conf_info = this.pos.get('conf_info');
        var url = "https://ecitizen.firs.gov.ng/en/security-code-verify/";
        url += conf_info.vat_number + "~" + order.sequence_number + "~" + conf_info.business_place + "~" + order.pos_session_id + "~" + order.get('bill_datetime') + "~" + order.get_total_with_tax().toFixed(2).toString() + "~" + order.get('sk_sid');
      }
      return '/report/barcode/?type=QR&value=' + encodeURIComponent(url) + '&width=125&height=125';
    },
  });
});

