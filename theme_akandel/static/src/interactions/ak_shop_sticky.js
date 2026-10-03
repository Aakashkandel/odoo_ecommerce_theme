import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/**
 * Shop "Sticky Toolbar" option: keeps the toolbar below the site header when
 * the header is fixed (any scroll effect), using its real visible height.
 */
export class AkandelShopStickyToolbar extends Interaction {
    static selector = "#o_wsale_container.ak-shop-sticky-tools";

    setup() {
        this.frame = null;
        this.header = document.querySelector("header#top");
    }

    start() {
        this.update();
        this.addListener(window, "scroll", this.schedule, { passive: true });
        this.addListener(window, "resize", this.schedule, { passive: true });
        if (this.header) {
            // Scroll effects slide the header in and out after scrolling.
            this.addListener(this.header, "transitionend", this.schedule);
        }
    }

    destroy() {
        cancelAnimationFrame(this.frame);
        this.el.style.removeProperty("--ak-sticky-top");
    }

    schedule() {
        cancelAnimationFrame(this.frame);
        this.frame = requestAnimationFrame(() => this.update());
    }

    update() {
        const header = this.header;
        let offset = 0;
        if (header && getComputedStyle(header).position === "fixed") {
            offset = Math.max(header.getBoundingClientRect().bottom, 0);
        }
        this.el.style.setProperty("--ak-sticky-top", `${Math.round(offset + 12)}px`);
    }
}

registry.category("public.interactions").add("theme_akandel.shop_sticky_toolbar", AkandelShopStickyToolbar);
