odoo.define('pos_print_order_kitchen_browser.OrderKitchenReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class OrderKitchenReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._receiptEnv = this.props.changes;
        }
        willUpdateProps(nextProps) {
            this._receiptEnv = nextProps.changes;
        }
        get changes() {
            return this.receiptEnv;
        }
        get receiptEnv () {
          return this._receiptEnv;
        }
        isSimple(line) {
            return (
                line.discount === 0 &&
                line.unit_name === 'Units' &&
                line.quantity === 1 &&
                !(
                    line.display_discount_policy == 'without_discount' &&
                    line.price < line.price_lst
                )
            );
        }
    }
    OrderKitchenReceipt.template = 'OrderKitchenReceipt';

    Registries.Component.add(OrderKitchenReceipt);

    return OrderKitchenReceipt;
});
