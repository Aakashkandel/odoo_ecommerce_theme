import { browser } from "@web/core/browser/browser";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { Interaction } from "@web/public/interaction";
import { CartService } from "@website_sale/js/cart_service";

/**
 * Akandel add-to-cart experiences.
 *
 * The active style is set by a theme view on `#wrapwrap`
 * (`data-ak-cart-style`, `data-ak-cart-type`, `data-ak-cart-mode`). When a
 * product is added through Odoo's cart service, the Akandel panel (drawer,
 * bottom sheet, modal, toast...) replaces the default notification. Adding,
 * updating and removing lines still go through Odoo's own `/shop/cart/*`
 * routes.
 */

const DIALOG_TYPES = new Set(["drawer-right", "drawer-left", "sheet", "modal", "fullscreen"]);
const AUTO_HIDE_TYPES = new Set(["toast-tr", "toast-bl", "toast-bc", "topbar", "floating"]);
const AUTO_HIDE_DELAY = 5000;
const SKIPPED_PATHS = /^(\/[a-z]{2}(_[A-Za-z]{2,4})?)?\/shop\/(cart|checkout|address|payment|confirmation|extra_info)/;

export function getAkCartConfig() {
    const wrap = document.getElementById("wrapwrap");
    if (!wrap?.dataset.akCartStyle || SKIPPED_PATHS.test(window.location.pathname)) {
        return null;
    }
    return {
        style: wrap.dataset.akCartStyle,
        type: wrap.dataset.akCartType || "drawer-right",
        mode: wrap.dataset.akCartMode || "full",
    };
}

function updateCartBadges(cartQuantity) {
    browser.sessionStorage.setItem("website_sale_cart_quantity", cartQuantity);
    for (const el of document.querySelectorAll(".my_cart_quantity")) {
        el.classList.toggle("d-none", !cartQuantity);
        el.textContent = cartQuantity;
    }
    if (cartQuantity) {
        document.querySelector("li.o_wsale_my_cart")?.classList.remove("d-none");
    }
}

class AkCartPanel {
    constructor() {
        this.root = null;
        this.panel = null;
        this.config = null;
        this.state = { mode: "full", addedLineIds: [] };
        this.hideTimer = null;
        this.lastFocus = null;
        this.busy = false;
        this.onKeydown = this.onKeydown.bind(this);
    }

    get isDialog() {
        return DIALOG_TYPES.has(this.config?.type);
    }

    /**
     * @param {Object} params
     * @param {"full"|"added"} [params.mode]
     * @param {number[]} [params.addedLineIds]
     * @returns {Promise<boolean>} false when the panel could not be rendered
     */
    async open({ mode, addedLineIds = [] } = {}) {
        const config = getAkCartConfig();
        if (!config) {
            return false;
        }
        this.config = config;
        this.state = { mode: mode || config.mode, addedLineIds };
        const showFirst = !AUTO_HIDE_TYPES.has(config.type);
        this.build();
        if (showFirst) {
            this.show();
        }
        const ok = await this.refresh();
        if (!ok) {
            this.close(true);
            return false;
        }
        if (!showFirst) {
            this.show();
        }
        return true;
    }

    build() {
        const { type, style } = this.config;
        if (this.root?.dataset.akKey !== `${type}:${style}`) {
            this.root?.remove();
            this.root = document.createElement("div");
            this.root.dataset.akKey = `${type}:${style}`;
            this.root.innerHTML = `<div class="ak-cp-backdrop"></div><div class="ak-cp-panel" tabindex="-1"></div>`;
            this.panel = this.root.querySelector(".ak-cp-panel");
            this.root.addEventListener("click", (ev) => this.onClick(ev));
            this.root.addEventListener("mouseenter", () => this.clearHideTimer());
            this.root.addEventListener("mouseleave", () => this.startHideTimer());
            this.root.addEventListener("focusin", () => this.clearHideTimer());
            document.body.appendChild(this.root);
        }
        this.root.className = `ak-cp-root ak-cp--${type} ak-cp-s-${style}`;
        if (this.isDialog) {
            this.panel.setAttribute("role", "dialog");
            this.panel.setAttribute("aria-modal", "true");
            this.panel.setAttribute("aria-labelledby", "ak_cp_title");
            this.panel.removeAttribute("aria-live");
        } else {
            this.panel.setAttribute("role", type === "dropdown" ? "dialog" : "status");
            this.panel.setAttribute("aria-live", "polite");
            this.panel.removeAttribute("aria-modal");
        }
        if (!this.root.classList.contains("is-open")) {
            this.panel.innerHTML = `<div class="ak-cp-loading" aria-hidden="true"><span></span><span></span><span></span></div>`;
        }
        if (type === "dropdown") {
            this.positionDropdown();
        }
    }

    positionDropdown() {
        const icons = [...document.querySelectorAll("header .o_wsale_my_cart a, header a[href$='/shop/cart']")];
        const icon = icons.find((el) => el.offsetParent !== null);
        if (!icon) {
            this.panel.style.removeProperty("--ak-cp-top");
            this.panel.style.removeProperty("--ak-cp-right");
            return;
        }
        const rect = icon.getBoundingClientRect();
        this.panel.style.setProperty("--ak-cp-top", `${Math.max(rect.bottom + 10, 12)}px`);
        this.panel.style.setProperty("--ak-cp-right", `${Math.max(window.innerWidth - rect.right - 12, 12)}px`);
    }

