import { BaseOptionComponent } from "@html_builder/core/utils";
import { BuilderAction } from "@html_builder/core/builder_action";
import { Plugin } from "@html_editor/plugin";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { AKANDEL_SHOP_DESIGNS } from "./akandel_shop_designs";

const THEMED = "#wrapwrap.o_ak_theme";

export const AKANDEL_SHOP_BANNERS = [
    { id: "ak_shop_banner_simple_opt", title: _t("Soft"), view: "theme_akandel.ak_shop_banner_simple" },
    { id: "ak_shop_banner_image_opt", title: _t("Image cover"), view: "theme_akandel.ak_shop_banner_image" },
    { id: "ak_shop_banner_split_opt", title: _t("Split"), view: "theme_akandel.ak_shop_banner_split" },
    { id: "ak_shop_banner_gradient_opt", title: _t("Gradient"), view: "theme_akandel.ak_shop_banner_gradient" },
];

/**
 * Products Page > Akandel Shop: page style (24), banner and extra elements.
 * Every choice is a theme view toggled with the `websiteConfig` action.
 */
export class AkandelShopOption extends BaseOptionComponent {
    static template = "theme_akandel.ShopOption";
    static selector = `${THEMED} main:has(#o_wsale_container)`;
    static applyTo = "#o_wsale_container";
    static title = _t("Akandel Shop Design");
    static groups = ["website.group_website_designer"];
    static editableOnly = false;

    setup() {
        super.setup();
        this.shopStyles = AKANDEL_SHOP_DESIGNS.shop.map((style) => ({ ...style, id: `ak_shop_${style.key}_opt` }));
        this.banners = AKANDEL_SHOP_BANNERS;
    }
}

/**
 * Shop and product pages > Add to Cart Experience: what visitors see after
 * clicking "Add to cart" (drawer, sheet, modal, toast...).
 */
export class AkandelCartOption extends BaseOptionComponent {
    static template = "theme_akandel.CartOption";
    static selector = `${THEMED} main:has(#o_wsale_container), ${THEMED} main:has(.o_wsale_product_page)`;
    static title = _t("Add to Cart Experience");
    static groups = ["website.group_website_designer"];
    static editableOnly = false;

    setup() {
        super.setup();
        this.cartStyles = AKANDEL_SHOP_DESIGNS.cart.map((style) => ({ ...style, id: `ak_cart_${style.key}_opt` }));
    }
}

export class AkFreeShippingAction extends BuilderAction {
    static id = "akFreeShipping";
    setup() {
        this.reload = {};
    }
    getValue() {
        return this.document.getElementById("wrapwrap")?.dataset.akFreeship || "50";
    }
    apply({ value }) {
        const amount = Math.max(parseFloat(value) || 0, 0);
        return rpc("/ak/config/website", { ak_free_shipping_threshold: amount });
    }
}

export class AkandelShopPlugin extends Plugin {
    static id = "akandelShop";

    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [AkandelShopOption, AkandelCartOption],
        builder_actions: { AkFreeShippingAction },
    };
}

registry.category("website-plugins").add(AkandelShopPlugin.id, AkandelShopPlugin);
