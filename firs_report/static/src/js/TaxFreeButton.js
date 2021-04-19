odoo.define('firs_report.TaxFreeButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
	
	class TaxFreeButton extends PosComponent {
        onClick() {
        	var pos_order = this.env.pos.get_order();
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
        }
    };

    TaxFreeButton.template = 'TaxFreeButton';
	ProductScreen.addControlButton({
        component: TaxFreeButton,
        condition: function() {
            return true;
        },
    });

    Registries.Component.add(TaxFreeButton);

    return TaxFreeButton;
});
