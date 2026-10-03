"""Generate Akandel section families (hero sliders, product cards, category
cards, offers, galleries) as Odoo 19 theme XML + builder metadata."""
import json
import os
import sys
from xml.sax.saxutils import escape

ROOT = sys.argv[1]
VIEWS = os.path.join(ROOT, 'views/sections')
BUILDER = os.path.join(ROOT, 'static/src/builder')
os.makedirs(VIEWS, exist_ok=True)

L = '/website/static/src/img/library/'
D = '/website/static/src/img/snippets_demo/'
IMG = {
    'sofa': L + 'shop_generic_1_lg.jpg', 'velvet': L + 'shop_generic_2_lg.jpg', 'room': L + 'shop_generic_3_lg.webp',
    'c1': L + 'shop_category_1.webp', 'c2': L + 'shop_category_2.webp', 'c3': L + 'shop_category_3.webp',
    'c4': L + 'shop_category_4.webp', 'gift': L + 'gift.webp',
    'm1': D + 's_images_mosaic_default_image_1.jpg', 'm2': D + 's_images_mosaic_default_image_2.jpg',
    'm3': D + 's_images_mosaic_default_image_3.jpg', 'm4': D + 's_images_mosaic_default_image_4.jpg',
    'm5': D + 's_images_mosaic_default_image_5.jpg', 'bed': D + 's_parallax.jpg',
}
THUMB = '/theme_akandel/static/src/img/snippets_thumbs/'


def e(s):
    return escape(s, {'"': '&quot;'})


def header(*parts):
    return '<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n' + '\n'.join(parts) + '\n</odoo>\n'


# =============================================================== HERO SLIDERS
HERO_VARIANTS = [
    ('split', 'Split Classic', 'o_cc o_cc2'), ('reverse', 'Split Reverse', 'o_cc o_cc1'),
    ('cover', 'Full Cover', 'o_cc o_cc5'), ('center', 'Centered Cover', 'o_cc o_cc5'),
    ('cardcover', 'Cover with Card', 'o_cc o_cc5'), ('framed', 'Framed Panel', 'o_cc o_cc1'),
    ('circle', 'Circle Spotlight', 'o_cc o_cc2'), ('arch', 'Arch Window', 'o_cc o_cc1'),
    ('stage', 'Product Stage', 'o_cc o_cc2'), ('type', 'Big Typography', 'o_cc o_cc1'),
    ('stacked', 'Image Over Text', 'o_cc o_cc1'), ('diagonal', 'Diagonal Cut', 'o_cc o_cc2'),
    ('luxe', 'Dark Luxe', 'o_cc o_cc5'), ('offset', 'Offset Card', 'o_cc o_cc2'),
    ('zoom', 'Ken Burns Zoom', 'o_cc o_cc5'), ('bleed', 'Half Bleed', 'o_cc o_cc1'),
    ('promo', 'Compact Promo', 'o_cc o_cc4'), ('numbered', 'Numbered Slides', 'o_cc o_cc1'),
    ('glass', 'Glass Card', 'o_cc o_cc5'), ('inset', 'Rounded Inset', 'o_cc o_cc1'),
    ('checklist', 'Feature Checklist', 'o_cc o_cc2'), ('ring', 'Dashed Ring', 'o_cc o_cc1'),
    ('tilt', 'Tilted Frames', 'o_cc o_cc2'), ('progress', 'Progress Bars', 'o_cc o_cc5'),
]
SLIDES = [
    dict(eyebrow='New season', t1='Everyday essentials,', hl='thoughtfully made', t2='.',
         text='Discover carefully selected products, checked for quality and delivered with care.',
         cta='Shop now', img='sofa', alt='Bright living room with a grey sofa', tagl='Up to', tagv='40% off'),
    dict(eyebrow='Quality first', t1='Products you can', hl='trust', t2=', every day.',
         text='Every item is inspected before it carries our name, so what you receive is exactly what you expect.',
         cta='Explore the range', img='m2', alt='Sculptural ceramic vase on marble', tagl='Just', tagv='Arrived'),
    dict(eyebrow='Limited offer', t1='Save big on our', hl='best sellers', t2='.',
         text='Customer favourites at their best price of the season. While stocks last.',
         cta='See the deals', img='room', alt='Sunlit room with a minimal table', tagl='Save', tagv='30%'),
    dict(eyebrow='Free delivery', t1='Delivered to your door,', hl='fast', t2='.',
         text='Free shipping on orders over $50 and easy 30-day returns on every purchase.',
         cta='Start shopping', img='gift', alt='Wrapped gift box', tagl='Free', tagv='Shipping'),
    dict(eyebrow='Curated picks', t1='Little details make a', hl='big difference', t2='.',
         text='Hand-picked favourites from trusted brands, chosen for how they make you feel.',
         cta='Browse picks', img='m4', alt='Terracotta vases in an arched niche', tagl='Top', tagv='Rated'),
    dict(eyebrow='Members club', t1='Join today and get', hl='10% off', t2=' your first order.',
         text='Early access to launches, exclusive offers and rewards on every purchase.',
         cta='Join the club', img='m3', alt='Oak desk and chair', tagl='Extra', tagv='10% off'),
]
POINTS = ['Quality checked', 'Fast, tracked delivery', '30-day easy returns']


