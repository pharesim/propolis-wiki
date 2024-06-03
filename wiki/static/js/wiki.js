const { colorSyntax, tableMergedCell, uml, wikiLink  } = toastui.Editor.plugin;
const viewer = toastui.Editor.factory({
    el: document.getElementById('editor'),
    initialValue: document.getElementById('editor').innerHTML,
    viewer: true,
    plugins: [latexPlugin, tableMergedCell, uml, wikiLink],
    extendedAutolinks: true
});