/* geometry.jsx — bleed coverage, safety margins and alignment.
 *
 * A document can have a correct 3mm bleed setting and still have artwork that
 * stops dead on the trim line. The setting is not the check. This measures what
 * the objects actually do.
 *
 * Spine awareness matters: on facing pages the inner edge butts the spine and
 * is SUPPOSED to stop at trim. Flagging it produces a page of false positives.
 * Verso (even folio) has its spine on the right, recto on the left.
 *
 * All measurements in millimetres.
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
 if(t==="number")return isFinite(v)?String(Math.round(v*1000)/1000):"null";
 if(t==="boolean")return v?"true":"false";
 if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(enc(v[i]));return "["+a.join(",")+"]";}
 if(t==="object"){var o=[];for(var k in v)if(v.hasOwnProperty(k))o.push('"'+esc(k)+'":'+enc(v[k]));
 return "{"+o.join(",")+"}";}return '"'+esc(v)+'"';}

var TOL = 0.05;                                   // mm, floating point slack
var R = { bleed: [], margins: [], drift: [], fractional: null, errors: [], settings: {} };

var doc = app.open(File(DOC_PATH), false);
var oldUnits = doc.viewPreferences.horizontalMeasurementUnits;
doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.MILLIMETERS;
doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.MILLIMETERS;

try {
    var dp = doc.documentPreferences;
    var BL = {
        top: dp.documentBleedTopOffset, bottom: dp.documentBleedBottomOffset,
        inside: dp.documentBleedInsideOrLeftOffset, outside: dp.documentBleedOutsideOrRightOffset
    };
    R.settings = { bleed: BL, facingPages: dp.facingPages };

    // Does this item make a mark? An empty text frame touching the edge is not
    // a bleed failure; a filled rectangle or a placed image is.
    function marks(it) {
        try {
            var cn = it.constructor.name;
            if (cn === "Group") return false;                 // children are tested individually
            if (it.images && it.images.length > 0) return true;
            if (it.graphics && it.graphics.length > 0) return true;
            var fn = it.fillColor ? String(it.fillColor.name) : "None";
            var f = fn !== "None" && fn !== "Paper";
            var s = it.strokeColor && String(it.strokeColor.name) !== "None" && it.strokeWeight > 0;
            if (f || s) return true;
            if (cn === "TextFrame" && String(it.contents).replace(/\s/g, "").length > 0) return true;
        } catch (e) {}
        return false;
    }

    for (var p = 0; p < doc.pages.length; p++) {
        var page = doc.pages[p];
        var pb = page.bounds;                     // [y1, x1, y2, x2]
        var folio = String(page.name);

        // Which vertical edge is the spine?
        var spine = "none";
        if (dp.facingPages) {
            try {
                // Compare against the enum itself. String(enum) yields a numeric
                // code, so name comparison silently never matches and every
                // spine edge gets reported as a bleed failure.
                if (page.side === PageSideOptions.LEFT_HAND) spine = "right";
                else if (page.side === PageSideOptions.RIGHT_HAND) spine = "left";
                else spine = "single";
            } catch (e) { spine = "unknown"; }
        }

        var mp = page.marginPreferences;
        var mBox = { top: pb[0] + mp.top, left: pb[1] + mp.left,
                     bottom: pb[2] - mp.bottom, right: pb[3] - mp.right };

        var items = page.allPageItems;
        var edgeTouch = { left: false, right: false, top: false, bottom: false };
        var edgeFull  = { left: false, right: false, top: false, bottom: false };
        var edgeWho   = { left: null,  right: null,  top: null,  bottom: null  };

        function note(it, b) {
            var d = { type: it.constructor.name, bounds: [b[1], b[0], b[3], b[2]] };
            try { d.hasImage = it.images.length > 0; } catch (e) {}
            try { d.fill = it.fillColor ? String(it.fillColor.name) : "None"; } catch (e) {}
            try { if (d.hasImage) d.link = String(it.images[0].itemLink.name); } catch (e) {}
            return d;
        }

        for (var i = 0; i < items.length; i++) {
            var it = items[i];
            if (!marks(it)) continue;
            var b;
            try { b = it.geometricBounds; } catch (e) { continue; }
            var name = it.constructor.name;

            // --- bleed: does anything touching an edge reach the full bleed? ---
            if (b[1] <= pb[1] + TOL) { edgeTouch.left = true; if (!edgeWho.left) edgeWho.left = note(it, b);
                if (b[1] <= pb[1] - BL.outside + TOL || b[1] <= pb[1] - BL.inside + TOL) edgeFull.left = true; }
            if (b[3] >= pb[3] - TOL) { edgeTouch.right = true; if (!edgeWho.right) edgeWho.right = note(it, b);
                if (b[3] >= pb[3] + BL.outside - TOL || b[3] >= pb[3] + BL.inside - TOL) edgeFull.right = true; }
            if (b[0] <= pb[0] + TOL) { edgeTouch.top = true; if (!edgeWho.top) edgeWho.top = note(it, b);
                if (b[0] <= pb[0] - BL.top + TOL) edgeFull.top = true; }
            if (b[2] >= pb[2] - TOL) { edgeTouch.bottom = true; if (!edgeWho.bottom) edgeWho.bottom = note(it, b);
                if (b[2] >= pb[2] + BL.bottom - TOL) edgeFull.bottom = true; }

            // --- safety margin: live content inside the margin box ---
            var hasCopy = false;
            try { hasCopy = name === "TextFrame" &&
                            String(it.contents).replace(/\s/g, "").length > 0; } catch (e) {}
            if (hasCopy) {
                var over = [];
                if (b[1] < mBox.left  - TOL) over.push({ edge: "left",   by: mBox.left - b[1] });
                if (b[3] > mBox.right + TOL) over.push({ edge: "right",  by: b[3] - mBox.right });
                if (b[0] < mBox.top   - TOL) over.push({ edge: "top",    by: mBox.top - b[0] });
                if (b[2] > mBox.bottom+ TOL) over.push({ edge: "bottom", by: b[2] - mBox.bottom });
                // Something bleeding off the page deliberately is not a margin breach.
                var bleeding = (b[1] <= pb[1] + TOL) || (b[3] >= pb[3] - TOL) ||
                               (b[0] <= pb[0] + TOL) || (b[2] >= pb[2] - TOL);
                if (over.length && !bleeding) {
                    var snip = "";
                    try { snip = String(it.contents).substr(0, 40).replace(/[\r\n]+/g, " "); } catch (e) {}
                    R.margins.push({ folio: folio, type: name, overshoot: over, text: snip,
                                     bounds: [b[1], b[0], b[3], b[2]] });
                }
            }
        }

        // Report only edges that are USED but not filled, and never the spine.
        var edges = ["left", "right", "top", "bottom"];
        for (var e = 0; e < edges.length; e++) {
            var ed = edges[e];
            if (ed === spine) continue;                      // butts the spine, correct
            if (!edgeTouch[ed] || edgeFull[ed]) continue;
            R.bleed.push({ folio: folio, edge: ed, spine: spine, item: edgeWho[ed],
                           note: "artwork reaches trim but stops short of the " +
                                 (ed === "top" ? BL.top : ed === "bottom" ? BL.bottom : BL.outside) +
                                 "mm bleed" });
        }
    }

    // --- repeated elements: does a folio or running head drift page to page? ---
    (function () {
        var buckets = {};
        for (var p = 0; p < doc.pages.length; p++) {
            var page = doc.pages[p], items = page.allPageItems, pb = page.bounds;
            for (var i = 0; i < items.length; i++) {
                try {
                    if (items[i].constructor.name !== "TextFrame") continue;
                    var c = String(items[i].contents).replace(/\s/g, "");
                    if (c.length === 0 || c.length > 40) continue;
                    var b = items[i].geometricBounds;
                    // Key on size and side so the same furniture groups together.
                    var w = Math.round((b[3] - b[1]) * 2) / 2, h = Math.round((b[2] - b[0]) * 2) / 2;
                    var side = (b[1] - pb[1]) < (pb[3] - b[3]) ? "L" : "R";
                    var key = side + "|" + w + "x" + h;
                    if (!buckets[key]) buckets[key] = [];
                    buckets[key].push({ folio: String(page.name), x: b[1] - pb[1], y: b[0] - pb[0] });
                } catch (e) {}
            }
        }
        for (var k in buckets) {
            if (!buckets.hasOwnProperty(k) || buckets[k].length < 4) continue;
            var xs = [], ys = [];
            for (var j = 0; j < buckets[k].length; j++) { xs.push(buckets[k][j].x); ys.push(buckets[k][j].y); }
            function spread(a) { var mn = a[0], mx = a[0];
                for (var i = 1; i < a.length; i++) { if (a[i] < mn) mn = a[i]; if (a[i] > mx) mx = a[i]; }
                return mx - mn; }
            var dx = spread(xs), dy = spread(ys);
            if (dx > 0.35 || dy > 0.35) {
                var worst = [];
                for (var j2 = 0; j2 < buckets[k].length && worst.length < 8; j2++) worst.push(buckets[k][j2]);
                R.drift.push({ key: k, count: buckets[k].length,
                               driftX_mm: dx, driftY_mm: dy, samples: worst });
            }
        }
    })();

    // --- near-misses: elements that ALMOST align to a margin or column guide.
    //     Exact alignment or a deliberate offset are both fine; 0.05-0.5mm out
    //     is the signature of a nudge, and that is what the eye catches.
    (function () {
        var near = [];
        for (var p = 0; p < doc.pages.length; p++) {
            var page = doc.pages[p], pb = page.bounds, mp = page.marginPreferences;
            var guides = [pb[1] + mp.left, pb[3] - mp.right];
            var colW = ((pb[3] - mp.right) - (pb[1] + mp.left) - mp.columnGutter * (mp.columnCount - 1)) / mp.columnCount;
            for (var c = 1; c < mp.columnCount; c++)
                guides.push(pb[1] + mp.left + c * (colW + mp.columnGutter));
            var items = page.allPageItems;
            for (var i = 0; i < items.length; i++) {
                try {
                    if (!marks(items[i])) continue;
                    var b = items[i].geometricBounds;
                    for (var e = 0; e < 2; e++) {
                        var x = e === 0 ? b[1] : b[3];
                        for (var g = 0; g < guides.length; g++) {
                            var d = Math.abs(x - guides[g]);
                            if (d > 0.05 && d < 0.5) {
                                near.push({ folio: String(page.name), type: items[i].constructor.name,
                                            edge: e === 0 ? "left" : "right", offBy_mm: d });
                                g = guides.length; e = 2;
                            }
                        }
                    }
                } catch (e2) {}
            }
        }
        R.nearMiss = near;
    })();

} catch (e) {
    R.errors.push(String(e));
}

try { doc.viewPreferences.horizontalMeasurementUnits = oldUnits; } catch (e) {}
doc.close(SaveOptions.NO);

var out = File(OUT_PATH); out.encoding = "UTF-8"; out.open("w"); out.write(enc(R)); out.close();
"ok";