def hero_slide(s, active, idx):
    pts = ''.join(f'<li><i class="fa fa-check" aria-hidden="true"/><span>{e(p)}</span></li>' for p in POINTS)
    return f'''
                <div class="carousel-item ak-slide{' active' if active else ''}" data-name="Slide">
                    <div class="container ak-slide-inner">
                        <div class="ak-slide-content">
                            <span class="ak-slide-index" aria-hidden="true">0{idx}</span>
                            <p class="ak-eyebrow">{e(s['eyebrow'])}</p>
                            <h2 class="ak-slide-title">{e(s['t1'])} <span class="ak-hl">{e(s['hl'])}</span>{e(s['t2'])}</h2>
                            <p class="ak-slide-text">{e(s['text'])}</p>
                            <p class="ak-slide-actions"><a href="/shop" class="btn btn-primary btn-lg">{e(s['cta'])}</a> <a href="/aboutus" class="btn btn-outline-primary btn-lg ak-btn-ghost">Learn more</a></p>
                            <ul class="ak-slide-points list-unstyled">{pts}</ul>
                        </div>
                        <div class="ak-slide-media">
                            <img class="ak-slide-img" src="{IMG[s['img']]}" alt="{e(s['alt'])}" loading="{'eager' if active else 'lazy'}"/>
                            <div class="ak-slide-tag"><span class="ak-slide-tag-label">{e(s['tagl'])}</span><span class="ak-slide-tag-value">{e(s['tagv'])}</span></div>
                        </div>
                    </div>
                </div>'''


def hero_template(i, key, name, cc):
    slides = [SLIDES[(i + k) % len(SLIDES)] for k in range(3)]
    num = f'{i + 1:02d}'
    body = ''.join(hero_slide(s, k == 0, k + 1) for k, s in enumerate(slides))
    active_attr = ' class="active" aria-current="true"'
    ind = ''.join(
        f'<button type="button" t-attf-data-bs-target="#akHero{{{{uniq}}}}" data-bs-slide-to="{k}"'
        f'{active_attr if k == 0 else ""} aria-label="Carousel indicator"/>' for k in range(3))
    return f'''
<template id="s_ak_hero_slider_{num}" name="Akandel Hero Slider {num} - {e(name)}">
    <section class="s_ak_hero_slider ak-hs-{key} {cc} pt0 pb0" data-snippet="s_ak_hero_slider" data-name="Hero Slider">
        <t t-set="uniq" t-value="datetime.datetime.now().microsecond"/>
        <div t-attf-id="akHero{{{{uniq}}}}" class="s_carousel carousel slide ak-hs-carousel" data-bs-ride="carousel" data-bs-interval="7000">
            <div class="carousel-inner">{body}
            </div>
            <button class="carousel-control-prev o_not_editable" contenteditable="false" t-attf-data-bs-target="#akHero{{{{uniq}}}}" data-bs-slide="prev" aria-label="Previous" title="Previous">
                <span class="carousel-control-prev-icon" aria-hidden="true"/>
                <span class="visually-hidden">Previous</span>
            </button>
            <button class="carousel-control-next o_not_editable" contenteditable="false" t-attf-data-bs-target="#akHero{{{{uniq}}}}" data-bs-slide="next" aria-label="Next" title="Next">
                <span class="carousel-control-next-icon" aria-hidden="true"/>
                <span class="visually-hidden">Next</span>
            </button>
            <div class="carousel-indicators o_not_editable">{ind}</div>
        </div>
    </section>
</template>'''


hero_xml = header(*[hero_template(i, k, n, cc) for i, (k, n, cc) in enumerate(HERO_VARIANTS)])
open(os.path.join(VIEWS, 's_ak_hero_sliders.xml'), 'w').write(hero_xml)


