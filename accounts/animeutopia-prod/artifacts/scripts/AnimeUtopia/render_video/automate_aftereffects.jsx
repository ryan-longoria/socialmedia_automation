#include "json2.jsx"

var LOG_FILE_PATH = "C:/animeutopia/after_effects_log.txt";

function logMessage(level, message) {
    var now = new Date();
    var timestamp = now.toISOString();
    var logStr = "[" + level + " " + timestamp + "] " + message;
    $.writeln(logStr);

    var logFile = new File(LOG_FILE_PATH);
    if (logFile.open("a")) {
        logFile.writeln(logStr);
        logFile.close();
    }
}

function downloadFromUrl(url, localPath) {
    try {
        logMessage("INFO", "Attempting to download: " + url);
        var socket = new Socket();
        var urlParts = url.split("://");
        if (urlParts.length < 2) {
            throw new Error("Invalid URL format: " + url);
        }
        var hostAndPath = urlParts[1].split("/");
        var host = hostAndPath.shift();
        var path = "/" + hostAndPath.join("/");

        if (socket.open(host + ":80", "BINARY")) {
            var request = "GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\n\r\n";
            socket.write(request);
            var response = socket.read(999999);
            socket.close();
            var parts = response.split("\r\n\r\n");
            if (parts.length < 2) {
                throw new Error("Invalid HTTP response.");
            }
            var content = parts.slice(1).join("\r\n\r\n");
            var file = new File(localPath);
            if (!file.open("w")) {
                throw new Error("Failed to open local file for writing: " + localPath);
            }
            file.write(content);
            file.close();
            logMessage("INFO", "File downloaded successfully to: " + localPath);
            return true;
        } else {
            throw new Error("Unable to open socket connection to: " + host);
        }
    } catch (e) {
        logMessage("ERROR", "Download failed: " + e.message);
        return false;
    }
}

var s3JsonUrl = "{{PRESIGNED_URL}}";  
var localJsonPath = "C:/animeutopia/output/most_recent_post.json";
if (!downloadFromUrl(s3JsonUrl, localJsonPath)) {
    logMessage("ERROR", "Failed to download JSON from S3.");
    throw new Error("Failed to download JSON from S3. Exiting script execution.");
}

var jsonFile = new File(localJsonPath);
if (!jsonFile.exists) {
    throw new Error("JSON file not found at " + localJsonPath);
}
jsonFile.open("r");
var jsonData = jsonFile.read();
jsonFile.close();

var postData;
try {
    postData = JSON.parse(jsonData);
    logMessage("INFO", "JSON data loaded. Title = " + postData.title);
} catch (e) {
    logMessage("ERROR", "JSON parse error: " + e.message);
    throw e;
}

var projectFilePath = "C:/animeutopia/anime_template.aep";
var projectFile = new File(projectFilePath);
if (!projectFile.exists) {
    throw new Error("After Effects project file not found: " + projectFilePath);
}
app.open(projectFile);
logMessage("INFO", "Opened AE project: " + projectFile.fsName);

try {
    var compName = "standard-news-template";
    var comp = null;
    for (var i = 1; i <= app.project.items.length; i++) {
        var item = app.project.items[i];
        if (item instanceof CompItem && item.name === compName) {
            comp = item;
            break;
        }
    }
    if (!comp) {
        throw new Error("Composition not found: " + compName);
    }

    var titleLayer = comp.layer("Title");
    var descLayer = comp.layer("Description");
    var bgLayer = comp.layer("BackgroundImage");

    if (!titleLayer) throw new Error("Title layer not found.");
    if (!descLayer) throw new Error("Description layer not found.");

    titleLayer.property("Source Text").setValue(postData.title);
    descLayer.property("Source Text").setValue(postData.description);
    logMessage("INFO", "Updated text layers: Title and Description.");

    var imageFile = new File("C:/animeutopia/output/backgroundimage_converted.jpg");
    if (imageFile.exists && bgLayer) {
        logMessage("INFO", "Replacing background image...");
        var importOpts = new ImportOptions(imageFile);
        var newFootage = app.project.importFile(importOpts);
        bgLayer.replaceSource(newFootage, false);

        var compW = comp.width;
        var compH = comp.height;
        var layerW = bgLayer.source.width;
        var layerH = bgLayer.source.height;
        var scaleX = (compW / layerW) * 100;
        var scaleY = (compH / layerH) * 100;
        var scaleFactor = Math.max(scaleX, scaleY);
        bgLayer.transform.scale.setValue([scaleFactor, scaleFactor]);
        bgLayer.transform.position.setValue([compW / 2, compH / 2]);

        logMessage("INFO", "Background replaced & scaled.");
    } else {
        logMessage("INFO", "No background image replaced (file missing or no BG layer).");
    }

    var updatedProjectFile = new File("C:/animeutopia/output/anime_template_updated.aep");
    app.project.save(updatedProjectFile);
    logMessage("INFO", "Project updated & saved: " + updatedProjectFile.fsName);

} catch (e) {
    logMessage("ERROR", "Error updating layers: " + e.message);
    throw e;
}

logMessage("INFO", "ExtendScript finished updates. Ready for aerender.");