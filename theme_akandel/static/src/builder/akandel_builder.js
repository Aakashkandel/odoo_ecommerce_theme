import { BaseOptionComponent } from "@html_builder/core/utils";
import { between } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import {
    HEADER_ELEMENTS,
    HEADER_NAVIGATION,
} from "@website/builder/plugins/options/header/header_option_plugin";
import { HeaderTemplateOption } from "@website/builder/plugins/options/header/header_template_option";
import { FooterTemplateChoice } from "@website/builder/plugins/options/footer_template_option";
import {
    AKANDEL_FOOTERS,
    AKANDEL_HEADERS,
    AKANDEL_MOBILE_STYLES,
    isAkandelWebsite,
} from "./akandel_variants";

/**
 * Header > Template: append the Akandel desktop headers to the native picker.
 * Selecting any item (core or Akandel) disables all the others, as the picker
 * relies on the `websiteConfig` action of the Website Builder.
 */
patch(HeaderTemplateOption.prototype, {
    setup() {
        super.setup(...arguments);
        this.akandelHeaders = isAkandelWebsite(this.editable) ? AKANDEL_HEADERS : [];
    },
});

/**
 * Header > Mobile Style: choose one of the Akandel mobile navigation variants
 * (or keep Odoo's default mobile header).
 */
export class AkandelMobileStyleOption extends BaseOptionComponent {
    static template = "theme_akandel.MobileStyleOption";
    static selector = "#wrapwrap > header";
    static editableOnly = false;
    static groups = ["website.group_website_designer"];

    setup() {
        super.setup();
        this.akandelMobileStyles = isAkandelWebsite(this.editable) ? AKANDEL_MOBILE_STYLES : [];
    }
}

export class AkandelBuilderPlugin extends Plugin {
    static id = "akandelBuilder";

    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [withSequence(between(HEADER_NAVIGATION, HEADER_ELEMENTS), AkandelMobileStyleOption)],
        footer_templates_providers: [() => this.getFooterTemplates()],
    };

    getFooterTemplates() {
        if (!isAkandelWebsite(this.editable)) {
            return [];
        }
        return AKANDEL_FOOTERS.map((footer) => ({
            key: `akandel_${footer.key}`,
            Component: FooterTemplateChoice,
            props: {
                title: footer.title,
                view: footer.view,
                varName: footer.varName,
                imgSrc: footer.imgSrc,
            },
        }));
    }
}

registry.category("website-plugins").add(AkandelBuilderPlugin.id, AkandelBuilderPlugin);
