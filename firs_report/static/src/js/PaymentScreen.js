odoo.define('firs_report.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const FIRSReportPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
				var self = this;

            	if (await this._isOrderValid(isForceValidate)) {
	                // remove pending payments before finalizing the validation
	                for (let line of this.paymentLines) {
	                    if (!line.is_done()) this.currentOrder.remove_paymentline(line);
	                    
	                }
					var conf = this.env.pos.get('conf_info');
					if (!conf){
						this.gui.show_popup('error',{
							'title': _t('Error'),
							'body': _t('Federal Inland Revenue Service configurations not provided!!!'),
						});
					}
					var currentOrder = this.env.pos.get_order();
					//var crr = time.datetime_to_str(new Date());
					var d = new Date();
					var crr = d.toISOString();
					var new_date = crr.split(".")
					if (new_date.length>1){
						crr = new_date[0];
					}
					var tot = currentOrder.get_total_with_tax();
	                var tot = tot.toFixed(2).toString();
	                var totex = currentOrder.get_total_without_tax().toString();
                    var order_name = currentOrder.name.split(' ').slice(1).join(' ')
                    var pos_name = order_name.replaceAll('-', '')

	                var bill_number =  currentOrder.pos.pos_session.id.toString() + conf.business_device + currentOrder.sequence_number.toString() + pos_name;
	                var val = conf.client_secret + conf.vat_number+ conf.business_place + currentOrder.pos_session_id.toString() + bill_number + crr + tot;
					var receipt_seq = conf.business_place+"/"+currentOrder.pos_session_id.toString()+"/"+currentOrder.sequence_number.toString();

					var md5 = $.md5(val);

	                currentOrder.sk_sid = md5;
					currentOrder.receipt_seq = receipt_seq;
					currentOrder.sk_sequence = currentOrder.sequence_number.toString();
					currentOrder.bill_datetime = crr;
					var taxes = currentOrder.get_tax_details();
					var vals = {
					"bill_datetime": crr,
					"bill_number": bill_number, //currentOrder.get_name(),
					"device": currentOrder.pos_session_id.toString(),
					"payment_type": "C",
					"security_code": md5,
					"total_value": tot,
					"total_without_tax": totex,
					"taxes": taxes,
					'conf_id': conf.id,
					}
					
					this.rpc({
		                model: 'firs.config',
		                method: 'get_report',
		                args: [vals],
		                kwargs: {},
		            }).then(function (result) {
		                currentOrder.sk_uid = result;
						currentOrder.sk_sid = md5;
						self._finalizeValidation();
		            }).catch(function (reason){
		                self._finalizeValidation();
		            });
	                
            	}
        	}
        };

    Registries.Component.extend(PaymentScreen, FIRSReportPaymentScreen);

    return PaymentScreen;
});
