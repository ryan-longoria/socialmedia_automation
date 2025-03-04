#include "json2.jsx"

/**
 * Custom logging function to output messages to the ExtendScript console and a log file.
 *
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
 *
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

var s3JsonUrl = "https://prod-animeutopia-media-bucket.s3.us-east-2.amazonaws.com/most_recent_post.json?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjELz%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMiJHMEUCIQCqocHz6jk4P0YiPM1y%2FA%2Fnv7TA5uQpsXTOl0UabA5CjwIgH5Pr09gNEG3XFMG13jFHk2eE4kiHfoZOaifoEx1zfm8qygMI9f%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARAAGgw0ODE2NjUwODQ0NzciDAOpPD5Jb3glG6UvuCqeA1Z%2BabMknXWcZGOZV5GDjL0erfZ%2FXn9g2iyivTb3RMz%2FEZSkYZsBypVD7yGGRg956pMV1isv1ro1WUeb7z4nKfn9x6Rxat3HZU3mY3KiXqfLUxzhyeueXnjAIIGq3ESUrfVVMGzuwgvbrF4lTxfsKArF4CdvvHmX6z4C4BL5DbscMhF5mD%2BB974bOYLiSnzZy3CReK3qrM4MIEXzi%2B0KrBVE0Q2NMgZFQNctsOfkwIEFqkFK%2BXVN%2FjoisC%2BNPwRdH4fj25h2a6jymmdMh%2FDMJkt8PF%2BDJuhUdRUZFuxohc0wZaY%2Frm3c88MU4XoQ7ECS9nxKkaU3ZG5SiWjgQiMxNo%2FINPllCQ7cQIsZ35CYt3oJ%2Bn1Fb4Z2l9pPKN%2FzXJSXkft0%2BxGGePefM6QtwGS8SArJ6J5uanOH0QsUF6eFnzD8Wjbi2JRy1saTqEEQIpYRqqZ1axmB0%2BR09aJz5qfiULsTE%2BHdNpE00jVsIGJP6uUkORa8kAlXfk8jgCWUnOUTJChjv%2B7%2FSSBcEMNrsKCxKtbWuLWr%2FgqtwsZIb%2Fwi9jD5rZ2%2BBjq3ArIZH7iwBv5KhXGzeb%2BQ5GMbcn%2FXjLsm3PLulH%2FiIm2YyOVQdxDmovEoV2UBRZCGA0Cejb5LCM4UQ8aAqKJFCak7Rd6eIj3JzJEnrdAsXGIjhnHPrqk9Cw9BgaFIqeNM7UZJ1I%2BeQs5vFUkNnF4iwLhEYG%2F6TkU0D%2BU5CKcgKzRN5JVoIpLnhYToOch7i5QZjoRN%2FoJtyOF9RoHIrNyx5DIfy8eVMFsZtLtBIIH%2BEnEo64R23ZCUOP5P51YqQXKhNzmHFV%2FAMiOy8jWmes0ZxMgWE5nW%2FqXO4HMWzpFG4rQ%2B5apY0pF9h07b3xDuC%2FUj0G4UFHlyZfE2xDN0nYWnlhaAvHfkx6qcRl%2FR2Wo30oj0vcEiLz4DheG3UmP6HeJkA42VBWR9z33oZikBF09QUafSQdWv03FT&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAXAJLZ5Q646VAZ53Q%2F20250304%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250304T194840Z&X-Amz-Expires=43200&X-Amz-SignedHeaders=host&X-Amz-Signature=3f9cf007583f0e2502344af42b0d0811b32748563ff47e3a4d2c8a584fb34430";
var localJsonPath = "C:/animeutopia/output/most_recent_post.json";

var jsonFile = new File(localJsonPath);
if (!jsonFile.exists) {
    var success = downloadFromUrl(s3JsonUrl, localJsonPath);
    if (!success) {
        logMessage("ERROR", "Failed to download JSON from S3.");
        throw new Error("Failed to download JSON from S3. Exiting script execution.");
    }
}

if (jsonFile.exists) {
    jsonFile.open("r");
    var jsonData = jsonFile.read();
    jsonFile.close();

    var postData = JSON.parse(jsonData);
    logMessage("INFO", "JSON data loaded: Title = " + postData.title);

    var projectFile = new File("C:/animeutopia/anime_template.aep"); 
    if (projectFile.exists) {
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
            if (!titleLayer) { throw new Error("Title layer not found."); }
            if (!subtitleLayer) { throw new Error("Description layer not found."); }
            if (!backgroundLayer) { 
                logMessage("WARN", "Background layer (BackgroundImage) not found. Skipping background image replacement."); 
            }

            titleLayer.property("Source Text").setValue(postData.title);
            subtitleLayer.property("Source Text").setValue(postData.description);
            logMessage("INFO", "Updated text layers.");

            var imageFile = new File("C:/animeutopia/output/backgroundimage_converted.jpg");
            if (imageFile.exists) {
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
                logMessage("INFO", "RenderQueue.render() completed.");
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
    } else {
        logMessage("ERROR", "After Effects project file (.aep) not found.");
    }
} else {
    logMessage("ERROR", "JSON file not found.");
}
