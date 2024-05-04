function latexPlugin() {
    const toHTMLRenderers = {
        latex(node) {
            const generator = new latexjs.HtmlGenerator({ hyphenate: false });
            var body = latexjs.parse(node.literal, { generator: generator }).domFragment();

            // remove annotations and .katex-html
            const remove = body.querySelectorAll("annotation, .katex-html");
            remove.forEach(function(element){
                element.parentNode.removeChild(element);
            });
            var div = document.createElement('div');
            div.appendChild(body.cloneNode(true));
            body = div.innerHTML;
            
            return [
                { type: 'openTag', tagName: 'div', outerNewLine: true },
                { type: 'html', content: body },
                { type: 'closeTag', tagName: 'div', outerNewLine: true }
            ];
        },
    }

    return { toHTMLRenderers }
}