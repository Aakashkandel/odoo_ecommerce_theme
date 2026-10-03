import { registry } from "@web/core/registry";
import { DynamicSnippet } from "@website/snippets/s_dynamic_snippet/dynamic_snippet";

/**
 * Akandel category sections: Odoo's dynamic snippet fed by website_sale's
 * "Category List" data source, rendered with the Akandel category templates.
 */
export class AkandelDynamicCategories extends DynamicSnippet {
    static selector = ".s_ak_categories";

    getRpcParameters() {
        const parentId = parseInt(this.el.dataset.parentCategoryId);
        return Object.assign(super.getRpcParameters(), parentId ? { parentId } : {});
    }
}

registry
    .category("public.interactions")
    .add("theme_akandel.dynamic_categories", AkandelDynamicCategories);

registry
    .category("public.interactions.edit")
    .add("theme_akandel.dynamic_categories", { Interaction: AkandelDynamicCategories });
