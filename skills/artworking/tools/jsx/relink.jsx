/* relink.jsx — find missing images and reconnect them.
 *
 * Relinking is a link operation: it does not recompose text and does not move
 * anything. That makes it the safest useful edit there is, PROVIDED the right
 * file is chosen. Matching purely on filename is how the wrong version of an
 * image ends up in print, so anything ambiguous is reported and skipped.
 *
 * PARAMS: { candidates: {name: [paths...]}, apply: bool }
 */

app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;

var DOC_PATH = "__DOC_PATH__";
var OUT_PATH = "__OUT_PATH__";
var PARAMS   = __PARAMS__;

function esc(s){s=String(s);var o="",c;for(var i=0;i<s.length;i++){c=s.charAt(i);
 if(c==='"')o+='\\"';else if(c==="\\")o+="\\\\";else if(c==="\n"||c==="\r")o+="\\n";
 else if(s.charCodeAt(i)<32||s.charCodeAt(i)>126){var h=s.charCodeAt(i).toString(16);
 while(h.length<4)h="0"+h;o+="\\u"+h;}else o+=c;}return o;}
function enc(v){if(v===null||v===undefined)return "null";var t=typeof v;
 if(t==="number")return isFinite(v)?String(v):"null";if(t==="boolean")return v?"true":"false";
 if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(enc(v[i]));return "["+a.join(",")+"]";}
 if(t==="object"){var o=[];for(var k in v)if(v.hasOwnProperty(k))o.push('"'+esc(k)+'":'+enc(v[k]));
 return "{"+o.join(",")+"}";}return '"'+esc(v)+'"';}

var LINK_MISSING = 1819109747;   // lmis

var R = { applied: [], skipped: [], notFound: [], ambiguous: [], errors: [], apply: PARAMS.apply === true };
var doc = app.open(File(DOC_PATH), false);

try {
    // Snapshot geometry so we can prove nothing moved.
    // Measure the containing frames, NOT the Image objects. A relinked image
    // with different pixel dimensions legitimately changes its own bounds
    // inside the frame; what must not move is the frame on the page.
    function frameBounds() {
        var out = [], items = doc.allPageItems;
        for (var g = 0; g < items.length; g++) {
            try {
                var cn = items[g].constructor.name;
                if (cn === "Image" || cn === "PDF" || cn === "EPS" || cn === "WMF") continue;
                out.push(cn + ":" + items[g].geometricBounds.join(","));
            } catch (e) {}
        }
        return out;
    }
    var before = frameBounds();

    // Collect first: relinking mutates doc.links, so iterating it live skips entries.
    var todo = [];
    for (var i = 0; i < doc.links.length; i++) {
        var l = doc.links[i];
        if (Number(l.status) !== LINK_MISSING) continue;
        todo.push({ name: String(l.name), index: i });
    }

    for (var t = 0; t < todo.length; t++) {
        var name = todo[t].name;
        var cands = PARAMS.candidates[name];

        if (!cands || cands.length === 0) { R.notFound.push(name); continue; }
        if (cands.length > 1) {
            R.ambiguous.push({ name: name, candidates: cands });
            continue;                       // never guess between versions
        }

        var link = null;
        for (var k = 0; k < doc.links.length; k++) {
            if (String(doc.links[k].name) === name && Number(doc.links[k].status) === LINK_MISSING) {
                link = doc.links[k]; break;
            }
        }
        if (!link) { R.skipped.push({ name: name, reason: "already resolved" }); continue; }

        var rec = { name: name, to: cands[0] };
        try { rec.ppiBefore = link.parent.effectivePpi; } catch (e) {}

        if (!R.apply) { R.applied.push(rec); continue; }   // dry run

        try {
            link.relink(File(cands[0]));
            link.update();
            try {
                for (var m = 0; m < doc.links.length; m++) {
                    if (String(doc.links[m].name) === File(cands[0]).name) {
                        rec.ppiAfter = doc.links[m].parent.effectivePpi;
                        rec.status = enc(Number(doc.links[m].status));
                        break;
                    }
                }
            } catch (e) {}
            R.applied.push(rec);
        } catch (e) {
            R.errors.push(name + ": " + e);
        }
    }

    // Nothing may have moved. Relinking must never reflow a frame.
    var after = frameBounds(), moved = 0;
    for (var b = 0; b < before.length && b < after.length; b++)
        if (before[b] !== after[b]) moved++;
    R.framesMoved = moved;
    R.itemCountBefore = before.length;
    R.itemCountAfter = after.length;

    if (R.apply && moved === 0 && R.errors.length === 0) {
        doc.save();
        R.saved = true;
    } else {
        R.saved = false;
        if (moved > 0) R.errors.push(moved + " page item(s) moved during relink — not saved");
    }
} catch (e) {
    R.errors.push(String(e));
}

doc.close(SaveOptions.NO);
var out = File(OUT_PATH); out.encoding = "UTF-8"; out.open("w"); out.write(enc(R)); out.close();
"ok";
