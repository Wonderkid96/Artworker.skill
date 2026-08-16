/* package.jsx — File > Package, driven from a script.
 *
 * Collects the document with its links and fonts so it can be handed to
 * someone else and actually open correctly. Runs against a COPY.
 *
 * Caveat that no setting fixes: fonts activated through Adobe Fonts are NOT
 * included. That is an Adobe licensing restriction. The report says so.
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

var R = { ok: false, warnings: [], errors: [] };
var doc = app.open(File(DOC_PATH), false);

try {
    // Record what a receiver will and will not get, before packaging.
    var missing = [], adobeFonts = [];
    for (var i = 0; i < doc.fonts.length; i++) {
        var f = doc.fonts[i], st = Number(f.status);
        // fsSu = substituted, fsNa = not available
        if (st === 1718834037 || st === 1718837601) missing.push(String(f.name));
        try {
            // Adobe Fonts live under CoreSync and are never packaged.
            var loc = String(f.location);
            if (loc.indexOf("CoreSync") !== -1 || loc.indexOf("Adobe/CoreSync") !== -1)
                adobeFonts.push(String(f.name));
        } catch (e) {}
    }
    R.missingFonts = missing;
    R.adobeFonts = adobeFonts;
    if (adobeFonts.length)
        R.warnings.push(adobeFonts.length + " font(s) come from Adobe Fonts and will NOT be included "
            + "in the package. That is an Adobe licensing restriction, not a setting. "
            + "Tell the recipient which families to activate: " + adobeFonts.join(", "));
    if (missing.length)
        R.warnings.push(missing.length + " font(s) are missing or substituted in this document, so they "
            + "cannot be packaged either: " + missing.join(", "));

    var badLinks = [];
    for (var j = 0; j < doc.links.length; j++)
        if (Number(doc.links[j].status) === 1819109747) badLinks.push(String(doc.links[j].name));
    R.missingLinks = badLinks;
    if (badLinks.length)
        R.warnings.push(badLinks.length + " link(s) are missing and cannot be collected: "
            + badLinks.slice(0, 10).join(", ") + (badLinks.length > 10 ? " ..." : ""));

    var folder = new Folder(PARAMS.outFolder);
    if (!folder.exists) folder.create();

    doc.packageForPrint(
        folder,
        true,                       // copy fonts
        true,                       // copy linked graphics
        true,                       // copy colour profiles
        true,                       // update graphic links
        PARAMS.hiddenLayers === true,
        true,                       // ignore preflight errors (we report our own)
        true,                       // create report
        PARAMS.includeIdml !== false,
        PARAMS.includePdf === true,
        PARAMS.pdfPreset || ""
    );

    R.ok = true;
    R.folder = String(folder.fsName);
    R.linkCount = doc.links.length;
    R.fontCount = doc.fonts.length;
} catch (e) {
    R.errors.push(String(e));
}

doc.close(SaveOptions.NO);

var out = File(OUT_PATH); out.encoding = "UTF-8"; out.open("w"); out.write(enc(R)); out.close();
"ok";