# =============================================================== PRODUCT CARDS
# (key, name, kit, number-of-elements, sm, rows per slide, arrow position)
PRODUCT_CARDS = [
    ('classic', 'Classic Card', 'vertical', 4, 2, 1, ''),
    ('rows', 'Horizontal Rows', 'horizontal', 3, 1, 2, ''),
    ('minimal', 'Minimal Clean', 'vertical', 4, 2, 1, ''),
    ('reveal', 'Hover Reveal', 'overlay', 4, 2, 1, ''),
    ('sale', 'Sale Badge Card', 'vertical', 4, 2, 1, ''),
    ('deal', 'Super Deal Wide', 'feature', 2, 1, 1, ''),
    ('round', 'Round Thumbnail', 'vertical', 5, 2, 1, ''),
    ('dark', 'Dark Card', 'vertical', 4, 2, 1, ''),
    ('mini', 'Mini List', 'list', 3, 1, 3, 'bottom'),
    ('portrait', 'Portrait Tall', 'vertical', 4, 2, 1, ''),
    ('pricetag', 'Price Tag', 'overlay', 4, 2, 1, ''),
    ('rated', 'Rated Card', 'vertical', 4, 2, 1, ''),
    ('gradient', 'Soft Gradient', 'vertical', 4, 2, 1, ''),
    ('quickadd', 'Quick Add', 'vertical', 4, 2, 1, ''),
    ('chip', 'Category Chip', 'vertical', 4, 2, 1, ''),
    ('tworows', 'Grid Two Rows', 'vertical', 4, 2, 2, 'bottom'),
    ('duo', 'Wide Duo', 'horizontal', 2, 1, 1, ''),
    ('compact', 'Compact Six', 'vertical', 6, 2, 1, ''),
    ('outline', 'Outline Hover', 'vertical', 4, 2, 1, ''),
    ('centered', 'Centered Link', 'vertical', 4, 2, 1, ''),
    ('float', 'Floating Cart', 'vertical', 4, 2, 1, ''),
    ('gold', 'Gold Accent', 'vertical', 4, 2, 1, ''),
    ('pricefirst', 'Price First', 'vertical', 4, 2, 1, ''),
    ('indexed', 'Indexed Showcase', 'horizontal', 3, 1, 1, 'bottom'),
]

P_CAT = ('<span t-if="record.public_categ_ids" class="ak-pc-cat" '
         't-out="record.public_categ_ids[:1].name"/>')
P_NAME = ('<h3 class="ak-pc-name"><a t-att-href="product.website_url" t-att-title="data.get(\'display_name\')" '
          't-out="data.get(\'display_name\')"/></h3>')
P_PRICE = ('<div class="ak-pc-price product_price" aria-label="Price information">'
           '<t t-call="website_sale.price_dynamic_filter_template_product_product"/></div>')
P_DESC = ('<p t-if="product.description_sale" class="ak-pc-desc" t-out="product.description_sale"/>')
P_RATING = ('<div t-if="is_view_active(\'website_sale.product_comment\')" class="ak-pc-rating">'
            '<t t-call="portal_rating.rating_widget_stars_static">'
            '<t t-set="rating_avg" t-value="record.rating_avg"/><t t-set="rating_count" t-value="record.rating_count"/>'
            '</t></div>')
P_BADGE = ('<span t-if="data.get(\'has_discounted_price\') and data.get(\'list_price\')" class="ak-pc-badge">'
           '-<t t-out="int(round(100 - (data[\'price\'] / data[\'list_price\']) * 100))"/>%</span>'
           '<span t-if="is_sample" class="ak-pc-badge ak-pc-badge-sample">Sample</span>')
P_WISH = ('<button type="button" class="o_add_wishlist ak-pc-wish" data-action="o_wishlist" title="Add to wishlist" '
          'aria-label="Add to wishlist" t-att-data-product-template-id="product_template_id" '
          't-att-data-product-product-id="product_id"><span class="fa fa-heart-o" role="presentation"/></button>')


def p_cart(label=True, extra=''):
    lbl = '<span class="ak-pc-cart-label">Add to cart</span>' if label else ''
    return ('<button t-if="product._website_show_quick_add()" type="button" '
            f'class="js_add_cart ak-pc-cart btn btn-primary {extra}" title="Add to cart" aria-label="Add to cart" '
            't-att-data-product-id="product_id" t-att-data-product-selected="product.is_product_variant" '
            't-att-data-product-template-id="product_template_id" t-att-data-product-type="product.type" '
            't-att-data-show-quantity="is_view_active(\'website_sale.product_quantity\')">'
            f'<i class="fa fa-shopping-cart" role="presentation"/>{lbl}</button>')


P_MEDIA = ('<a t-att-href="product.website_url" class="ak-pc-media" contenteditable="false" t-att-title="product.display_name">'
           '<img class="ak-pc-img" t-att-src="data[\'image_512\']" t-att-alt="product.display_name" loading="lazy"/></a>')
P_VIEW = '<a t-att-href="product.website_url" class="ak-pc-view">View product <i class="fa fa-long-arrow-right" aria-hidden="true"/></a>'


