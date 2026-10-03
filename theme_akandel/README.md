# Akandel Theme for Odoo 19

A modern, fully configurable **eCommerce theme** for Odoo 19 Website +
eCommerce, with **24 or more designs for every section family**. Built only on Odoo 19's supported extension points: theme
views, theme assets, Website Builder options and native building blocks. No core
file is modified, and the shop, cart and checkout keep Odoo's standard behavior.

| | |
|---|---|
| Technical name | `theme_akandel` |
| Category | Theme / Retail |
| Odoo version | 19.0 (Community or Enterprise) |
| Depends on | `website_sale`, `website_sale_wishlist`, `website_mass_mailing` |
| License | LGPL-3 |

---

## 1. Installation

The module lives in `odoo_addons/theme_akandel`, which is mounted in the
container as `/mnt/odoo_addons` (see `stack.yml` / `config/odoo.conf`).

1. **Restart Odoo** so the addons path is rescanned:
   ```bash
   docker restart odoo_projects_web
   ```
2. Log in as an administrator, activate the developer mode and run
   **Apps > Update Apps List**.
3. **Apply the theme** (recommended way, so it gets its defaults):
   *Website > Configuration > Settings > Theme > **Choose a theme*** (or open
   the Website app on a new website) and pick **Akandel Theme**.

   Applying the theme from the theme chooser:
   * activates the **Akandel Essential** header, the **Refined** mobile
     navigation and the **Columns** footer,
   * activates the **Clean Cards** shop style (with product count and trust
     bar) and the **Side Drawer** add-to-cart experience (with free shipping
     bar and recommendations),
   * enables the hover sub-menus and the footer "scroll to top" button,
   * fills the homepage with the Akandel sections **only if the homepage was
     never designed on that website** (existing content is never overwritten).

   Installing `theme_akandel` from the Apps menu only makes it available.
   Applying it to a website is always done through the theme chooser, as for
   every Odoo theme.

Command line equivalent (installs the module only):

```bash
docker exec odoo_projects_web odoo server -c /etc/odoo/odoo.conf -d <db> -i theme_akandel --stop-after-init --no-http
```

---

## 2. Configuring the store in the Website Builder

Everything is edited in **Website > Edit**.

### Theme tab
* **Colors**: five Akandel palettes sit at the top of the palette list (*Clay*,
  *Noir*, *Sage*, *Coast*, *Rose*). Every Akandel style reads the active palette,
  so any palette or custom color works.
* **Fonts**: Poppins (headings) and Roboto (body) by default (see *Design
  system* below for the other fonts offered).
* Buttons, inputs, link styles, header/footer colors: standard Odoo options.


### Section families: 24 designs each

Five Website Builder categories hold 24 ready-made blocks each, and every
dropped block can switch to any other design of its family **without losing
its content** (Website Builder > block options):

| Family | Builder option | What you configure |
|---|---|---|
| **Akandel · Hero Sliders** | *Slider Design* (24) | Real carousels: add/remove slides, timing, images, texts, buttons, badges, colors |
| **Akandel · Product Carousels** | *Template* (24 card designs, with previews) + *Heading Style* (8) | Native Odoo Products block: filter (newest, recently sold/viewed...), **category, tags, product names, number of products**, variants; cards add to cart and wishlist |
| **Akandel · Categories** | *Template* (24, with previews) + *Parent Category* + *Heading Style* | Live shop categories with cover images and links (Website > eCommerce > Categories) |
| **Akandel · Offers** | *Offer Design* (24) | Image cards, coupons, deal of the day, color blocks... all texts, codes, images and links |
| **Akandel · Galleries** | *Gallery Design* (24) | Grid, masonry, bento, scroll strip, polaroid, collage... images and captions |

Headers, mobile menus and footers also offer **24 designs each** (see below).

### Design system
* Fonts: **Poppins** (headings) + **Roboto** (body) by default; Manrope, DM Sans,
  Inter, Outfit and the serif fonts Fraunces, Playfair Display and Cormorant
  Garamond remain selectable in the Theme tab.
