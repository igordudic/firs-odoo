odoo.define('firs_report.OrderReceipt', function(require) {
    'use strict';

    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');
	
    const FIRSReportOrderReceipt = OrderReceipt =>
        class extends OrderReceipt {
            /**
             * The receipt has signature if one of the paymentlines
             * is paid with mercury.
             */
            get getReceiptQRCodeValue() {
                
				let order = this.env.pos.get_order();
				if (order.sk_uid !== undefined && order.sk_uid !==null && order.sk_uid !== false){
		        	var url = "https://ecitizen.i-fis.com.ng/en/payment-code-verify/"+order.sk_uid;
		        }
		        else{
		        	var conf_info = this.env.pos.get('conf_info');
		        	var url = "https://ecitizen.i-fis.com.ng/en/security-code-verify/";
		        	url += conf_info.vat_number+"~"+order.sequence_number+"~"+conf_info.business_place+"~"+order.pos_session_id+"~"+order.get('bill_datetime')+"~"+order.get_total_with_tax().toFixed(2).toString()+"~"+order.get('sk_sid');
		        }
				return '/report/barcode/?type=QR&value='+url+'&width=125&height=125';
				
            }
        };

    Registries.Component.extend(OrderReceipt, FIRSReportOrderReceipt);

    return OrderReceipt;
});
