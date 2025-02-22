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
            // Split HTTP headers from content
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
            return true;
        } else {
            throw new Error("Unable to open socket connection.");
        }
    } catch(e) {
        alert("Download failed: " + e.message);
        return false;
    }
}

// Define the S3 URL (update with your bucket name and region as needed)
var s3JsonUrl = "https://your-s3-bucket.s3.amazonaws.com/most_recent_post.json";
var localJsonPath = "most_recent_post.json";

// Download the JSON file from S3 if it does not exist locally
var jsonFile = new File(localJsonPath);
if (!jsonFile.exists) {
    var success = downloadFromUrl(s3JsonUrl, localJsonPath);
    if (!success) {
        alert("Failed to download JSON from S3.");
        // Exit script if JSON cannot be obtained
        return;
    }
}

if (jsonFile.exists) {
    jsonFile.open("r");
    var jsonData = jsonFile.read();
    jsonFile.close();

    var postData = JSON.parse(jsonData);

    var projectFile = new File("/animeutopia/anime_template.aep"); 
    if (projectFile.exists) {
        app.open(projectFile);

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
                throw new Error("Composition 'standard-news-template' not found in the After Effects project.");
            }

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
                throw new Error("Background layer (BackgroundImage) not found in the composition.");
            }

            titleLayer.property("Source Text").setValue(postData.title);
            subtitleLayer.property("Source Text").setValue(postData.description);

            var imageFile = new File("backgroundimage_converted.jpg");
            if (imageFile.exists) {
                var importOptions = new ImportOptions(imageFile);
                var imageFootage = app.project.importFile(importOptions);

                backgroundLayer.replaceSource(imageFootage, false);

                var compWidth = comp.width;
                var compHeight = comp.height;
                var layerWidth = backgroundLayer.source.width;
                var layerHeight = backgroundLayer.source.height;

                var scaleX = (compWidth / layerWidth) * 100;
                var scaleY = (compHeight / layerHeight) * 100;

                var scaleFactor = Math.max(scaleX, scaleY);
                backgroundLayer.transform.scale.setValue([scaleFactor, scaleFactor]);

                backgroundLayer.transform.position.setValue([compWidth / 2, compHeight / 2]);
            } else {
                throw new Error("Background image (backgroundimage_converted.jpg) not found.");
            }

            var renderQueue = app.project.renderQueue;
            var rqItem = renderQueue.items.add(comp);

            var outputModule = rqItem.outputModule(1);

            outputModule.file = new File("anime_post.mp4");

            outputModule.format = "QuickTime";
            outputModule.videoCodec = "H.264";
            outputModule.includeSourceXMP = false; 
            outputModule.audioOutput = true; 
            outputModule.audioCodec = "AAC"; 

            renderQueue.render();
        } catch (e) {
            alert("Error: " + e.message);
        }
    } else {
        alert("After Effects project file (.aep) not found.");
    }
} else {
    alert("JSON file not found.");
}