def kit(name, k):
    if name == 'vertical':
        extra = {
            'rated': P_RATING + P_DESC, 'centered': '', 'chip': '', 'gold': P_RATING,
        }.get(k, '')
        actions = {
            'centered': P_VIEW, 'quickadd': '', 'float': '', 'minimal': '',
        }.get(k, p_cart())
        media_extra = {
            'quickadd': p_cart(False, 'ak-pc-cart-fab'), 'float': p_cart(False, 'ak-pc-cart-fab'),
            'minimal': p_cart(False, 'ak-pc-cart-fab'),
        }.get(k, '')
        if k == 'pricefirst':
            body = P_PRICE + P_NAME + P_CAT
        else:
            body = P_CAT + P_NAME + extra + P_PRICE
        return (f'<div class="ak-pc-media-wrap">{P_MEDIA}{P_BADGE}{P_WISH}{media_extra}</div>'
                f'<div class="ak-pc-body">{body}<div class="ak-pc-actions">{actions}</div></div>')
    if name == 'horizontal':
        return (f'<div class="ak-pc-media-wrap">{P_MEDIA}{P_BADGE}</div>'
                f'<div class="ak-pc-body">{P_CAT}{P_NAME}{P_DESC if k == "duo" else ""}'
                f'<div class="ak-pc-foot">{P_PRICE}{p_cart(k == "duo")}</div></div>')
    if name == 'overlay':
        return (f'<div class="ak-pc-media-wrap">{P_MEDIA}{P_BADGE}'
                f'<div class="ak-pc-overlay">{P_WISH}{p_cart(k == "reveal")}</div></div>'
                f'<div class="ak-pc-body">{P_NAME}{P_PRICE}</div>')
    if name == 'feature':
        return (f'<div class="ak-pc-media-wrap">{P_MEDIA}{P_BADGE}</div>'
                f'<div class="ak-pc-body">{P_CAT}{P_NAME}{P_PRICE}{P_DESC}'
                f'<div class="ak-pc-actions">{p_cart()}{P_WISH}</div></div>')
    if name == 'list':
        return (f'<div class="ak-pc-media-wrap">{P_MEDIA}</div>'
                f'<div class="ak-pc-body">{P_NAME}{P_PRICE}</div>{p_cart(False)}')
    raise ValueError(name)


def product_card_template(i, key, name, kitname, n, sm, rows, arrow):
    num = f'{i + 1:02d}'
    attrs = f'data-number-of-elements="{n}" data-number-of-elements-sm="{sm}" data-thumb="{THUMB}pc_{num}.svg"'
    if rows > 1:
        attrs += f' data-row-per-slide="{rows}"'
    if arrow:
        attrs += f' data-arrow-position="{arrow}"'
    return f'''
<template id="dynamic_filter_template_product_product_ak_{num}" name="Akandel {num} · {e(name)}">
    <t t-foreach="records" t-as="data" {attrs}>
        <t t-set="record" t-value="data['_record']"/>
        <t t-set="product" t-value="record"/>
        <t t-set="product_template_id" t-value="record.id if not record.is_product_variant else record.product_tmpl_id.id"/>
        <t t-set="product_id" t-value="record.id if record.is_product_variant else record.product_variant_id.id"/>
        <div class="o_carousel_product_card ak-pc ak-pc-kit-{kitname} ak-pc-{key}" role="article" t-att-aria-label="product.display_name" t-att-data-add2cart-rerender="data.get('_add2cart_rerender')">
            <input type="hidden" name="product-id" t-att-data-product-id="record.id"/>
            <span class="ak-pc-index" aria-hidden="true" t-out="'%02d' % (data_index + 1)"/>
            {kit(kitname, key)}
        </div>
    </t>
</template>'''


# Section presets using each card template.
HEADING_STYLES = ['line', 'center', 'eyebrow', 'underline', 'split', 'pill', 'bar', 'minimal']
PRODUCT_TITLES = [
    ('Featured products', 'Hand-picked for you'), ('Derma-approved essentials', 'Explore our latest formulas'),
    ('New arrivals', 'Just landed'), ('Trending now', 'What everyone is buying'),
    ('On sale', 'Limited-time prices'), ('Super deal', 'Deal of the week'),
    ('Best sellers', 'Customer favourites'), ('Editor\'s choice', 'Our team recommends'),
    ('Quick picks', 'Small prices, big love'), ('Fresh drops', 'New this week'),
    ('Price drop', 'Grab them while you can'), ('Top rated', 'Loved by customers'),
    ('Seasonal edit', 'Made for this season'), ('Add in one click', 'Fast favourites'),
    ('Shop by need', 'Find the right product'), ('More to discover', 'Browse the collection'),
    ('Spotlight', 'Two you should know'), ('Little extras', 'Perfect add-ons'),
    ('Most wanted', 'Back in stock'), ('Recommended', 'Picked for you'),
    ('Everyday essentials', 'Restock your favourites'), ('Premium selection', 'Our finest products'),
    ('Under $50', 'Great value picks'), ('The top three', 'Ranked by customers'),
]
FILTERS = ["dynamic_filter_newest_products", "dynamic_filter_newest_products"]
DESIGN_CLASSES = ('o_wsale_products_opt_layout_catalog o_wsale_products_opt_design_thumbs '
                  'o_wsale_products_opt_name_color_regular o_wsale_products_opt_cc1')


