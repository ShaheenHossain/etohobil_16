{
    'name': 'eTohobil',
    'version': '16.0.0.0.1',
    'depends': ['base', 'mail', 'account', 'sale', 'web', 'purchase', 'portal'],
    'data': [
        # 'views/mail_template_member_invoice.xml',
        'views/member_payment.xml',
        'views/etohobil_members.xml',
        'views/etohobil_payment_history.xml',
        # 'views/payment_record_views.xml',
        # 'views/payment_structure_form_view.xml',
        'views/member_deposit_structure.xml',
        # 'views/bank_deposit_views.xml',
        # 'views/property_asset_views.xml',
        # 'views/loan_management_views.xml',
        # 'data/payment_structure_data.xml',
        # 'reports/payment_slip_report.xml',
         'security/ir.model.access.csv',
         'security/portal_security.xml',
         # 'data/payment.structure.csv',
        'data/member.deposit.structure.csv',
        'data/res.partner.csv',
        # 'views/account_chart_data.xml',
        'wizards/module_cleanup_wizard.xml',
        'views/portal_templates.xml',
        # 'views/member_reports.xml',
    ],


    'assets': {
        'web.assets_backend': [
            # 'web/static/src/js/widgets/form_controller.js',  # Path to FormController
            # 'web/static/src/js/core/rpc.js',  # Path to rpc
            # 'etohobil/static/src/js/sync_amount.js',
            'etohobil_16/static/src/js/disable_button.js',
        ]
    },


    'application': True,
    'installable': True,
    'auto_install': False,
    # 'uninstall_hook': 'uninstall_hook',

}
