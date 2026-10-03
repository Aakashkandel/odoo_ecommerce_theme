import { onWillStart, useState } from "@odoo/owl";
import { BaseOptionComponent } from "@html_builder/core/utils";
import { SNIPPET_SPECIFIC_BEFORE } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useDynamicSnippetOption } from "@website/builder/plugins/options/dynamic_snippet_hook";
import { DYNAMIC_SNIPPET } from "@website/builder/plugins/options/dynamic_snippet_option_plugin";
import { AKANDEL_SECTION_DESIGNS } from "./akandel_section_designs";

/**
 * Generic "Design" picker: switches the design class of an Akandel section
 * family. All designs of a family share the same markup, so the content the
 * store owner edited is kept when another design is selected.
 */
export class AkandelDesignOption extends BaseOptionComponent {
    static template = "theme_akandel.DesignOption";
    static designs = [];
    static designLabel = "";

    setup() {
        super.setup();
        this.designs = this.constructor.designs;
        this.designLabel = this.constructor.designLabel;
    }
}

function designOption(selector, designs, designLabel) {
    return class extends AkandelDesignOption {
        static selector = selector;
        static designs = designs;
        static designLabel = designLabel;
    };
}

const HeroDesignOption = designOption(".s_ak_hero_slider", AKANDEL_SECTION_DESIGNS.hero, _t("Slider Design"));
const OfferDesignOption = designOption(".s_ak_offers", AKANDEL_SECTION_DESIGNS.offers, _t("Offer Design"));
const GalleryDesignOption = designOption(".s_ak_gallery", AKANDEL_SECTION_DESIGNS.gallery, _t("Gallery Design"));
const HeadingStyleOption = designOption(
    ".s_ak_products, .s_ak_categories",
    AKANDEL_SECTION_DESIGNS.heading,
    _t("Heading Style")
);

/**
 * Category sections: Odoo's dynamic snippet options (template picker with
 * previews, number of categories) restricted to shop categories, plus a
 * "Parent category" filter (shows its sub-categories).
 */
export class AkandelCategoriesOption extends BaseOptionComponent {
    static template = "theme_akandel.CategoriesOption";
    static dependencies = ["dynamicSnippetOption"];
    static selector = ".s_ak_categories";

    setup() {
        super.setup();
        this.dynamicOptionParams = useDynamicSnippetOption("product.public.category");
        this.state = useState({ categories: [] });
        onWillStart(async () => {
            const websiteId = this.services.website.currentWebsite.id;
            this.state.categories = await this.services.orm.searchRead(
                "product.public.category",
                [["child_id", "!=", false], "|", ["website_id", "=", false], ["website_id", "=", websiteId]],
                ["id", "display_name"],
                { order: "sequence, name" }
            );
        });
    }
}

export class AkandelSectionsPlugin extends Plugin {
    static id = "akandelSections";
    static dependencies = ["dynamicSnippetOption"];

    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [
            withSequence(SNIPPET_SPECIFIC_BEFORE, HeroDesignOption),
            withSequence(SNIPPET_SPECIFIC_BEFORE, OfferDesignOption),
            withSequence(SNIPPET_SPECIFIC_BEFORE, GalleryDesignOption),
            withSequence(SNIPPET_SPECIFIC_BEFORE, HeadingStyleOption),
            withSequence(DYNAMIC_SNIPPET, AkandelCategoriesOption),
        ],
        on_snippet_dropped_handlers: this.onSnippetDropped.bind(this),
    };

    async onSnippetDropped({ snippetEl }) {
        if (snippetEl.matches(AkandelCategoriesOption.selector)) {
            await this.dependencies.dynamicSnippetOption.setOptionsDefaultValues(
                snippetEl,
                "product.public.category"
            );
        }
    }
}

registry.category("website-plugins").add(AkandelSectionsPlugin.id, AkandelSectionsPlugin);