def product_section(i, key, name, kitname, n, sm, rows, arrow):
    num = f'{i + 1:02d}'
    title, eyebrow = PRODUCT_TITLES[i]
    hs = HEADING_STYLES[i % len(HEADING_STYLES)]
    flt = FILTERS[i % 2]
    cc = 'o_cc o_cc2' if i % 3 == 1 else 'o_cc o_cc1'
    extra = f' data-row-per-slide="{rows}"' if rows > 1 else ''
    if arrow:
        extra += f' data-arrow-position="{arrow}"'
    return f'''
<template id="s_ak_product_carousel_{num}" name="Akandel Products {num} - {e(name)}">
    <section data-snippet="s_dynamic_snippet_products" data-name="Products · {e(name)}"
        class="s_dynamic_snippet_products oe_website_sale s_dynamic o_dynamic_snippet_empty s_ak_products ak-ph-{hs} {cc} pt64 pb64 {DESIGN_CLASSES} s_product_product_ak_{num}"
        t-att-data-filter-id="(res_company.env.ref('website_sale.{flt}', raise_if_not_found=False) or res_company.env['website.snippet.filter']).id or None"
        data-template-key="theme_akandel.dynamic_filter_template_product_product_ak_{num}"
        data-number-of-records="12" data-number-of-elements="{n}" data-number-of-elements-small-devices="{sm}"{extra}
        data-product-category-id="all" data-show-variants="true" data-carousel-interval="5000" data-custom-template-data="{{}}">
        <t t-call="theme_akandel.ak_dynamic_products_body" _ak_eyebrow="{e(json.dumps(eyebrow))}" _ak_title="{e(json.dumps(title))}"/>
    </section>
</template>'''


prod_xml = header(
    *[product_card_template(i, *v) for i, v in enumerate(PRODUCT_CARDS)],
    *[product_section(i, *v) for i, v in enumerate(PRODUCT_CARDS)],
)
open(os.path.join(VIEWS, 's_ak_product_carousels.xml'), 'w').write(prod_xml)


# =============================================================== CATEGORY CARDS
# (key, name, column classes, extra row classes, label kit)
CATEGORY_CARDS = [
    ('circle', 'Circle Thumbs', 'col-4 col-md-3 col-lg-2', 'g-4 justify-content-center', 'below'),
    ('tile', 'Overlay Tiles', 'col-6 col-lg-3', 'g-3', 'over'),
    ('card', 'Cards with Link', 'col-6 col-lg-3', 'g-4', 'card'),
    ('pill', 'Image Pills', 'col-auto', 'g-3 justify-content-center', 'inline'),
    ('bento', 'Bento Grid', 'ak-cc-cell', 'ak-cc-grid ak-cc-grid-bento', 'over'),
    ('strip', 'Scroll Strip', 'ak-cc-cell', 'ak-cc-scroll', 'below'),
    ('numbered', 'Numbered List', 'col-md-6', 'g-0 ak-cc-counter', 'inline'),
    ('reveal', 'Hover Reveal', 'col-6 col-lg-3', 'g-3', 'over'),
    ('arch', 'Arch Frames', 'col-6 col-md-4 col-lg-2', 'g-4', 'below'),
    ('soft', 'Soft Squares', 'col-4 col-md-3 col-lg-2', 'g-4 justify-content-center', 'below'),
    ('gradient', 'Gradient Cards', 'col-6 col-lg-3', 'g-3', 'card'),
    ('polaroid', 'Polaroid', 'col-6 col-md-4 col-lg-3', 'g-4', 'card'),
    ('tall', 'Tall Portraits', 'col-6 col-lg-3', 'g-3', 'over'),
    ('large', 'Large Two Column', 'col-md-6', 'g-4', 'over'),
    ('masonry', 'Masonry', 'ak-cc-cell', 'ak-cc-grid ak-cc-grid-masonry', 'over'),
    ('rows', 'Side Rows', 'col-md-6 col-lg-4', 'g-3', 'inline'),
    ('outline', 'Outline Cards', 'col-6 col-md-4 col-lg-3', 'g-3', 'card'),
    ('glass', 'Glass Labels', 'col-6 col-lg-3', 'g-3', 'over'),
    ('ribbon', 'Ribbon Labels', 'col-6 col-lg-3', 'g-3', 'over'),
    ('stagger', 'Staggered', 'col-6 col-lg-3', 'g-4', 'below'),
    ('hexagon', 'Hexagons', 'col-4 col-md-3 col-lg-2', 'g-3 justify-content-center', 'below'),
    ('banner', 'Banner Stack', 'col-md-6', 'g-3', 'over'),
    ('links', 'Text Links', 'col-12', 'g-0', 'inline'),
    ('ring', 'Gradient Rings', 'col-4 col-md-3 col-lg-2', 'g-4 justify-content-center', 'below'),
]


