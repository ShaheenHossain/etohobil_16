# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ModuleCleanupWizard(models.TransientModel):
    _name = 'module.cleanup.wizard'
    _description = 'Clean up module data before uninstall'

    confirm = fields.Boolean(string="I understand this will delete all payment products", required=True)

    def action_cleanup_and_uninstall(self):
        """Clean up products and then uninstall the module"""
        if not self.confirm:
            raise UserError("Please confirm that you want to delete all payment products.")

        _logger.info("Starting cleanup of payment products")

        # Delete payment products
        products = self.env['product.product'].search([
            ('is_payment_product', '=', True)
        ])

        if products:
            _logger.info(f"Found {len(products)} products to delete")

            # Clear references from member.deposit.structure
            structures = self.env['member.deposit.structure'].search([
                ('payment_info', 'in', products.ids)
            ])
            if structures:
                structures.write({'payment_info': False})
                _logger.info(f"Cleared references from {len(structures)} deposit structures")

            # Delete products
            try:
                products.unlink()
                _logger.info(f"Successfully deleted {len(products)} products")
            except Exception as e:
                _logger.error(f"Error deleting products: {str(e)}")
                raise UserError(f"Error deleting products: {str(e)}")
        else:
            _logger.info("No payment products found to delete")

        # Now uninstall the module
        module = self.env['ir.module.module'].search([
            ('name', '=', 'etohobil_16')
        ], limit=1)

        if not module:
            raise UserError("Module not found")

        _logger.info("Starting module uninstall")

        # Return the uninstall action
        return module.button_immediate_uninstall()