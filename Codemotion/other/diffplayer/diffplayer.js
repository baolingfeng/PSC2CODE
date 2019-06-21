/*    MINIMAL DEMO of using Ace and diff-match-patch to create a
      record-replay system

      Dependencies:
      - jQuery (included)
      - jQuery doTimeout (included) http://benalman.com/projects/jquery-dotimeout-plugin/
      - diff-match-patch (included) https://code.google.com/p/google-diff-match-patch/
      - Ace (check out from GitHub into pwd) https://github.com/ajaxorg/ace-builds

      Copyright Philip Guo - www.pgbovine.net
*/


// gross global variables ...

var dmp = new diff_match_patch();
var deltas, deltaObjs, allDiffs, timestamps, relativeTimestamps;
var editor, replayer, doc;

var idx = 0;
var curTimeoutId;

var curText = ''; // current text of the editor
// each element is an object with 't' as timestamp and 'd' as the delta object
var deltas = [];

var DEBOUNCE_MS = 1000; // milliseconds of debouncing (i.e., 'clustering' a
                        // rapid series of edit actions as a single diff)
                        // set to 'null' for no debouncing

var Range = ace.require("ace/range").Range;


// applies diff to doc
function applyDiff(diff, isReverse /* optional -- should we reverse effects of the diff? */) {
  if (isReverse === undefined) {
    isReverse = false;
  }
  console.log('applyDiff', isReverse, diff);

  // each diff consists of N chunks, starting edits at offset 0
  var offset = 0;

  // see http://stackoverflow.com/questions/25083183/how-can-i-get-and-patch-diffs-in-ace-editor
  diff.forEach(function(chunk) {
    var op = chunk[0];
    var text = chunk[1];

    if (op === 0) { // equality ... just advance forward
      offset += text.length;
    } else if (op === (isReverse ? 1 : -1)) { // -1 means delete
      doc.remove(Range.fromPoints(
        doc.indexToPosition(offset),
        doc.indexToPosition(offset + text.length)
      ));

      // move the editor's cursor to offset to look aesthetically sharp
      replayer.clearSelection(); // or else we get a weird selection
      replayer.moveCursorToPosition(doc.indexToPosition(offset));
    } else if (op === (isReverse ? -1 : 1)) { // 1 means insert
      doc.insert(doc.indexToPosition(offset), text);
      offset += text.length;

      // move the editor's cursor to offset to look aesthetically sharp
      replayer.clearSelection(); // or else we get a weird selection
      replayer.moveCursorToPosition(doc.indexToPosition(offset /* new offset value */ ));

    } else {
      console.assert(false);
    }
  });
}

function reverseDiff(diff) {
  applyDiff(diff, true);
}

function snapshotDiff() {
  var newText = editor.getValue();

  var timestamp = new Date().getTime();

  if (curText != newText) {
    /*

The two key function calls here are diff_main followed by diff_toDelta

Each 'd' field is in the following format:

http://downloads.jahia.com/downloads/jahia/jahia6.6.1/jahia-root-6.6.1.0-aggregate-javadoc/name/fraser/neil/plaintext/DiffMatchPatch.html#diff_toDelta(java.util.LinkedList)

Crush the diff into an encoded string which describes the operations
required to transform text1 into text2. E.g. =3\t-2\t+ing -> Keep 3
chars, delete 2 chars, insert 'ing'. Operations are tab-separated.
Inserted text is escaped using %xx notation.

    */
    var delta = {t: timestamp,
                 d: dmp.diff_toDelta(dmp.diff_main(curText, newText))};

    deltas.push(delta);
    curText = newText;
  }
}


$(document).ready(function() {
  $("#replayerPane").hide();

  // initialize globals
  editor = ace.edit("editor");
  replayer = ace.edit("replayer");
  // containment relationship: Editor -> EditSession -> Document
  doc = replayer.getSession().getDocument();

  editor.$blockScrolling = Infinity; // kludgy to shut up weird warnings
  replayer.$blockScrolling = Infinity; // kludgy to shut up weird warnings

  // whenever the editor's content changes, run ...
  editor.on('change', function(e) {
    // debounce so that we don't fire an event for every single
    // keystroke. deboucing means that the callback function snapshotDiff
    // will be called only ONCE at the end of a rapid succession of
    // 'change' events after a specified DEBOUNCE_MS timeout has elapsed.
    if (DEBOUNCE_MS > 0) {
      $.doTimeout('editorChange', DEBOUNCE_MS, snapshotDiff);
    } else {
      snapshotDiff(); // no debouncing!
    }
  });

  $("#replayBtn").click(function() {
    $("#editorPane").hide();
    $("#replayerPane").show();

    var startingText = '';
    replayer.setValue(startingText);
    idx = 0; // reset global

    // make sure all entries in deltas are in chronological order
    for (var i = 0; i < deltas.length-1; i++) {
      var cur = deltas[i];
      var next = deltas[i+1];
      console.assert(cur.t <= next.t);
    }

    deltaObjs = deltas.map(function(e) {return e.d;});
    var timestamps = deltas.map(function(e) {return e.t;});

    allDiffs = []; // global

    var cur = startingText;

    // turn delta objects into diffs by using the following contortions:
    deltaObjs.forEach(function(d, i) {
      var diff = dmp.diff_fromDelta(cur, d);
      allDiffs.push(diff);
      var patch = dmp.patch_make(diff);
      var newCur = dmp.patch_apply(patch, cur);
      console.assert(newCur.length === 2);
      cur = newCur[0];
    });

    console.assert(allDiffs.length === timestamps.length);
    console.assert(timestamps.length > 0);

    doc.insert(doc.indexToPosition(0), startingText); // initialize

    var relativeTimestamps = [500]; // start with a small starting delay
    for (var i = 1; i < timestamps.length; i++) {
      var timeDiff = timestamps[i] - timestamps[i-1];
      relativeTimestamps.push(timeDiff);
    }

    function autoclickNextBtn() {
      $("#nextBtn").click();
      console.assert(idx > 0);
      if (idx < relativeTimestamps.length) {
        curTimeoutId = setTimeout(autoclickNextBtn, relativeTimestamps[idx]);
      }
    }
    // uncomment to auto-play
    //curTimeoutId = setTimeout(autoclickNextBtn, relativeTimestamps[0]);
  });

  $("#nextBtn").click(function() {
    clearTimeout(curTimeoutId);

    if (idx < allDiffs.length) {
      var curDiff = allDiffs[idx];
      applyDiff(curDiff);
      console.log('next', idx);
      idx++;
    }
  });

  $("#prevBtn").click(function() {
    clearTimeout(curTimeoutId);

    if (idx > 0) {
      idx--;
      var curDiff = allDiffs[idx];
      reverseDiff(curDiff);
      console.log('prev', idx);
    }
  });
});