def category_template(i, key, name, cols, extra, label):
    num = f'{i + 1:02d}'
    img = ('<span class="ak-cc-media"><img class="ak-cc-img" t-att-src="cat[\'cover_image\']" '
           't-att-alt="cat[\'name\']" loading="lazy"/></span>')
    nm = '<span class="ak-cc-name" t-out="cat[\'name\']"/>'
    link = '<span class="ak-cc-link">Shop now <i class="fa fa-long-arrow-right" aria-hidden="true"/></span>'
    idx = '<span class="ak-cc-index" aria-hidden="true" t-out="\'%02d\' % (cat_index + 1)"/>'
    inner = {
        'below': f'{img}<span class="ak-cc-body">{nm}</span>',
        'over': f'{img}<span class="ak-cc-body">{nm}{link}</span>',
        'card': f'{img}<span class="ak-cc-body">{nm}{link}</span>',
        'inline': f'{idx}{img}<span class="ak-cc-body">{nm}</span><i class="fa fa-angle-right ak-cc-chevron" aria-hidden="true"/>',
    }[label]
    return f'''
<template id="dynamic_filter_template_product_public_category_ak_{num}" name="Akandel {num} · {e(name)}">
    <t t-foreach="records" t-as="cat" data-number-of-elements="4" data-number-of-elements-sm="2"
       data-column-classes="{cols}" data-extra-classes="{extra}" data-thumb="{THUMB}cc_{num}.svg">
        <a t-attf-href="/shop/category/#{{cat['id']}}" class="ak-cc ak-cc-{label} ak-cc-{key}" t-att-title="cat['name']">{inner}</a>
    </t>
</template>'''


CAT_TITLES = ['Shop by category', 'Browse categories', 'Explore the range', 'Find what you need',
              'Popular categories', 'Categories', 'Shop departments', 'Discover more']


def category_section(i, key, name, cols, extra, label):
    num = f'{i + 1:02d}'
    hs = HEADING_STYLES[(i + 1) % len(HEADING_STYLES)]
    cc = 'o_cc o_cc2' if i % 4 == 2 else 'o_cc o_cc1'
    return f'''
<template id="s_ak_categories_{num}" name="Akandel Categories {num} - {e(name)}">
    <section data-snippet="s_ak_categories" data-name="Categories · {e(name)}"
        class="s_ak_categories s_dynamic o_dynamic_snippet_empty ak-ph-{hs} {cc} pt64 pb64 s_product_public_category_ak_{num}"
        t-att-data-filter-id="(res_company.env.ref('website_sale.dynamic_filter_category_list', raise_if_not_found=False) or res_company.env['website.snippet.filter']).id or None"
        data-template-key="theme_akandel.dynamic_filter_template_product_public_category_ak_{num}"
        data-number-of-records="12" data-number-of-elements="4" data-number-of-elements-small-devices="2"
        data-column-classes="{cols}" data-extra-classes="{extra}">
        <t t-call="theme_akandel.ak_dynamic_products_body" _ak_eyebrow="'Categories'" _ak_title="{e(json.dumps(CAT_TITLES[i % len(CAT_TITLES)]))}"/>
    </section>
</template>'''


cat_xml = header(
    *[category_template(i, *v) for i, v in enumerate(CATEGORY_CARDS)],
    *[category_section(i, *v) for i, v in enumerate(CATEGORY_CARDS)],
)
open(os.path.join(VIEWS, 's_ak_categories_dynamic.xml'), 'w').write(cat_xml)


# =============================================================== OFFERS
OFFER_VARIANTS = [
    ('cards', 'Image Cards'), ('overlay', 'Overlay Tiles'), ('feature', 'Feature + Two'),
    ('coupon', 'Coupon Tickets'), ('gradient', 'Gradient Tiles'), ('dark', 'Dark Deals'),
    ('circles', 'Circle Badges'), ('rows', 'Minimal Rows'), ('horizontal', 'Horizontal Cards'),
    ('polaroid', 'Polaroid Tilt'), ('dotd', 'Deal of the Day'), ('icons', 'Icon Offers'),
    ('gold', 'Gold Border'), ('stripes', 'Full-width Stripes'), ('imgleft', 'Image Left Rows'),
    ('mosaic', 'Mosaic'), ('ribbon', 'Corner Ribbons'), ('glass', 'Glass on Image'),
    ('blocks', 'Color Blocks'), ('percent', 'Big Percent'), ('stack', 'Stacked Banners'),
    ('arch', 'Arch Images'), ('duo', 'Offset Duo'), ('floating', 'Floating Badges'),
]
OFFERS = [
    dict(badge='-50%', name='Flat 50% Off', text='On selected essentials, this week only.', code='SAVE50', img='m2'),
    dict(badge='-60%', name='Up to 60% Off', text='Last pieces of the season at their lowest price.', code='LAST60', img='room'),
    dict(badge='Gift', name='Complimentary Gift', text='Free gift with every order over $75.', code='GIFT75', img='gift'),
]


