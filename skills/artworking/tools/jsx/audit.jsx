/* audit.jsx — read an InDesign document and emit JSON.
 *
 * Runs against a COPY. indesign.py never passes the original.
 *
 * ExtendScript is ES3: no JSON, no modern syntax, and an exception inside a
 * loop silently ends the loop. Every section is therefore wrapped so one
 * failure records itself and the rest still runs — a partial audit that says
 * what it missed beats a blank one that looks fine.
 */

app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;

var DOC_PATH = "__DOC_PATH__";
var OUT_PATH = "__OUT_PATH__";

// --- minimal JSON writer (ES3 has none) ------------------------------------

function esc(s) {
    s = String(s);
    var out = "", c;
    for (var i = 0; i < s.length; i++) {
        c = s.charAt(i);
        if (c === '"') out += '\\"';
        else if (c === "\\") out += "\\\\";
        else if (c === "\n" || c === "\r") out += "\\n";
        else if (c === "\t") out += "\\t";
        else if (s.charCodeAt(i) < 32 || s.charCodeAt(i) > 126) {
            var h = s.charCodeAt(i).toString(16);
            while (h.length < 4) h = "0" + h;
            out += "\\u" + h;
        } else out += c;
    }
    return out;
}

function enc(v) {
    if (v === null || v === undefined) return "null";
    var t = typeof v;
    if (t === "number") return isFinite(v) ? String(v) : "null";
    if (t === "boolean") return v ? "true" : "false";
    if (v instanceof Array) {
        var a = [];
        for (var i = 0; i < v.length; i++) a.push(enc(v[i]));
        return "[" + a.join(",") + "]";
    }
    if (t === "object") {
        var o = [];
        for (var k in v) if (v.hasOwnProperty(k)) o.push('"' + esc(k) + '":' + enc(v[k]));
        return "{" + o.join(",") + "}";
    }
    return '"' + esc(v) + '"';
}

// --- harness ---------------------------------------------------------------

var R = { errors: [] };
function section(name, fn) {
    try { R[name] = fn(); }
    catch (e) { R[name] = null; R.errors.push(name + ": " + e); }
}
function code(v) {                       // 4-char enum -> readable string
    try {
        var n = Number(v), s = "";
        for (var i = 3; i >= 0; i--) s += String.fromCharCode((n >> (i * 8)) & 255);
        return s;
    } catch (e) { return String(v); }
}

function locate(it) {
    var d = { type: "?", folio: "pasteboard", bounds: null };
    try { d.type = it.constructor.name; } catch (e) {}
    try { if (it.parentPage) d.folio = String(it.parentPage.name); } catch (e) {}
    try { var b = it.geometricBounds; d.bounds = [b[1], b[0], b[3], b[2]]; } catch (e) {}
    return d;
}

var doc = app.open(File(DOC_PATH), false);

section("document", function () {
    var dp = doc.documentPreferences;
    return {
        pages: doc.pages.length,
        spreads: doc.spreads.length,
        facingPages: dp.facingPages,
        pageWidth_mm: dp.pageWidth,
        pageHeight_mm: dp.pageHeight,
        bleedTop: dp.documentBleedTopOffset,
        bleedBottom: dp.documentBleedBottomOffset,
        bleedInside: dp.documentBleedInsideOrLeftOffset,
        bleedOutside: dp.documentBleedOutsideOrRightOffset,
        slugTop: dp.slugTopOffset,
        intent: code(dp.intent),
        cmykProfile: String(doc.cmykProfile),
        rgbProfile: String(doc.rgbProfile),
        firstFolio: doc.pages.length ? String(doc.pages[0].name) : null,
        lastFolio: doc.pages.length ? String(doc.pages[doc.pages.length - 1].name) : null
    };
});

section("margins", function () {
    var mp = doc.pages[0].marginPreferences;
    return { top: mp.top, bottom: mp.bottom, left: mp.left, right: mp.right,
             columns: mp.columnCount, gutter: mp.columnGutter };
});

section("fonts", function () {
    var seen = {}, out = [];
    for (var i = 0; i < doc.fonts.length; i++) {
        var f = doc.fonts[i], key = String(f.name);
        if (seen[key]) { seen[key].count++; continue; }
        // fsIn = installed, fsSu = SUBSTITUTED (the font is missing)
        seen[key] = { name: key, status: code(f.status), type: code(f.fontType), count: 1 };
        out.push(seen[key]);
    }
    return out;
});

section("swatches", function () {
    var out = [];
    for (var i = 0; i < doc.swatches.length; i++) {
        var s = doc.swatches[i], vals = null, model = "-", space = "-";
        try { vals = s.colorValue; } catch (e) {}
        try { model = code(s.model); } catch (e) {}
        try { space = code(s.space); } catch (e) {}
        out.push({ name: String(s.name), model: model, space: space, values: vals });
    }
    return out;
});

