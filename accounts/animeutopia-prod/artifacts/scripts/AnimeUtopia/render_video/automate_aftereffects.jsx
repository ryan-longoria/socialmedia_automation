#include "json2.jsx"

var s3JsonUrl = "{{PRESIGNED_URL}}";  

/**
 * Custom logging function to output messages to the ExtendScript console and a log file.
 * @param {string} level - The log level (e.g., "INFO", "ERROR", "WARN").
 * @param {string} message - The log message.
 */
function logMessage(level, message) {
    var logStr = "[" + level + "] " + message;
    $.writeln(logStr);
    var logFile = new File("~/after_effects_log.txt");
    if (logFile.open("a")) {
        logFile.writeln(logStr);
        logFile.close();
    }
}

/**
 * Downloads a file from a URL using a basic HTTP GET via a Socket.
 * This function assumes the file is publicly accessible.
 * @param {string} url - The URL of the file to download.
 * @param {string} localPath - The local path where the file will be saved.
 * @returns {boolean} True if download succeeds, false otherwise.
 */
function downloadFromUrl(url, localPath) {
    try {
        var socket = new Socket();
        var urlParts = url.split("://");
        if (urlParts.length < 2) {
            throw new Error("Invalid URL format.");
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
            file.encoding = "UTF-8";
            if (!file.open("w")) {
                throw new Error("Failed to open local file for writing.");
            }
            file.write(content);
            file.close();
            logMessage("INFO", "File downloaded successfully from: " + url);
            return true;
        } else {
            throw new Error("Unable to open socket connection.");
        }
    } catch (e) {
        logMessage("ERROR", "Download failed: " + e.message);
        return false;
    }
}

var localJsonPath = "C:/animeutopia/output/most_recent_post.json";
var projectFilePath = "C:/animeutopia/anime_template.aep";

if (!downloadFromUrl(s3JsonUrl, localJsonPath)) {
    logMessage("ERROR", "Failed to download JSON from S3.");
    throw new Error("Failed to download JSON from S3. Exiting script execution.");
}

var jsonFile = new File(localJsonPath);
if (!jsonFile.exists) {
    logMessage("ERROR", "JSON file not found.");
    throw new Error("JSON file not found. Exiting script execution.");
}
jsonFile.open("r");
var jsonData = jsonFile.read();
jsonFile.close();
var postData = JSON.parse(jsonData);
logMessage("INFO", "JSON data loaded: Title = " + postData.title);

var projectFile = new File(projectFilePath);
if (!projectFile.exists) {
    logMessage("ERROR", "After Effects project file (.aep) not found.");
    throw new Error("After Effects project file not found. Exiting script execution.");
}
app.open(projectFile);
logMessage("INFO", "Opened project file: " + projectFile.fsName);

try {
    var comp = null;
    var compName = "standard-news-template";
    for (var i = 1; i <= app.project.items.length; i++) {
        var item = app.project.items[i];
        if (item instanceof CompItem && item.name === compName) {
            comp = item;
            break;
        }
    }
    if (!comp) {
        throw new Error("Composition '" + compName + "' not found in the project.");
    }
    logMessage("INFO", "Found composition: " + compName);

    var titleLayer = null;
    var subtitleLayer = null;
    var backgroundLayer = null;
    for (var i = 1; i <= comp.layers.length; i++) {
        var layer = comp.layers[i];
        if (layer.name === "Title") {
            titleLayer = layer;
        }
        if (layer.name === "Description") {
            subtitleLayer = layer;
        }
        if (layer.name === "BackgroundImage") {
            backgroundLayer = layer;
        }
    }
    if (!titleLayer) {
        throw new Error("Title layer not found in the composition.");
    }
    if (!subtitleLayer) {
        throw new Error("Description layer not found in the composition.");
    }
    if (!backgroundLayer) {
        logMessage("WARN", "Background layer (BackgroundImage) not found. Skipping background image replacement.");
    }

    titleLayer.property("Source Text").setValue(postData.title);
    subtitleLayer.property("Source Text").setValue(postData.description);
    logMessage("INFO", "Updated text layers.");

    var imageFile = new File("C:/animeutopia/output/backgroundimage_converted.jpg");
    if (imageFile.exists && backgroundLayer) {
        var importOptions = new ImportOptions(imageFile);
        var imageFootage = app.project.importFile(importOptions);
        backgroundLayer.replaceSource(imageFootage, false);
        logMessage("INFO", "Background image replaced.");
        var compWidth = comp.width;
        var compHeight = comp.height;
        var layerWidth = backgroundLayer.source.width;
        var layerHeight = backgroundLayer.source.height;
        var scaleX = (compWidth / layerWidth) * 100;
        var scaleY = (compHeight / layerHeight) * 100;
        var scaleFactor = Math.max(scaleX, scaleY);
        backgroundLayer.transform.scale.setValue([scaleFactor, scaleFactor]);
        backgroundLayer.transform.position.setValue([compWidth / 2, compHeight / 2]);
        logMessage("INFO", "Background layer scaled and positioned.");
    } else {
        logMessage("WARN", "Background image file not found; skipping background replacement.");
    }

    var renderQueue = app.project.renderQueue;
    var rqItem = renderQueue.items.add(comp);
    logMessage("INFO", "Added composition to render queue.");
    var outputModule = rqItem.outputModule(1);
    var outputFile = new File("C:/animeutopia/output/anime_post.mp4");
    outputModule.file = outputFile;
    outputModule.format = "QuickTime";
    outputModule.videoCodec = "H.264";
    outputModule.includeSourceXMP = false;
    outputModule.audioOutput = true;
    outputModule.audioCodec = "AAC";
    logMessage("INFO", "Output module configured. Output file: " + outputFile.fsName);

    logMessage("INFO", "Starting render...");
    try {
        renderQueue.render();
        logMessage("INFO", "Render completed.");
    } catch (renderError) {
        logMessage("ERROR", "RenderQueue.render() failed: " + renderError.message);
    }

    if (outputFile.exists) {
        logMessage("INFO", "Output file created: " + outputFile.fsName);
    } else {
        logMessage("WARN", "Output file was not created.");
    }
    try {
        var exportFile = new File("C:/animeutopia/output/anime_template_exported.aep");
        app.project.save(exportFile);
        logMessage("INFO", "Project file exported to: " + exportFile.fsName);
    } catch (exportError) {
        logMessage("ERROR", "Error exporting project file: " + exportError.message);
    }
} catch (e) {
    logMessage("ERROR", "Processing error: " + e.message);
}
