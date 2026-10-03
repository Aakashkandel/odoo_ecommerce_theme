{
    'name': 'Akandel Theme',
    'description': 'Akandel - a modern, fully configurable eCommerce theme for Odoo 19 with 24+ designs for every section.',
    'category': 'Theme/Retail',
    'summary': 'eCommerce, Shop, Beauty, Health, Personal Care, Home, Lifestyle, Store',
    'sequence': 5,
    'version': '19.0.3.0.0',
    'author': 'Akandel',
    'license': 'LGPL-3',
    'depends': [
        'website_sale',
        'website_sale_wishlist',
        'website_mass_mailing',
    ],
    'data': [
        'data/ir_asset.xml',

        # Layout, shared components and header / footer variants
        'views/layout.xml',
        'views/header/headers.xml',
        'views/header/mobile_headers.xml',
        'views/header/headers_extra.xml',
        'views/header/mobile_headers_extra.xml',
        'views/footer/footers.xml',
        'views/footer/footers_extra.xml',

        # Building blocks
        'views/snippets/s_ak_heroes.xml',
        'views/snippets/s_ak_promos.xml',
        'views/snippets/s_ak_categories.xml',
        'views/snippets/s_ak_products.xml',
        'views/snippets/s_ak_collections.xml',
        'views/snippets/s_ak_story.xml',
        'views/snippets/s_ak_engagement.xml',
        'views/snippets/snippets.xml',

        # Section families (24 designs each), selectable in the Website Builder
        'views/sections/s_ak_hero_sliders.xml',
        'views/sections/s_ak_product_carousels.xml',
        'views/sections/s_ak_categories_dynamic.xml',
        'views/sections/s_ak_offers.xml',
        'views/sections/s_ak_galleries.xml',
        'views/sections/sections_registry.xml',

        # eCommerce presentation hooks
        'views/shop/shop_templates.xml',
        # Shop page styles (24), add-to-cart experiences (24) and shop options
        'views/shop/shop_styles.xml',
        'views/shop/cart_styles.xml',
        'views/shop/shop_options.xml',
    ],
    'images': [
        'static/description/akandel_cover.png',
        'static/description/akandel_screenshot.png',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_akandel/static/src/scss/theme.scss',
            'theme_akandel/static/src/scss/header.scss',
            'theme_akandel/static/src/scss/footer.scss',
            'theme_akandel/static/src/scss/snippets.scss',
            'theme_akandel/static/src/scss/shop.scss',
            'theme_akandel/static/src/scss/sections/*.scss',
            'theme_akandel/static/src/interactions/*.js',
        ],
        'website.website_builder_assets': [
            'theme_akandel/static/src/builder/**/*',
        ],
    },
}