    async refresh() {
        let result;
        try {
            result = await rpc("/ak/cart_panel", {
                mode: this.state.mode,
                added_line_ids: this.state.addedLineIds,
            });
        } catch {
            return false;
        }
        if (!result?.html || !this.root) {
            return false;
        }
        this.panel.innerHTML = result.html;
        updateCartBadges(result.cart_quantity || 0);
        return true;
    }

    show() {
        this.clearHideTimer();
        if (!this.root.classList.contains("is-open")) {
            this.lastFocus = document.activeElement;
            // Next frame so that the opening transition runs.
            requestAnimationFrame(() => requestAnimationFrame(() => this.root?.classList.add("is-open")));
            document.addEventListener("keydown", this.onKeydown);
            if (this.isDialog) {
                document.documentElement.classList.add("ak-cp-lock");
            }
        }
        if (this.isDialog || this.config.type === "dropdown") {
            setTimeout(() => this.panel?.focus({ preventScroll: true }), 60);
        }
        this.startHideTimer();
    }

    close(immediate = false) {
        this.clearHideTimer();
        document.removeEventListener("keydown", this.onKeydown);
        document.documentElement.classList.remove("ak-cp-lock");
        if (!this.root) {
            return;
        }
        const root = this.root;
        root.classList.remove("is-open");
        if (immediate) {
            root.remove();
            this.root = null;
        }
        if (this.lastFocus?.isConnected) {
            this.lastFocus.focus({ preventScroll: true });
        }
        this.lastFocus = null;
    }

    startHideTimer() {
        this.clearHideTimer();
        if (this.root && AUTO_HIDE_TYPES.has(this.config?.type)) {
            this.hideTimer = setTimeout(() => this.close(), AUTO_HIDE_DELAY);
        }
    }

    clearHideTimer() {
        clearTimeout(this.hideTimer);
        this.hideTimer = null;
    }

    onKeydown(ev) {
        if (ev.key === "Escape") {
            this.close();
            return;
        }
        if (ev.key !== "Tab" || !this.isDialog || !this.root?.classList.contains("is-open")) {
            return;
        }
        // Keep the keyboard focus inside the dialog.
        const focusables = [...this.panel.querySelectorAll("a[href], button:not([disabled])")].filter(
            (el) => el.offsetParent !== null
        );
        if (!focusables.length) {
            return;
        }
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (ev.shiftKey && (document.activeElement === first || document.activeElement === this.panel)) {
            ev.preventDefault();
            last.focus();
        } else if (!ev.shiftKey && document.activeElement === last) {
            ev.preventDefault();
            first.focus();
        }
    }

    onClick(ev) {
        const target = ev.target;
        if (target.closest(".ak-cp-backdrop, .ak-cp-close, .ak-cp-continue")) {
            ev.preventDefault();
            this.close();
            return;
        }
        const qtyBtn = target.closest("[data-ak-qty]");
        if (qtyBtn) {
            ev.preventDefault();
            this.updateQuantity(qtyBtn);
        }
    }

    async updateQuantity(button) {
        const lineEl = button.closest(".ak-cp-line");
        if (!lineEl || this.busy) {
            return;
        }
        const delta = parseInt(button.dataset.akQty);
        const current = parseInt(lineEl.querySelector(".ak-cp-qty-val")?.textContent || "0");
        const quantity = delta === 0 ? 0 : Math.max(current + delta, 0);
        this.busy = true;
        lineEl.classList.add("is-busy");
        try {
            await rpc("/shop/cart/update", {
                line_id: parseInt(lineEl.dataset.lineId),
                product_id: parseInt(lineEl.dataset.productId),
                quantity,
            });
            await this.refresh();
        } catch {
            lineEl.classList.remove("is-busy");
        } finally {
            this.busy = false;
        }
    }
}

export const akCartPanel = new AkCartPanel();

patch(CartService.prototype, {
    _showCartNotification(props, options = {}) {
        const config = getAkCartConfig();
        if (!config || !props?.lines?.length) {
            return super._showCartNotification(props, options);
        }
        const fallback = () =>
            super._showCartNotification({ lines: props.lines, currency_id: props.currency_id }, options);
        akCartPanel
            .open({ addedLineIds: props.lines.map((line) => line.id) })
            .then((ok) => !ok && fallback())
            .catch(fallback);
        if (props.warning) {
            super._showCartNotification({ warning: props.warning }, options);
        }
    },
});

/**
 * Optional: the header cart icon opens the full cart panel instead of the
 * cart page (Website Builder > "Cart Icon Opens Panel").
 */
export class AkandelCartIcon extends Interaction {
    static selector = "#wrapwrap[data-ak-cart-style][data-ak-cart-icon] > header";
    dynamicContent = {
        ".o_wsale_my_cart a, a[href$='/shop/cart']": {
            "t-on-click": this.onCartIconClick,
        },
    };

    onCartIconClick(ev) {
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button !== 0 || !getAkCartConfig()) {
            return;
        }
        const href = ev.currentTarget.href || "/shop/cart";
        ev.preventDefault();
        akCartPanel.open({ mode: "full" }).then((ok) => {
            if (!ok) {
                window.location.href = href;
            }
        });
    }
}

registry.category("public.interactions").add("theme_akandel.cart_icon", AkandelCartIcon);
