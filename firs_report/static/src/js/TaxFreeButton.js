odoo.define('firs_report.TaxFreeButton', function (require) {
"use strict";
var core = require('web.core');
var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');

//Custom Code
var TaxFreeButton = screens.ActionButtonWidget.extend({
    template: 'TaxFreeButton',

    button_click: function(){
            var pos_order = this.pos.get_order();
            console.log(pos_order,"pos_order")
        	if (pos_order!==null){
	    		pos_order.is_tax_free_order=true;
	    		var orderlines = pos_order.get_orderlines();
	    		$.each(orderlines,function(index){
	    			var line = orderlines[index];
	    			//line.get_product().taxes_id = [];
					//line.price_manually_set=true;
	    			line.trigger('change',line);
	    		})
	    	}

    },

    custom_function: function(){
        console.log('Hi I am button click of CustomButton');
    }

});

screens.define_action_button({
    'name': 'tax_free_button',
    'widget': TaxFreeButton,
});
});