def offer_template(i, key, name):
    num = f'{i + 1:02d}'
    cc = {'dark': 'o_cc o_cc5', 'gradient': 'o_cc o_cc1', 'blocks': 'o_cc o_cc1', 'stripes': 'o_cc o_cc1'}.get(key, 'o_cc o_cc1' if i % 2 == 0 else 'o_cc o_cc2')
    items = ''
    for k, o in enumerate(OFFERS):
        items += f'''
                <div class="ak-of-item">
                    <div class="ak-of-media"><img class="ak-of-img" src="{IMG[o['img']]}" alt="{e(o['name'])}" loading="lazy"/></div>
                    <div class="ak-of-body">
                        <span class="ak-of-badge">{e(o['badge'])}</span>
                        <h3 class="ak-of-name">{e(o['name'])}</h3>
                        <p class="ak-of-text">{e(o['text'])}</p>
                        <p class="ak-of-code">Use code <strong>{o['code']}</strong></p>
                        <a href="/shop" class="ak-of-link">+ Shop Now</a>
                    </div>
                </div>'''
    return f'''
<template id="s_ak_offers_{num}" name="Akandel Offers {num} - {e(name)}">
    <section class="s_ak_offers ak-of-{key} {cc} pt80 pb80" data-snippet="s_ak_offers" data-name="Offers">
        <div class="container">
            <div class="ak-of-head">
                <p class="ak-eyebrow">Limited offers</p>
                <h2 class="ak-of-title">Deals you will <span class="ak-hl">love</span></h2>
                <p class="ak-of-sub">Fresh savings every week on the products you use every day.</p>
            </div>
            <div class="ak-of-grid">{items}
            </div>
        </div>
    </section>
</template>'''


open(os.path.join(VIEWS, 's_ak_offers.xml'), 'w').write(
    header(*[offer_template(i, k, n) for i, (k, n) in enumerate(OFFER_VARIANTS)]))


# =============================================================== GALLERIES
GALLERY_VARIANTS = [
    ('grid', 'Classic Grid'), ('masonry', 'Masonry Columns'), ('bento', 'Bento Feature'),
    ('strip', 'Scroll Strip'), ('polaroid', 'Polaroid Scatter'), ('circles', 'Circles'),
    ('captions', 'Hover Captions'), ('film', 'Full-bleed Film'), ('stagger', 'Staggered'),
    ('offset', 'Offset Rows'), ('mosaic', 'Mosaic'), ('squares', 'Edge Squares'),
    ('framed', 'Framed Prints'), ('pills', 'Tall Pills'), ('slant', 'Slanted'),
    ('mono', 'Grayscale Reveal'), ('cards', 'Caption Cards'), ('bigleft', 'Big Left'),
    ('collage', 'Collage Overlap'), ('hexagon', 'Hexagons'), ('arch', 'Arch Row'),
    ('duo', 'Large Duo'), ('blob', 'Organic Shapes'), ('dark', 'Dark Gallery'),
]
GALLERY_IMGS = [('m1', 'Morning light'), ('m2', 'Pure shapes'), ('m3', 'Work corner'),
                ('m4', 'Earth tones'), ('m5', 'Soft curves'), ('velvet', 'Rich colour')]


def gallery_template(i, key, name):
    num = f'{i + 1:02d}'
    cc = 'o_cc o_cc5' if key == 'dark' else ('o_cc o_cc2' if i % 3 == 1 else 'o_cc o_cc1')
    rot = GALLERY_IMGS[i % 6:] + GALLERY_IMGS[:i % 6]
    figs = ''.join(
        f'''
                <figure class="ak-ga-item"><img class="ak-ga-img" src="{IMG[k]}" alt="{e(c)}" loading="lazy"/><figcaption class="ak-ga-cap">{e(c)}</figcaption></figure>'''
        for k, c in rot)
    return f'''
<template id="s_ak_gallery_{num}" name="Akandel Gallery {num} - {e(name)}">
    <section class="s_ak_gallery ak-ga-{key} {cc} pt80 pb80" data-snippet="s_ak_gallery" data-name="Gallery">
        <div class="container">
            <div class="ak-ga-head">
                <div>
                    <p class="ak-eyebrow">Gallery</p>
                    <h2 class="ak-ga-title">Moments from our <span class="ak-hl">community</span></h2>
                </div>
                <a href="/website/social/instagram" class="ak-link-arrow" target="_blank">Follow us <i class="fa fa-long-arrow-right ms-1" aria-hidden="true"/></a>
            </div>
            <div class="ak-ga-grid">{figs}
            </div>
        </div>
    </section>
</template>'''


