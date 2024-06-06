/*!
 * TOAST UI Editor : Wiki Link Plugin
 * @version 1.0.0 | Monday May 27th 2024
 * @author
 * @license ISC
 */
(function webpackUniversalModuleDefinition(root, factory) {
	if(typeof exports === 'object' && typeof module === 'object')
		module.exports = factory();
	else if(typeof define === 'function' && define.amd)
		define([], factory);
	else if(typeof exports === 'object')
		exports["toastui"] = factory();
	else
		root["toastui"] = root["toastui"] || {}, root["toastui"]["Editor"] = root["toastui"]["Editor"] || {}, root["toastui"]["Editor"]["plugin"] = root["toastui"]["Editor"]["plugin"] || {}, root["toastui"]["Editor"]["plugin"]["wikiLink"] = factory();
})(self, function() {
return /******/ (function() { // webpackBootstrap
/******/ 	"use strict";
/******/ 	// The require scope
/******/ 	var __webpack_require__ = {};
/******/
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	!function() {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = function(exports, definition) {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	}();
/******/
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	!function() {
/******/ 		__webpack_require__.o = function(obj, prop) { return Object.prototype.hasOwnProperty.call(obj, prop); }
/******/ 	}();
/******/
/************************************************************************/
var __webpack_exports__ = {};
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": function() { return /* binding */ wikiLinkPlugin; }
/* harmony export */ });
/* unused harmony export findParentByClassName */

function createInput() {
    var form = document.createElement("form");
    form.innerHTML = "<input class='wiki-link-input' id='wiki-link-input-link' type='text' placeholder='Link' />";
    form.innerHTML += "<input type='submit' value='submit' />";
    return form;
}
function createToolbarItemOption(element) {
    var wikiLinkCustomEl = document.createElement('button');
    wikiLinkCustomEl.className = 'toastui-editor-toolbar-icons link wikiLink';
    return {
        name: "wikiLink",
        tooltip: "Wiki Link",
        el: wikiLinkCustomEl,
        popup: {
            body: element,
            style: { width: "auto" },
        },
    };
}
function createSelection(tr, selection, SelectionClass, openTag, closeTag) {
    var mapping = tr.mapping, doc = tr.doc;
    var from = selection.from, to = selection.to, empty = selection.empty;
    var mappedFrom = mapping.map(from) + openTag.length;
    var mappedTo = mapping.map(to) - closeTag.length;
    return empty
        ? SelectionClass.create(doc, mappedTo, mappedTo)
        : SelectionClass.create(doc, mappedFrom, mappedTo);
}
function hasClass(element, className) {
    return element.classList.contains(className);
}
function findParentByClassName(el, className) {
    var currentEl = el;
    while (currentEl && !hasClass(currentEl, className)) {
        currentEl = currentEl.parentElement;
    }
    return currentEl;
}
function getCurrentEditorEl(wikiLinkEl, containerClassName) {
    var editorDefaultEl = findParentByClassName(wikiLinkEl, "toastui-editor-defaultUI");
    return editorDefaultEl.querySelector(".".concat(containerClassName, " .ProseMirror"));
}
function sleep(ms) {
    return new Promise(function (resolve) { return setTimeout(resolve, ms); });
}
var containerClassName;
var currentEditorEl;


function wikiLinkPlugin(context, options) {
    if (options === void 0) { options = {}; }
    var eventEmitter = context.eventEmitter, pmState = context.pmState;
    eventEmitter.listen("focus", function (editType) {
        containerClassName = "toastui-editor-".concat(editType === "markdown" ? "md" : "ww", "-container");
    });
    var container = document.createElement("div");
    var inputForm = createInput();
    inputForm.onsubmit = function (ev) {
        ev.preventDefault();
        var link = document.getElementById("wiki-link-input-link");
        currentEditorEl = getCurrentEditorEl(container, containerClassName);
        eventEmitter.emit("command", "wikiLink", {
            link: link.value,
        });
        eventEmitter.emit("closePopup");
        link.value = '';
        currentEditorEl.focus();
    };
    container.appendChild(inputForm);
    var toolbarItemWiki = createToolbarItemOption(container);
    toolbarItemWiki.el.addEventListener('click', function () {
        sleep(10).then(function () { eventEmitter.emit("command", "fillInput"); });
    });
    return {
        markdownCommands: {
            fillInput: function (_a, _b, dispatch) {
                var tr = _b.tr, selection = _b.selection, schema = _b.schema;
                var slice = selection.content();
                var textContent = slice.content.textBetween(0, slice.content.size, "\n");
                document.getElementById('wiki-link-input-link').value = textContent;
                return true;
            },
            wikiLink: function (_a, _b, dispatch) {
                var link = _a.link;
                var tr = _b.tr, selection = _b.selection, schema = _b.schema;
                var openTag = "[[";
                var closeTag = "]]";
                var linked = ''.concat(openTag).concat(link.trim()).concat(closeTag);
                tr.replaceSelectionWith(schema.text(linked)).setSelection(createSelection(tr, selection, pmState.TextSelection, openTag, closeTag));
                dispatch(tr);
                return true;
            },
        },
        toolbarItems: [
            {
                groupIndex: 3,
                itemIndex: 3,
                item: toolbarItemWiki,
            },
        ],
        toHTMLRenderers: {
            text(node, context) {
                const capitalizeFirstLetter = (string) => {
                    return string.charAt(0).toUpperCase() + string.slice(1)
                }

                if (node.literal.includes('[[')) {
                    return [
                        { type: 'html', content: node.literal.replaceAll(/\[\[([^\]]+)\]\]/g, (match, p1, offset, string, groups) => {
                            let link = p1;
                            const hasFragment = link.includes('|')

                            let linkFragment = hasFragment ? link.split('|')[1] : '';
                            let linkText = link.split('|')[0].replaceAll('-',' ')

                            if (hasFragment) {
                                linkText = `${linkText} (${linkFragment})`
                                linkFragment = `#${linkFragment.replaceAll(' ','')}`
                            }

                            link =  link.split('|')[0].split(' ').map(capitalizeFirstLetter).join('-') + linkFragment;
                            return `<a href="/wiki/${link}">${linkText}</a>`
                        })}
                    ];
                } else {
                    return {
                        type: 'text',
                        content: node.literal
                    }
                }
            },
        },
    };
}

__webpack_exports__ = __webpack_exports__["default"];
/******/ 	return __webpack_exports__;
/******/ })()
;
});