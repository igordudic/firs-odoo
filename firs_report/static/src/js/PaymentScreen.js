odoo.define('firs_report.PaymentScreen', function(require) {
    'use strict';
    var PaymentScreenWidget = require('point_of_sale.screens').PaymentScreenWidget;
    var core = require('web.core');
    var rpc = require('web.rpc');
    var _t = core._t;

    // On Payment screen, allow online payments
    PaymentScreenWidget.include({
        validate_order: async function(force_validation) {
            if (this.pos.get_order().is_paid() && !this.invoicing) {
                var lines = this.pos.get_order().get_paymentlines();

                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].mercury_swipe_pending) {
                        this.pos.get_order().remove_paymentline(lines[i]);
                        this.render_paymentlines();
                    }
                }

                var conf = this.pos.get('conf_info');
                if (!conf) {
                    this.gui.show_popup('error', {
                        'title': _t('Error'),
                        'body': _t('Federal Inland Revenue Service configurations not provided!!!'),
                    });
                }

                var currentOrder = this.pos.get_order();
                var d = new Date();
                var crr = d.toISOString();
                var new_date = crr.split(".");
                if (new_date.length > 1) {
                    crr = new_date[0];
                }
                var tot = currentOrder.get_total_with_tax().toFixed(2).toString();
                var totex = currentOrder.get_total_without_tax().toString();
                var order_name = currentOrder.name.split(' ').slice(1).join(' ');
                var pos_name = order_name.replaceAll('-', '');

                var bill_number = Date.now();
                var val = conf.client_secret + conf.vat_number + conf.business_place + currentOrder.pos_session_id.toString() + bill_number + crr + tot;
                var receipt_seq = conf.business_place + "/" + currentOrder.pos_session_id.toString() + "/" + currentOrder.sequence_number.toString();

                var md5 = $.md5(val);

                currentOrder.sk_sid = md5;
                currentOrder.receipt_seq = receipt_seq;
                currentOrder.sk_sequence = currentOrder.sequence_number.toString();
                currentOrder.bill_datetime = crr;
                var taxes = currentOrder.get_tax_details();
                var vals = {
                    "bill_datetime": crr,
                    "bill_number": bill_number,
                    "device": currentOrder.pos_session_id.toString(),
                    "payment_type": "C",
                    "security_code": md5,
                    "total_value": tot,
                    "total_without_tax": totex,
                    "taxes": taxes,
                    'conf_id': conf.id,
                };

                var self = this;
                var uid_code = false;
        try {
            uid_code = await rpc.query({
                model: 'firs.config',
                method: 'get_report',
                args: [vals],
                kwargs: {},
            });
            currentOrder.sk_uid = uid_code;
            currentOrder.sk_sid = md5;
            self.finalize_validation();
            console.log("RPC Result:", uid_code);
        } catch (reason) {
            self.finalize_validation();
        }
    }

    return await this._super?.(force_validation) || true;
}
    });
});
