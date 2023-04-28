odoo.define('firs_report.main', function (require) {
"use strict";
	
	var core = require('web.core');
	var _t = core._t;
	//const PosBaseWidget = require('point_of_sale.BaseWidget');
	var models = require('point_of_sale.models');
	var time = require('web.time');
	var utils = require('web.utils');
	
    
    var _super_order_line = models.Orderline;
    models.Orderline = models.Orderline.extend({
		get_all_prices: function(){
        var self = this;

        var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        var taxtotal = 0;

        var product =  this.get_product();
        var taxes =  this.pos.taxes;
        var taxes_ids = _.filter(product.taxes_id, t => t in this.pos.taxes_by_id);
        var taxdetail = {};
        var product_taxes = [];
		//Changes added by Nilesh
		if (this.order.is_tax_free_order){
			taxes_ids=[];	
		}
        _(taxes_ids).each(function(el){
            var tax = _.detect(taxes, function(t){
                return t.id === el;
            });
            product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
        });
        product_taxes = _.uniq(product_taxes, function(tax) { return tax.id; });

        var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
        var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_quantity(), this.pos.currency.rounding);
        _(all_taxes.taxes).each(function(tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = tax.amount;
        });

        return {
            "priceWithTax": all_taxes.total_included,
            "priceWithoutTax": all_taxes.total_excluded,
            "priceSumTaxVoid": all_taxes.total_void,
            "priceWithTaxBeforeDiscount": all_taxes_before_discount.total_included,
            "tax": taxtotal,
            "taxDetails": taxdetail,
        };
    },
		
	});
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
            json.sk_sid = this.sk_sid;
            json.sk_uid = this.sk_uid;
            json.sk_sequence = this.sk_sequence;
            json.receipt_seq = this.receipt_seq;
            return json;
        },
        export_as_JSON: function() {
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            
            json.sk_sid = this.sk_sid;
            json.sk_uid = this.sk_uid;
			json.sk_sequence = this.sk_sequence;
            json.receipt_seq = this.receipt_seq;
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
	
});