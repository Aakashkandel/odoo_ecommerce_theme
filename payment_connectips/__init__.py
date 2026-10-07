# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from . import controllers
from . import models

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    setup_provider(env, "connectips")


def uninstall_hook(env):
    reset_payment_provider(env, "connectips")
