/*!
 * TOAST UI Editor : Reference Plugin
 * @version 1.0.0 | Wed Apr 24 2024
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
		root["toastui"] = root["toastui"] || {}, root["toastui"]["Editor"] = root["toastui"]["Editor"] || {}, root["toastui"]["Editor"]["plugin"] = root["toastui"]["Editor"]["plugin"] || {}, root["toastui"]["Editor"]["plugin"]["uml"] = factory();
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
/* harmony export */   "default": function() { return /* binding */ referencePlugin; }
/* harmony export */ });
/* unused harmony export findParentByClassName */

function createInput() {
    var form = document.createElement("form");
    form.innerHTML = "<input class='reference-input' id='reference-input-author' type='text' placeholder='Author(s)' />";
    form.innerHTML += "<input class='reference-input' id='reference-input-year' type='text' placeholder='Year' />";
    form.innerHTML += "<input class='reference-input' id='reference-input-title' type='text' placeholder='Title, Publisher, Pages etc.' />";
    form.innerHTML += "<input class='reference-input' id='reference-input-link' type='text' placeholder='Link or DOI or hive post' />";
    form.innerHTML += "<input class='reference-input' id='reference-input-isbn' type='text' placeholder='ISBN' />";
    form.innerHTML += "<input type='submit' value='submit' />";
    return form;
}
function createToolbarItemOption(element) {
    var referenceCustomEl = document.createElement('button');
    referenceCustomEl.textContent = 'Ref';
    referenceCustomEl.className = 'toastui-editor-toolbar-icons custom';
    return {
        name: "reference",
        tooltip: "Reference",
        el: referenceCustomEl,
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
function getCurrentEditorEl(referenceEl, containerClassName) {
    var editorDefaultEl = findParentByClassName(referenceEl, "toastui-editor-defaultUI");
    return editorDefaultEl.querySelector(".".concat(containerClassName, " .ProseMirror"));
}
function sleep(ms) {
    return new Promise(function (resolve) { return setTimeout(resolve, ms); });
}
var containerClassName;
var currentEditorEl;
function referencePlugin(context, options) {
    if (options === void 0) { options = {}; }
    var eventEmitter = context.eventEmitter, pmState = context.pmState;
    eventEmitter.listen("focus", function (editType) {
        containerClassName = "toastui-editor-".concat(editType === "markdown" ? "md" : "ww", "-container");
    });
    var container = document.createElement("div");
    var inputForm = createInput();
    inputForm.onsubmit = function (ev) {
        ev.preventDefault();
        var author = document.getElementById("reference-input-author");
        var year = document.getElementById("reference-input-year");
        var title = document.getElementById("reference-input-title");
        var link = document.getElementById("reference-input-link");
        var isbn = document.getElementById("reference-input-isbn");
        currentEditorEl = getCurrentEditorEl(container, containerClassName);
        eventEmitter.emit("command", "reference", {
            author: author.value,
            year: year.value,
            title: title.value,
            link: link.value,
            isbn: isbn.value
        });
        eventEmitter.emit("closePopup");
        author.value = '';
        year.value = '';
        title.value = '';
        link.value = '';
        isbn.value = '';
        currentEditorEl.focus();
    };
    container.appendChild(inputForm);
    var toolbarItem = createToolbarItemOption(container);
    toolbarItem.el.addEventListener('click', function () {
        sleep(10).then(function () { eventEmitter.emit("command", "fillInput"); });
    });
    return {
        markdownCommands: {
            fillInput: function (_a, _b, dispatch) {
                var tr = _b.tr, selection = _b.selection, schema = _b.schema;
                var slice = selection.content();
                var textContent = slice.content.textBetween(0, slice.content.size, "\n");
                document.getElementById('reference-input-title').value = textContent;
                return true;
            },
            reference: function (_a, _b, dispatch) {
                var author = _a.author, year = _a.year, title = _a.title, link = _a.link, isbn = _a.isbn;
                var tr = _b.tr, selection = _b.selection, schema = _b.schema;
                var openTag = "<ref>";
                var closeTag = "</ref>";
                var reference = author + ' ';
                if (year != '') {
                    reference += '(' + year + ') ';
                }
                reference += title + ' ' + link + ' ';
                if (isbn != '') {
                    reference += 'ISBN: ' + isbn;
                }
                var referenced = "".concat(openTag).concat(reference.trim()).concat(closeTag);
                tr.replaceSelectionWith(schema.text(referenced)).setSelection(createSelection(tr, selection, pmState.TextSelection, openTag, closeTag));
                dispatch(tr);
                return true;
            },
        },
        wysiwygCommands: {
            fillInput: function (_a, _b, dispatch) {
                var tr = _b.tr, selection = _b.selection, schema = _b.schema;
                var slice = selection.content();
                var textContent = slice.content.textBetween(0, slice.content.size, "\n");
                document.getElementById('reference-input-title').value = textContent;
                return true;
            },
            reference: function (_a, _b, dispatch) {
                var author = _a.author, year = _a.year, title = _a.title, link = _a.link, isbn = _a.isbn;
                var tr = _b.tr, selection = _b.selection, schema = _b.schema;
                var from = selection.from, to = selection.to;
                var mark = schema.marks.ref.create();
                tr.addMark(from, to, mark);
                dispatch(tr);
                return true;
            },
        },
        toolbarItems: [
            {
                groupIndex: 4,
                itemIndex: 0,
                item: toolbarItem,
            },
        ],
        toHTMLRenderers: {
            htmlInline: {
                ref: function (node, _a) {
                    //return context.entering ? [
                    //    { type: 'openTag', tagName: 'span', classNames: ['reference-rendered'] },
                    //    { type: 'text', content: node.next.literal },
                    //    { type: 'closeTag', tagName: 'span' }
                    //  ] : [ ];
                    var origin = _a.origin, entering = _a.entering;
                    // same error e.match when switching md->wysiwyg, also span doesn't close when it should in wysiwyg
                    //const result = origin();
                    //result.type = 'html';
                    //result.content = '</span>';
                    //if(entering) { 
                    //    result.content = '<span class="reference-rendered">';
                    //}
                    //return result;
                    // @todo breaks wysiwyg, error e.match when switching from md
                    return entering
                        ? {
                            type: "openTag",
                            //type: "html",
                            //content: '<span class="reference-rendered">',
                            tagName: "span",
                            classNames: ["reference-rendered"],
                        }
                        //: { type: "html", content: "</span>" };
                        : { type: "closeTag", tagName: "span" };
                },
            },
        },
    };
}

__webpack_exports__ = __webpack_exports__["default"];
/******/ 	return __webpack_exports__;
/******/ })()
;
});