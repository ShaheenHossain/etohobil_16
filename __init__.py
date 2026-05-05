
# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def uninstall_hook(cr, registry):
    """Remove all products created by this module during uninstall"""
    # Don't use env here - just execute raw SQL to avoid transaction issues
    cr.execute("""
        DELETE FROM product_product 
        WHERE is_payment_product = True
    """)

    cr.execute("""
        DELETE FROM product_template 
        WHERE is_payment_product = True
    """)

    _logger.info("Uninstall hook: Removed payment products")


from . import models
from . import wizards