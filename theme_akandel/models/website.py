from odoo import fields, models
from odoo.fields import Domain


class Website(models.Model):
    _inherit = 'website'

    ak_free_shipping_threshold = fields.Float(
        string="Free Shipping Threshold (Akandel)",
        default=50.0,
        help="Order amount shown as the goal of the free shipping bar of the Akandel cart panel.",
    )

    def _akandel_get_nav_categories(self, limit=8):
        """Top-level eCommerce categories shown in Akandel category menus.

        Relies on website_sale's own availability rules, so visitors only see
        categories of this website that contain published products.
        """
        self.ensure_one()
        Category = self.env['product.public.category']
        domain = Domain('parent_id', '=', False) & Category._get_available_category_domain(self.id)
        return Category.search(domain, limit=limit)