section("unusedSwatches", function () {
    var u = doc.unusedSwatches, out = [];
    for (var i = 0; i < u.length; i++) {
        var n = String(u[i].name);
        if (n !== "") out.push(n);
    }
    return out;
});

section("inks", function () {
    var out = [];
    for (var i = 0; i < doc.inks.length; i++) out.push(String(doc.inks[i].name));
    return out;
});

section("links", function () {
    var out = [];
    for (var i = 0; i < doc.links.length; i++) {
        var l = doc.links[i], rec = { name: String(l.name), status: code(l.status) };
        try { rec.path = String(l.filePath); } catch (e) {}
        try {
            var im = l.parent;
            rec.effectivePpi = im.effectivePpi;
            rec.actualPpi = im.actualPpi;
            try { rec.space = String(im.space); } catch (e) {}
            try { rec.page = im.parentPage ? String(im.parentPage.name) : "pasteboard"; } catch (e) {}
        } catch (e) {}
        out.push(rec);
    }
    return out;
});

section("overset", function () {
    // Only obtainable from the source. A PDF cannot show it.
    var out = [];
    for (var i = 0; i < doc.stories.length; i++) {
        if (!doc.stories[i].overflows) continue;
        var rec = { page: "?", snippet: "" };
        try {
            var tc = doc.stories[i].textContainers, last = tc[tc.length - 1];
            rec.page = last.parentPage ? String(last.parentPage.name) : "pasteboard";
        } catch (e) {}
        try { rec.snippet = String(doc.stories[i].contents).substr(0, 80); } catch (e) {}
        out.push(rec);
    }
    return { count: out.length, stories: doc.stories.length, items: out };
});

section("typeSizes", function () {
    var sizes = {}, out = [];
    for (var i = 0; i < doc.stories.length; i++) {
        var r = doc.stories[i].textStyleRanges;
        for (var j = 0; j < r.length; j++) {
            try {
                var body = String(r[j].contents);
                if (body.replace(/\s/g, "").length === 0) continue;
                var ps = Math.round(r[j].pointSize * 100) / 100;
                sizes[ps] = (sizes[ps] || 0) + body.length;
            } catch (e) {}
        }
    }
    for (var k in sizes) if (sizes.hasOwnProperty(k)) out.push({ pt: Number(k), chars: sizes[k] });
    out.sort(function (a, b) { return a.pt - b.pt; });
    return out;
});

section("strokes", function () {
    var w = {}, out = [], thin = [], items = doc.allPageItems;
    for (var i = 0; i < items.length; i++) {
        try {
            var it = items[i], sc = null, sw = 0;
            try { sc = it.strokeColor; sw = it.strokeWeight; } catch (e) { continue; }
            if (!sc || String(sc.name) === "None" || !(sw > 0)) continue;
            var v = Math.round(sw * 1000) / 1000;
            w[v] = (w[v] || 0) + 1;
            if (v < 0.25) { var d = locate(it); d.pt = v; thin.push(d); }
        } catch (e) {}
    }
    for (var k in w) if (w.hasOwnProperty(k)) out.push({ pt: Number(k), items: w[k] });
    out.sort(function (a, b) { return a.pt - b.pt; });
    return { weights: out, belowMinimum: thin };
});

section("layers", function () {
    var out = [];
    for (var i = 0; i < doc.layers.length; i++) {
        var l = doc.layers[i];
        out.push({ name: String(l.name), visible: l.visible, printable: l.printable, locked: l.locked });
    }
    return out;
});

section("registrationUse", function () {
    var out = [], items = doc.allPageItems;
    for (var i = 0; i < items.length; i++) {
        try {
            var f = items[i].fillColor && String(items[i].fillColor.name) === "Registration";
            var s = items[i].strokeColor && String(items[i].strokeColor.name) === "Registration";
            if (!f && !s) continue;
            var d = locate(items[i]);
            d.on = f && s ? "fill+stroke" : (f ? "fill" : "stroke");
            out.push(d);
        } catch (e) {}
    }
    return { count: out.length, items: out };
});

section("textByPage", function () {
    // allPageItems, NOT page.textFrames — the latter misses frames nested
    // inside groups, which silently drops copy from the audit.
    var out = [];
    for (var p = 0; p < doc.pages.length; p++) {
        var page = doc.pages[p], items = page.allPageItems, parts = [];
        for (var i = 0; i < items.length; i++) {
            try {
                if (items[i].constructor.name !== "TextFrame") continue;
                var c = String(items[i].contents);
                if (c.replace(/\s/g, "").length === 0) continue;
                parts.push(c);
            } catch (e) {}
        }
        out.push({ folio: String(page.name), index: p + 1, text: parts.join("\n") });
    }
    return out;
});

doc.close(SaveOptions.NO);

var f = File(OUT_PATH);
f.encoding = "UTF-8";
f.open("w");
f.write(enc(R));
f.close();

"ok";
