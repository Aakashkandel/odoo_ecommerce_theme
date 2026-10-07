# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Payment Provider: eSewa",
    "summary": "Accept payments through the eSewa ePay v2 gateway (Nepal).",
    "version": "19.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "website": "https://github.com/OCA/l10n-nepal",
    "author": "Amnil Technologies, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": ["payment"],
    "data": [
        "views/payment_esewa_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
        "data/ir_cron_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
}
