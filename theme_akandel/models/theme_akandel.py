import logging

from lxml import etree, html

from odoo import api, models
from odoo.addons.website.models.theme_models import ThemeUtils as WebsiteThemeUtils

_logger = logging.getLogger(__name__)

# Desktop header variants (selectable from Website Builder > Header > Template).
AKANDEL_HEADER_TEMPLATES = [
    'theme_akandel.template_header_ak_essential',
    'theme_akandel.template_header_ak_centered',
    'theme_akandel.template_header_ak_announce',
    'theme_akandel.template_header_ak_category',
    'theme_akandel.template_header_ak_promo',
    'theme_akandel.template_header_ak_minimal',
    'theme_akandel.template_header_ak_split',
    'theme_akandel.template_header_ak_floating',
    'theme_akandel.template_header_ak_search',
    'theme_akandel.template_header_ak_luxe',
    'theme_akandel.template_header_ak_bold',
    'theme_akandel.template_header_ak_utility',
    'theme_akandel.template_header_ak_stacked',
    'theme_akandel.template_header_ak_pill',
    'theme_akandel.template_header_ak_transparent',
    'theme_akandel.template_header_ak_dark',
    'theme_akandel.template_header_ak_brand',
    'theme_akandel.template_header_ak_searchpill',
    'theme_akandel.template_header_ak_contact',
    'theme_akandel.template_header_ak_chips',
    'theme_akandel.template_header_ak_boxed',
    'theme_akandel.template_header_ak_caps',
    'theme_akandel.template_header_ak_duo',
    'theme_akandel.template_header_ak_slim',
]

# Mobile navigation variants (selectable from Website Builder > Header > Mobile Style).
AKANDEL_MOBILE_TEMPLATES = [
    'theme_akandel.template_header_mobile_ak_refined',
    'theme_akandel.template_header_mobile_ak_centered',
    'theme_akandel.template_header_mobile_ak_drawer',
    'theme_akandel.template_header_mobile_ak_fullscreen',
    'theme_akandel.template_header_mobile_ak_sheet',
    'theme_akandel.template_header_mobile_ak_tabbar',
    'theme_akandel.template_header_mobile_ak_search',
    'theme_akandel.template_header_mobile_ak_compact',
    'theme_akandel.template_header_mobile_ak_promo',
    'theme_akandel.template_header_mobile_ak_dark',
    'theme_akandel.template_header_mobile_ak_floating',
    'theme_akandel.template_header_mobile_ak_chips',
    'theme_akandel.template_header_mobile_ak_brand',
    'theme_akandel.template_header_mobile_ak_darkbar',
    'theme_akandel.template_header_mobile_ak_glass',
    'theme_akandel.template_header_mobile_ak_bordered',
    'theme_akandel.template_header_mobile_ak_gold',
    'theme_akandel.template_header_mobile_ak_rounded',
    'theme_akandel.template_header_mobile_ak_bigtype',
    'theme_akandel.template_header_mobile_ak_iconpills',
    'theme_akandel.template_header_mobile_ak_leftdark',
    'theme_akandel.template_header_mobile_ak_sheetdark',
    'theme_akandel.template_header_mobile_ak_cards',
    'theme_akandel.template_header_mobile_ak_clean',
]

# Footer variants (selectable from Website Builder > Footer > Template).
AKANDEL_FOOTER_TEMPLATES = [
    'theme_akandel.template_footer_ak_columns',
    'theme_akandel.template_footer_ak_newsletter',
    'theme_akandel.template_footer_ak_centered',
    'theme_akandel.template_footer_ak_minimal',
    'theme_akandel.template_footer_ak_mega',
    'theme_akandel.template_footer_ak_trust',
    'theme_akandel.template_footer_ak_statement',
    'theme_akandel.template_footer_ak_contact',
    'theme_akandel.template_footer_ak_split',
    'theme_akandel.template_footer_ak_payments',
    'theme_akandel.template_footer_ak_gallery',
    'theme_akandel.template_footer_ak_cards',
    'theme_akandel.template_footer_ak_app',
    'theme_akandel.template_footer_ak_darkcols',
    'theme_akandel.template_footer_ak_bigbrand',
    'theme_akandel.template_footer_ak_twotone',
    'theme_akandel.template_footer_ak_support',
    'theme_akandel.template_footer_ak_newsleft',
    'theme_akandel.template_footer_ak_wave',
    'theme_akandel.template_footer_ak_linkgrid',
    'theme_akandel.template_footer_ak_socialband',
    'theme_akandel.template_footer_ak_categories',
    'theme_akandel.template_footer_ak_compactdark',
    'theme_akandel.template_footer_ak_brandcta',
]


class ThemeUtils(models.AbstractModel):
    _inherit = 'theme.utils'

    # Registering the Akandel variants lets `enable_view` switch away from
    # every other header/footer template, exactly like the core ones. The
    # core default template must stay last (see `_reset_default_config`).
    _header_templates = AKANDEL_HEADER_TEMPLATES + WebsiteThemeUtils._header_templates
    _footer_templates = AKANDEL_FOOTER_TEMPLATES + WebsiteThemeUtils._footer_templates

    def _theme_akandel_post_copy(self, mod):
        self.enable_view('theme_akandel.template_header_ak_essential')
        self.enable_view('theme_akandel.template_header_mobile_ak_refined')
        self.enable_view('theme_akandel.template_footer_ak_columns')
        self.enable_view('website.header_hoverable_dropdown')
        self.enable_view('website.option_footer_scrolltop')
        # Shop page style, shop extras and the side drawer cart experience.
        self.enable_view('theme_akandel.ak_shop_style_clean')
        self.enable_view('theme_akandel.ak_shop_product_count')
        self.enable_view('theme_akandel.ak_shop_trust_bar')
        self.enable_view('theme_akandel.ak_cart_style_drawer')
        self.enable_view('theme_akandel.ak_cart_opt_freeship')
        self.enable_view('theme_akandel.ak_cart_opt_reco')
        # Clean storefront header by default; both stay available in
        # Website Builder > Header > Elements.
        self.disable_view('website.header_text_element')
        self.disable_view('website.header_call_to_action')
        self._akandel_seed_homepage()

    @api.model
    def _akandel_seed_homepage(self):
        """Fill the homepage with the Akandel sections, unless the store owner
        already designed it on this website. The sections are rendered once
        and saved as regular, fully editable Website Builder content."""
        website = self.env['website'].get_current_website()
        homepage = website.with_context(website_id=website.id).viewref('website.homepage', raise_if_not_found=False)
        if not homepage:
            return
        wrap = etree.fromstring(homepage.arch).xpath("//div[@id='wrap']")
        if not wrap:
            return
        if homepage.website_id and len(wrap[0]):
            # The homepage was customized on this website: keep it.
            return
        try:
            content = self.env['ir.qweb'].with_context(website_id=website.id)._render(
                'theme_akandel.ak_homepage_sections', {'website': website},
            )
        except Exception:  # noqa: BLE001 - seeding must never block a theme install
            _logger.exception("Akandel: could not render the default homepage sections")
            return
        wrap_html = '<div id="wrap" class="oe_structure oe_empty">%s</div>' % content
        # Validate the markup before saving it into the view.
        html.fromstring(wrap_html)
        homepage.with_context(website_id=website.id).save(wrap_html, xpath="//div[@id='wrap']")
