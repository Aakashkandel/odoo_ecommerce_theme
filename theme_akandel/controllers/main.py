from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request, route

from odoo.addons.website.controllers.main import Website


class AkandelWebsite(Website):

    @route()
    def get_dynamic_snippet_templates(self, filter_name=False):
        """Theme templates are copied per website: only list the ones of the
        current website (and generic ones), never duplicates from others."""
        templates = super().get_dynamic_snippet_templates(filter_name=filter_name)
        keys = [t['key'] for t in templates if t['key'].startswith('theme_akandel.')]
        if not keys:
            return templates
        View = request.env['ir.ui.view'].sudo()
        allowed = View.search([('key', 'in', keys)] + request.website.website_domain())
        allowed_ids = set(allowed.filter_duplicate().ids)
        return [
            t for t in templates
            if not t['key'].startswith('theme_akandel.') or t['id'] in allowed_ids
        ]


class AkandelCart(http.Controller):

    @route('/ak/cart_panel', type='jsonrpc', auth='public', website=True, sitemap=False)
    def ak_cart_panel(self, mode='full', added_line_ids=None, **kwargs):
        """Render the Akandel add-to-cart panel (drawer, modal, toast...).

        Only reads the current cart; quantities are changed through Odoo's own
        `/shop/cart/update` route, so pricing and cart rules stay standard.
        """
        website = request.website
        View = request.env['ir.ui.view']
        if not website.viewref('theme_akandel.ak_cart_panel', raise_if_not_found=False):
            return {}  # theme not applied on this website
        order = request.cart
        added = [int(i) for i in (added_line_ids or []) if str(i).isdigit()]
        recommendations = []
        if order and website.is_view_active('theme_akandel.ak_cart_opt_reco'):
            recommendations = order._cart_accessories()[:4]
        freeship = website.ak_free_shipping_threshold \
            if website.is_view_active('theme_akandel.ak_cart_opt_freeship') else 0
        html = View._render_template('theme_akandel.ak_cart_panel', {
            'website': website,
            'website_sale_order': order,
            'mode': 'added' if mode == 'added' else 'full',
            'added_line_ids': added,
            'recommendations': recommendations,
            'freeship_threshold': freeship,
        })
        return {
            'html': html,
            'cart_quantity': order.cart_quantity if order else 0,
        }

    @route('/ak/config/website', type='jsonrpc', auth='user')
    def ak_config_website(self, **options):
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise NotFound()
        website = request.env['website'].get_current_website()
        values = {}
        if 'ak_free_shipping_threshold' in options:
            values['ak_free_shipping_threshold'] = max(float(options['ak_free_shipping_threshold'] or 0), 0)
        if values:
            website.write(values)
        return True
