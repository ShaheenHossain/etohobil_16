odoo.define('etohobil_16.disable_button', function (require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        _onButtonClicked: function (event) {
            var self = this;
            var $button = $(event.data.originalEvent.currentTarget);
            var button = $button.data('button');

            // Check if this is our button
            if (button && button.name === 'action_add_all_products') {
                // Disable the button
                $button.prop('disabled', true);
                $button.addClass('disabled');

                // Execute the original action
                var result = this._super.apply(this, arguments);

                // Re-enable after 3 seconds or on error
                if (result && result.then) {
                    result.finally(function () {
                        setTimeout(function() {
                            $button.prop('disabled', false);
                            $button.removeClass('disabled');
                        }, 3000);
                    }).catch(function() {
                        setTimeout(function() {
                            $button.prop('disabled', false);
                            $button.removeClass('disabled');
                        }, 3000);
                    });
                }
                return result;
            }
            return this._super.apply(this, arguments);
        },
    });
});