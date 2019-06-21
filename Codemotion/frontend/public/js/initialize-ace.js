function initializeAce() {
	var editor = ace.edit(this)
	editor.getSession().setMode('ace/mode/'+$(this).data('language'))
	
	editor.getSession().setUseWrapMode(true)
	editor.setShowPrintMargin(false)
	editor.setHighlightActiveLine(false)
	editor.$blockScrolling = Infinity
}