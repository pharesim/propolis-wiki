import type { Context } from '@toast-ui/toastmark';
import type { PluginContext, PluginInfo, HTMLMdNode, I18n } from '@toast-ui/editor';
import type { Transaction, Selection, TextSelection } from 'prosemirror-state';
import { PluginOptions } from '@t/index';

import './css/plugin.css';

function createInput() {
    const form = document.createElement("form");
    form.innerHTML = "<input class='reference-link' type='text' /><input class='reference-text' type='text' />";
    return form;
}
  
function createToolbarItemOption(dropDown: HTMLDivElement) {
    return {
        name: "reference",
        text: "REF",
        tooltip: "Reference",
        style: { background: "none", fontSize: "20px" },
        popup: {
            body: dropDown,
            style: { width: "100px", maxHeight: "200px", overflow: "auto" },
        },
    };
}

function createSelection(
    tr: Transaction,
    selection: Selection,
    SelectionClass: typeof TextSelection,
    openTag: string,
    closeTag: string
) {
    const { mapping, doc } = tr;
    const { from, to, empty } = selection;
    const mappedFrom = mapping.map(from) + openTag.length;
    const mappedTo = mapping.map(to) - closeTag.length;
  
    return empty
        ? SelectionClass.create(doc, mappedTo, mappedTo)
        : SelectionClass.create(doc, mappedFrom, mappedTo);
}

const getSpanAttrs = (selection: Selection) => {
    const slice = selection.content();
    let attrs: Attr = {
        htmlAttrs: null,
        htmlInline: null,
        classNames: null,
    };
    slice.content.nodesBetween(0, slice.content.size, (node: any) => {
        if (node.marks.length > 0) {
            node.marks.forEach((mark: Mark) => {
                if (mark.type.name === "span") {
                    attrs = mark.attrs;
                }
            });
        }
    });
    return attrs;
};
  
function hasClass(element: HTMLElement, className: string) {
    return element.classList.contains(className);
}

export function findParentByClassName(el: HTMLElement, className: string) {
    let currentEl: HTMLElement | null = el;
  
    while (currentEl && !hasClass(currentEl, className)) {
        currentEl = currentEl.parentElement;
    }
  
    return currentEl;
}
  
function getCurrentEditorEl(
    referenceEl: HTMLElement,
    containerClassName: string
) {
    const editorDefaultEl = findParentByClassName(
        referenceEl,
        `toastui-editor-defaultUI`
    )!;
  
    return editorDefaultEl.querySelector<HTMLElement>(
        `.${containerClassName} .ProseMirror`
    )!;
}
  
let containerClassName: string;
let currentEditorEl: HTMLElement;

export default function referencePlugin(
    context: PluginContext,
    options: PluginOptions = {}
): PluginInfo {
    const { eventEmitter, pmState } = context;
  
    eventEmitter.listen("focus", (editType) => {
        containerClassName = `toastui-editor-${editType === "markdown" ? "md" : "ww"}-container`;
    });
  
    const container = document.createElement("div");
  
    const inputForm = createInput();
  
    inputForm.onsubmit = (ev) => {
        ev.preventDefault();
        const input_link = inputForm.querySelector(".reference-link") as HTMLInputElement;
        const input_text = inputForm.querySelector(".reference-text") as HTMLInputElement;
        currentEditorEl = getCurrentEditorEl(container, containerClassName);
  
        eventEmitter.emit("command", "reference", {
            link: input_link.value,
            text: input_text.value,
        });
        eventEmitter.emit("closePopup");
  
        currentEditorEl.focus();
    };
  
    container.appendChild(inputForm);
  
    const toolbarItem = createToolbarItemOption(container);
  
    return {
        markdownCommands: {
            reference: ({ reference }, { tr, selection, schema }, dispatch) => {
                if (reference) {
                    const slice = selection.content();
                    const textContent = slice.content.textBetween(
                        0,
                        slice.content.size,
                        "\n"
                    );
  
                    const openTag = `<ref>`;
                    const closeTag = `</ref>`;
                    const referenced = `${openTag}${textContent}${closeTag}`;
  
                    tr.replaceSelectionWith(schema.text(referenced)).setSelection(
                        createSelection(
                            tr,
                            selection,
                            pmState.TextSelection,
                            openTag,
                            closeTag
                        )
                    );
  
                    dispatch!(tr);
  
                    return true;
                }
                return false;
            },
        },
        wysiwygCommands: {
            reference: ({ reference }, { tr, selection, schema }, dispatch) => {
                if (reference) {
                    const { from, to } = selection;
  
                    const mark = schema.marks.p.create();
  
                    tr.addMark(from, to, mark);
                    dispatch!(tr);
  
                    return true;
                }
                return false;
            },
        },
        toolbarItems: [
            {
                groupIndex: 0,
                itemIndex: 0,
                item: toolbarItem,
            },
        ],
        toHTMLRenderers: {
            htmlInline: {
                p(node: HTMLMdNode, { entering }: Context) {
                    return entering
                    ? {
                        type: "openTag",
                        tagName: "ref",
                    }
                    : { type: "closeTag", tagName: "ref" };
                },
            },
        },
    };
}