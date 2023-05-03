odoo.define(
    'pos_print_kitchen_browser',
    function (require) {
        "use strict";
        var core = require('web.core');
        var QWeb = core.qweb;
        const { useRef } = owl.hooks;
        const ReceiptScreen = require('point_of_sale.AbstractReceiptScreen')
        const Registries = require('point_of_sale.Registries');
        var models = require('point_of_sale.models');
        const { Gui } = require('point_of_sale.Gui');
        const PosComponent = require('point_of_sale.PosComponent');

        const KotScreen = (ReceiptScreen) => {
            
            class KotScreen extends ReceiptScreen {
                constructor() {
                    super(...arguments);
                    this.orderReceipt = useRef('order-kot-receipt');
                    this.changes = arguments[1].changes

                }
                mounted() {
                    this.printReceipt();
                }
                confirm() {
                    this.props.resolve({ confirmed: true, payload: null });
                    this.trigger('close-temp-screen');
                }
                whenClosing() {
                    this.confirm();
                }
                async printReceipt() {
                    if(true) {
                        let result = await this._printReceipt();
                    }
                }
                async tryReprint() {
                    await this._printReceipt();
                }
                
            }
            KotScreen.template = 'KotScreen';
            return KotScreen
        }
        Registries.Component.addByExtending(KotScreen, ReceiptScreen)

        //gui.define_screen({name:'kot_receipt_browser', widget: KotScreen});
        var _super_order = models.Order.prototype;
        models.Order = models.Order.extend({
            printChanges: async function(){
                var printers = this.pos.printers;
                let isPrintSuccessful = true;
                var all_changes = null;
                for(var i = 0; i < printers.length; i++){
                    var changes = this.computeChanges(printers[i].config.product_categories_ids);
                    if ( changes['new'].length > 0 || changes['cancelled'].length > 0){
                        if (this.pos.config.print_kot_in_browser){
                            if (all_changes){
                                if (changes['new'].length > 0){
                                    all_changes['new'].push({name_wrapped:['### ' + printers[i].config?.name]})
                                    all_changes['new'] = all_changes['new'].concat(changes['new'])    
                                }
                                if (changes['cancelled'].length > 0){
                                    all_changes['cancelled'].push({name_wrapped:['### ' + printers[i].config?.name]})
                                    all_changes['cancelled'] = all_changes['cancelled'].concat(changes['cancelled'])
                                }
                                
                            }
                            else {
                                all_changes = changes
                            }
                        }else{
                            var receipt = QWeb.render('OrderChangeReceipt',{changes:changes, widget:this});
                            const result = await printers[i].print_receipt(receipt);
                            if (!result.successful) {
                                isPrintSuccessful = false;
                            }
                        }

                    }
                }
                if (all_changes){
                    Gui.showTempScreen('KotScreen', {changes:all_changes})
                }
                return isPrintSuccessful;
            },
        });


    }
)