* Default palette *Akandel Derma*: blue actions (#1570CC, AA contrast), gold
  highlights (#C48A1C), navy ink, soft grey surfaces. Wrap words in a heading
  with the highlight style (`<span class="ak-hl">`) to get the gold accent.

### Header (click the header)
* **Template**: 24 Akandel headers are listed after the Odoo ones, each with a
  preview (Essential, Centered Logo, Announcement Bar, Category Navigation,
  Promotion, Minimal Drawer, Split Menu, Floating Bar, Search First, Luxe, Bold,
  Utility Bar, Stacked, Pill Navigation, Transparent, Dark, Brand Color, Inline
  Search, Contact Strip, Category Chips, Boxed, Bold Caps, Two Buttons, Slim).
* **Mobile Style**: *Odoo default* plus 24 Akandel mobile navigations, e.g.
  *Refined drawer, Centered logo, Category drawer, Fullscreen overlay, Bottom
  sheet, Bottom tab bar, Persistent search, Compact, Promo strip, Dark drawer,
  Floating bar, Category chips*. It works with every desktop header.
* Standard options keep working: background color, content width, scroll effect,
  sub-menu behavior and the **Elements** toggles (search, text, social,
  language selector, sign in, call to action).
* Texts inside headers (announcement, promotion, tagline, utility links, call
  to action buttons) are edited inline.
* Category menus and chips are generated from **Website > eCommerce >
  Categories** (top-level categories that contain published products).

### Footer (click the footer)
* **Template**: 24 Akandel footers, listed after the Odoo ones (Columns,
  Newsletter Band, Centered, Minimal, Mega, Trust Signals, Statement, Contact,
  Split Brand, Payments, Gallery, Cards, App Download, Dark Columns, Big Brand,
  Two Tone, Support Cards, Newsletter Left, Wave, Link Grid, Social Band, Shop
  Categories, Compact Dark, Brand Call to Action).
* All texts, links, images and social icons are editable. Newsletter forms
  subscribe visitors to an Odoo mailing list (*Email Marketing* app).

### Other building blocks (Blocks panel)
Three more categories: **Akandel · Heroes & Promos**, **Akandel · Shop** and
**Akandel · Story & Trust**. That is 30 blocks you can drag, reorder, duplicate
and style (colors, spacing, background, columns, images, links):

| Category | Blocks |
|---|---|
| Heroes & promos | Split Hero, Cover Hero, Editorial Hero, Framed Hero, Campaign Banner, Promo Strip, Promo Marquee, Offer Tiles |
| Shop | Category Grid, Category Bento, Category Circles, New Arrivals*, Best Sellers*, Recently Viewed*, Product Spotlight, Collection Duo, Collection Trio, Shop the Look |
| Story & trust | Brand Story, Brand Values, Benefits Bar, Service Cards, Press Mentions, Reviews Grid, Feature Testimonial, Newsletter Band**, Newsletter Split**, Lookbook, Journal, Delivery & Returns |

\* Pre-configured instances of Odoo's native **Products** dynamic block
(newest, recently sold and recently viewed filters). Live products, prices,
ribbons, wishlist and add-to-cart come from Odoo, and the block keeps all its
native options.
\** Real `website_mass_mailing` subscription forms. Pick the mailing list in the
block options.

---

## 3. Shop page & add-to-cart experiences

### Shop page (Website Builder > click the product grid > *Akandel Shop Design*)
* **Shop Style**: *Odoo default* + 24 styles: Clean Cards, Minimal Grid, Soft
  Shadow, Bordered Catalog, Image Gallery, Boutique Centered, Dark Store, Pastel
  Tiles, Compact Dense, Magazine, Rounded Pills, Sidebar Panels, Filter Bar,
  Colored Header Band, Gold Luxe, Blue Accent, Outline Hover, Floating Toolbar,
  Zoom Focus, Tall Showcase, Lined List, Glass Cards, Gradient Header, Material
  Elevation. Styles only restyle Odoo's own product tile variables, so the
  native *Products Page* options (grid / list layout, columns, products per
  page, image size, card design, actions, ribbons, filters, sort) keep working
  with every style.
* **Banner**: None, Soft, Image cover (uses the category cover image),
  Split, Gradient. The title follows the page (category, search, shop) and the
  banner text is editable.
* **Promo Strip**, **Product Count**, **Sticky Toolbar** (stays below the
  site header), **Buttons on Hover**, **Sidebar Card**, **Trust Bar**
  (editable shipping / returns / payment reassurance).

### Add to cart (shop or product page > *Add to Cart Experience*)
* **Add to Cart Style**: *Odoo notification* + 24 experiences shown after
  "Add to cart":
  * side drawers: Side Drawer, Minimal, Left, Dark, Wide + Picks, Floating,
    Glass, Gold Accent, Compact, Drawer with Steps;
  * Bottom Sheet, Dark Bottom Sheet (become full-width sheets on phones);
  * modals: Centered, Split, Success; Fullscreen Overlay;
  * Mini Cart Dropdown (opens under the header cart icon), Top Bar slide-down;
  * notifications that hide after 5 s (paused on hover): Toast Card, Toast
    Bottom Left, Dark Snackbar, Floating Pill, Floating Mini Cart, Cart Bubble.
* Drawers, sheets, fullscreen and dropdown show the whole cart with
  quantity +/- and remove buttons; the other styles focus on the item just
  added. All show the subtotal (following the website tax display setting),
  *View cart* and *Checkout*.
* Options: **Cart Icon Opens Panel** (header cart icon opens the panel instead
  of the cart page), **Free Shipping Bar** with its **Threshold** amount,
  **Recommendations** (the products' *Accessory Products*).
* Accessible: dialog roles, Esc to close, focus kept in dialogs and restored on
  close, `aria-live` notifications, reduced-motion support. The cart and
  checkout pages keep Odoo's standard notification.
* Quantities change through Odoo's own `/shop/cart/update` route; the panel
  content is rendered by `/ak/cart_panel` (read only). Prices, taxes, cart
  rules and the "go to cart" setting stay standard.

## 4. eCommerce pages

Shop, category, search, product, cart, checkout (numbered step progress,
card-style address / delivery / payment choices), confirmation and portal
pages are restyled on top of Odoo's standard markup; every Odoo eCommerce
option still works. Template extensions are additive only:

* **Product page**: an editable "purchase assurance" block (delivery, returns,
  guarantee) under the add-to-cart area.
* **Shop**: friendlier empty / no-result states with recovery actions.
* **Cart**: friendlier empty-cart state with a wishlist shortcut.
* **Cart & checkout summaries**: an editable reassurance block (secure payment,
  shipping, returns).

Routes, controllers, pricing, cart updates (`/shop/cart/update_json`), checkout
steps, payment and order handling are untouched.

---

## 5. Module structure

```
theme_akandel/
├── __manifest__.py              # Theme/Retail module, assets, data files
├── controllers/main.py         # template pickers scoped to the current website,
│                                #   cart panel rendering, free shipping setting
├── models/
│   ├── theme_akandel.py         # theme.utils: post-copy defaults + homepage seeding
│   └── website.py               # category navigation, free shipping threshold
├── data/ir_asset.xml            # theme assets: primary variables & Bootstrap overrides
├── views/
│   ├── layout.xml               # theme marker + shared header components
│   ├── header/headers.xml       # 13 desktop headers
│   ├── header/mobile_headers.xml# 12 mobile navigations (+ tab bar layout)
│   ├── footer/footers.xml       # 12 footers
│   ├── snippets/*.xml           # 31 building blocks + registration + homepage
│   ├── sections/*.xml           # 5 families x 24 designs (generated, see below)
│   └── shop/
│       ├── shop_templates.xml   # additive eCommerce extensions
│       ├── shop_styles.xml      # 24 shop page styles (generated)
│       ├── cart_styles.xml      # 24 add-to-cart experiences (generated)
│       └── shop_options.xml     # banners, shop extras, cart options, cart panel
└── static/src/
    ├── scss/                    # design tokens, Bootstrap, header, footer, blocks, shop
    ├── builder/                 # Website Builder options (design pickers, category option)
    ├── interactions/            # live category sections, cart panel, sticky toolbar
    └── img/                     # builder previews & block thumbnails (SVG)
```

### Technical notes
* Module name starts with `theme_`, so Odoo stores the views as
  `theme.ir.ui.view` and copies them **per website** when the theme is applied.
  Other websites of the database are not affected.
* Header and footer variants follow the core contract (`website.layout` /
  `//header//nav` and `div#footer`) and reuse the core placeholders, so all
  native header and footer options stay functional.
* Mobile variants extend `website.template_header_mobile` additively. The
  cart and wishlist buttons injected by `website_sale` and
  `website_sale_wishlist` are kept.
* The builder extensions (`website.website_builder_assets`) use public Odoo 19
  APIs: OWL template inheritance of `website.HeaderTemplateOption`, a
  `BaseOptionComponent` using the `websiteConfig` action, and the
  `footer_templates_providers` resource. They only show up on websites using
  the theme (detected with the `o_ak_theme` class on `#wrapwrap`).
* Demo images come from Odoo's own `website` image library, so the theme ships
  no third-party photography. Replace them from the builder (double-click an
  image).

### Uninstall / switch theme
Switching to another theme from the theme chooser removes the Akandel views of
that website and restores Odoo's default header and footer. Homepage content
created from Akandel blocks stays as regular content.

### Regenerating the section families
`views/sections/*.xml`, `static/src/builder/akandel_section_designs.js` and
the preview thumbnails are generated. To add or rename designs, edit
`tools/gen_sections.py`, then run (Python 3.9+, no dependencies):

```bash
python3 tools/gen_sections.py . && python3 tools/gen_thumbs_sections.py .
```

and add the matching `.ak-hs-* / .ak-pc-* / .ak-cc-* / .ak-of-* / .ak-ga-*`
styles in `static/src/scss/sections/`. Upgrade the module afterwards.

Shop styles and add-to-cart experiences are generated the same way by
`tools/gen_shop_cart.py` (`views/shop/shop_styles.xml`,
`views/shop/cart_styles.xml`, `static/src/builder/akandel_shop_designs.js`);
their styles live in `scss/sections/shop_styles.scss` and
`scss/sections/cart_panel.scss`.
