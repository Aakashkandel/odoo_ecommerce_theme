import { _t } from "@web/core/l10n/translation";

/**
 * Single source of truth for the Akandel header / mobile / footer variants
 * exposed in the Website Builder. Keys must match the views defined in
 * views/header/*.xml and views/footer/footers.xml.
 */
const IMG = "/theme_akandel/static/src/img/builder";

export const AKANDEL_HEADERS = [
    { key: "essential", title: _t("Akandel · Essential") },
    { key: "centered", title: _t("Akandel · Centered Logo") },
    { key: "announce", title: _t("Akandel · Announcement Bar") },
    { key: "category", title: _t("Akandel · Category Navigation") },
    { key: "promo", title: _t("Akandel · Promotion") },
    { key: "minimal", title: _t("Akandel · Minimal Drawer"), extraViews: ["website.no_autohide_menu"] },
    { key: "split", title: _t("Akandel · Split Menu") },
    { key: "floating", title: _t("Akandel · Floating Bar") },
    { key: "search", title: _t("Akandel · Search First") },
    { key: "luxe", title: _t("Akandel · Luxe") },
    { key: "bold", title: _t("Akandel · Bold") },
    { key: "utility", title: _t("Akandel · Utility Bar") },
    { key: "stacked", title: _t("Akandel · Stacked") },
    { key: "pill", title: _t("Akandel · Pill Navigation") },
    { key: "transparent", title: _t("Akandel · Transparent") },
    { key: "dark", title: _t("Akandel · Dark") },
    { key: "brand", title: _t("Akandel · Brand Color") },
    { key: "searchpill", title: _t("Akandel · Inline Search") },
    { key: "contact", title: _t("Akandel · Contact Strip") },
    { key: "chips", title: _t("Akandel · Category Chips") },
    { key: "boxed", title: _t("Akandel · Boxed") },
    { key: "caps", title: _t("Akandel · Bold Caps") },
    { key: "duo", title: _t("Akandel · Two Buttons") },
    { key: "slim", title: _t("Akandel · Slim") },
].map((header) => ({
    ...header,
    id: `ak_header_${header.key}_opt`,
    views: [`theme_akandel.template_header_ak_${header.key}`, ...(header.extraViews || [])],
    varName: `ak_${header.key}`,
    imgSrc: `${IMG}/header_${header.key}.svg`,
}));

export const AKANDEL_MOBILE_STYLES = [
    { key: "refined", title: _t("Refined drawer") },
    { key: "centered", title: _t("Centered logo") },
    { key: "drawer", title: _t("Category drawer") },
    { key: "fullscreen", title: _t("Fullscreen overlay") },
    { key: "sheet", title: _t("Bottom sheet") },
    { key: "tabbar", title: _t("Bottom tab bar"), extraViews: ["theme_akandel.ak_mobile_tabbar_layout"] },
    { key: "search", title: _t("Persistent search") },
    { key: "compact", title: _t("Compact") },
    { key: "promo", title: _t("Promo strip") },
    { key: "dark", title: _t("Dark drawer") },
    { key: "floating", title: _t("Floating bar") },
    { key: "chips", title: _t("Category chips") },
    { key: "brand", title: _t("Brand color bar") },
    { key: "darkbar", title: _t("Dark bar") },
    { key: "glass", title: _t("Frosted glass") },
    { key: "bordered", title: _t("Accent border") },
    { key: "gold", title: _t("Gold accent") },
    { key: "rounded", title: _t("Rounded drawer") },
    { key: "bigtype", title: _t("Big type drawer") },
    { key: "iconpills", title: _t("Icon pills") },
    { key: "leftdark", title: _t("Dark left drawer") },
    { key: "sheetdark", title: _t("Dark bottom sheet") },
    { key: "cards", title: _t("Card menu") },
    { key: "clean", title: _t("Clean minimal") },
].map((style) => ({
    ...style,
    id: `ak_mobile_${style.key}_opt`,
    views: [`theme_akandel.template_header_mobile_ak_${style.key}`, ...(style.extraViews || [])],
    imgSrc: `${IMG}/mobile_${style.key}.svg`,
}));

export const AKANDEL_FOOTERS = [
    { key: "columns", title: _t("Akandel · Columns") },
    { key: "newsletter", title: _t("Akandel · Newsletter Band") },
    { key: "centered", title: _t("Akandel · Centered") },
    { key: "minimal", title: _t("Akandel · Minimal") },
    { key: "mega", title: _t("Akandel · Mega") },
    { key: "trust", title: _t("Akandel · Trust Signals") },
    { key: "statement", title: _t("Akandel · Statement") },
    { key: "contact", title: _t("Akandel · Contact & Showroom") },
    { key: "split", title: _t("Akandel · Split Brand") },
    { key: "payments", title: _t("Akandel · Payments") },
    { key: "gallery", title: _t("Akandel · Gallery") },
    { key: "cards", title: _t("Akandel · Cards") },
    { key: "app", title: _t("Akandel · App Download") },
    { key: "darkcols", title: _t("Akandel · Dark Columns") },
    { key: "bigbrand", title: _t("Akandel · Big Brand") },
    { key: "twotone", title: _t("Akandel · Two Tone") },
    { key: "support", title: _t("Akandel · Support Cards") },
    { key: "newsleft", title: _t("Akandel · Newsletter Left") },
    { key: "wave", title: _t("Akandel · Wave") },
    { key: "linkgrid", title: _t("Akandel · Link Grid") },
    { key: "socialband", title: _t("Akandel · Social Band") },
    { key: "categories", title: _t("Akandel · Shop Categories") },
    { key: "compactdark", title: _t("Akandel · Compact Dark") },
    { key: "brandcta", title: _t("Akandel · Brand Call to Action") },
].map((footer) => ({
    ...footer,
    view: `theme_akandel.template_footer_ak_${footer.key}`,
    varName: `ak_${footer.key}`,
    imgSrc: `${IMG}/footer_${footer.key}.svg`,
}));

/**
 * The Akandel views only exist on websites using the theme; the layout marks
 * those websites with the `o_ak_theme` class on #wrapwrap.
 *
 * @param {HTMLElement} editable the builder editable (#wrapwrap)
 */
export function isAkandelWebsite(editable) {
    return !!editable?.classList?.contains("o_ak_theme");
}