open(os.path.join(VIEWS, 's_ak_galleries.xml'), 'w').write(
    header(*[gallery_template(i, k, n) for i, (k, n) in enumerate(GALLERY_VARIANTS)]))


# =============================================================== REGISTRY
def reg(prefix, items, group, kw, thumb):
    out = []
    for i, it in enumerate(items):
        num = f'{i + 1:02d}'
        out.append(f'        <t t-snippet="theme_akandel.{prefix}_{num}" string="{e(it[1])}" group="{group}" '
                   f't-thumbnail="{THUMB}{thumb}">'
                   f'<keywords>{kw}, {e(it[1].lower())}, akandel</keywords></t>')
    return '\n'.join(out)


registry_xml = header(f'''
<template id="snippets_sections" inherit_id="website.snippets" name="Akandel Section Families">
    <xpath expr="//snippets[@id='snippet_groups']/t[@snippet-group='intro']" position="before">
        <t snippet-group="ak_hero" t-snippet="website.s_snippet_group" string="Akandel · Hero Sliders" t-thumbnail="{THUMB}group_ak_hero.svg"/>
        <t snippet-group="ak_categories" t-snippet="website.s_snippet_group" string="Akandel · Categories" t-thumbnail="{THUMB}group_ak_categories.svg"/>
        <t snippet-group="ak_products" t-snippet="website.s_snippet_group" string="Akandel · Product Carousels" t-thumbnail="{THUMB}group_ak_products.svg"/>
        <t snippet-group="ak_offers" t-snippet="website.s_snippet_group" string="Akandel · Offers" t-thumbnail="{THUMB}group_ak_offers.svg"/>
        <t snippet-group="ak_gallery" t-snippet="website.s_snippet_group" string="Akandel · Galleries" t-thumbnail="{THUMB}group_ak_gallery.svg"/>
    </xpath>
    <xpath expr="//snippets[@id='snippet_structure']" position="inside">
{reg('s_ak_hero_slider', HERO_VARIANTS, 'ak_hero', 'hero, slider, carousel, banner, slideshow', 'group_ak_hero.svg')}
{reg('s_ak_categories', CATEGORY_CARDS, 'ak_categories', 'categories, shop by, departments, collections', 'group_ak_categories.svg')}
{reg('s_ak_product_carousel', PRODUCT_CARDS, 'ak_products', 'products, carousel, shop, best sellers, new arrivals', 'group_ak_products.svg')}
{reg('s_ak_offers', OFFER_VARIANTS, 'ak_offers', 'offers, deals, sale, discount, promotion, coupon', 'group_ak_offers.svg')}
{reg('s_ak_gallery', GALLERY_VARIANTS, 'ak_gallery', 'gallery, images, photos, lookbook, instagram', 'group_ak_gallery.svg')}
    </xpath>
</template>''')
open(os.path.join(VIEWS, 'sections_registry.xml'), 'w').write(registry_xml)

# =============================================================== BUILDER METADATA
meta = {
    'hero': [{'cls': f'ak-hs-{k}', 'title': f'{i + 1:02d} · {n}'} for i, (k, n, _) in enumerate(HERO_VARIANTS)],
    'offers': [{'cls': f'ak-of-{k}', 'title': f'{i + 1:02d} · {n}'} for i, (k, n) in enumerate(OFFER_VARIANTS)],
    'gallery': [{'cls': f'ak-ga-{k}', 'title': f'{i + 1:02d} · {n}'} for i, (k, n) in enumerate(GALLERY_VARIANTS)],
    'heading': [{'cls': f'ak-ph-{k}', 'title': k.capitalize()} for k in HEADING_STYLES],
}
js = ('// Generated by the Akandel section generator: keep in sync with views/sections/*.xml\n'
      f'export const AKANDEL_SECTION_DESIGNS = {json.dumps(meta, indent=4)};\n')
open(os.path.join(BUILDER, 'akandel_section_designs.js'), 'w').write(js)

# Thumbnail manifest for the SVG generator
json.dump({
    'products': [(f'{i + 1:02d}', v[0], v[2]) for i, v in enumerate(PRODUCT_CARDS)],
    'categories': [(f'{i + 1:02d}', v[0], v[4]) for i, v in enumerate(CATEGORY_CARDS)],
}, open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'sections_manifest.json'), 'w'))
print('ok', len(HERO_VARIANTS), len(PRODUCT_CARDS), len(CATEGORY_CARDS), len(OFFER_VARIANTS), len(GALLERY_VARIANTS))
