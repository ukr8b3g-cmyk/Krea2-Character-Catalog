import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "Krea2.CatalogPromptFile",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "Krea2CatalogPromptFile") return;
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            const control = this.widgets?.find((widget) => widget.name === "control_after_generate");
            if (control) control.value = "increment";
            return result;
        };
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);
            if (!this.catalogPreview) {
                this.catalogPreview = ComfyWidgets.STRING(
                    this, "selected_record", ["STRING", { multiline: true }], app
                ).widget;
                this.catalogPreview.inputEl.readOnly = true;
                this.catalogPreview.options.serialize = false;
                this.catalogPreview.serializeValue = () => undefined;
            }
            this.catalogPreview.value = (message.text ?? []).join("\n");
            const size = this.computeSize();
            size[0] = Math.max(size[0], this.size[0]);
            size[1] = Math.max(size[1], this.size[1]);
            this.setSize(size);
            app.graph.setDirtyCanvas(true, false);
        };
    },
});
