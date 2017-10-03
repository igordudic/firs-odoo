odoo.define('firs_report.main', function (require) {
"use strict";
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var _t = core._t;
	var gui = require('point_of_sale.gui');
	var popup_widget = require('point_of_sale.popups');
	var SuperPaymentScreenWidget = screens.PaymentScreenWidget.prototype;
	var models = require('point_of_sale.models');
	var time = require('web.time');
	var Model = require('web.DataModel');


	var _super = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes, options) {
            _super.prototype.initialize.apply(this, arguments);
            this.set({
                sk_sid: false,
                sk_sequence: false,
                receipt_seq: false,
                sk_uid:false
            });
            
        },
        export_for_printing: function() {
            var currentOrder = this.pos.get_order();
            var json = _super.prototype.export_for_printing.apply(this, arguments);
            json.sk_sid = currentOrder.get('sk_sid');
            json.sk_uid = currentOrder.get('sk_uid');
            json.sk_sequence = currentOrder.get('sk_sequence');
            json.receipt_seq = currentOrder.get('receipt_seq');
            return json;
        },
        export_as_JSON: function() {
            self = this;
            var currentOrder = self.pos.get_order();
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            if (currentOrder != undefined) {
                json.sk_sid = currentOrder.get('sk_sid');
                json.sk_uid = currentOrder.get('sk_uid');
				json.sk_sequence = currentOrder.get('sk_sequence');
                json.receipt_seq = currentOrder.get('receipt_seq');
            }
            return json;
		},
	});
	


	models.load_models([{
        model: 'firs.config',
        fields: [],
        loaded: function(self, result) {
			console.log(result)
            if (result.length) {
                self.set('conf_info', result[0]);
            }
		},}], { 'after': 'product.product' });
		

	screens.PaymentScreenWidget.include({
		validate_order: function(force_validation) {
			var self = this;
			if (this.order_is_valid(force_validation)) {
				var conf = this.pos.get('conf_info');

				if (!conf){
					this.gui.show_popup('error',{
						'title': _t('Error'),
						'body': _t('Federal Inland Revenue Service configurations not provided!!!'),
					});
				}

				var currentOrder = self.pos.get_order();

				var crr = time.datetime_to_str(new Date());
                var tot = currentOrder.get_total_with_tax().toString();
                var totex = currentOrder.get_total_without_tax().toString();

                var val = conf.client_secret + conf.vat_number+ conf.business_place + currentOrder.pos_session_id.toString() + currentOrder.sequence_number.toString() + crr + tot;
				var receipt_seq = conf.business_place+"/"+currentOrder.pos_session_id.toString()+"/"+currentOrder.sequence_number.toString();


				var md5 = $.md5(val);

                currentOrder.set('sk_sid', md5);
				currentOrder.set('receipt_seq', receipt_seq);
				currentOrder.set('sk_sequence', currentOrder.sequence_number.toString());

				var taxes = currentOrder.get_tax_details();

				(new Model('firs.config')).call('get_report', [{
					"bill_datetime": crr,
					"bill_number": currentOrder.sequence_number.toString(),
					"device": currentOrder.pos_session_id.toString(),
					"payment_type": "C",
					"security_code": md5,
					"total_value": tot,
					"total_without_tax": totex,
					"taxes": taxes,
					'conf_id': conf.id
                }])
				.then(function(result) {
					console.log(result);
					currentOrder.set('sk_uid', result);
					self.finalize_validation();
				})
				.fail(function(error, event) {
					self.finalize_validation();
					console.log('fail');

				});

			}
		}
	});



});