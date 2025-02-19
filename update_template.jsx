var jsonFile = new File("most_recent_post.json");

if (jsonFile.exists) {
    jsonFile.open("r");
    var jsonData = jsonFile.read();
    jsonFile.close();

    var postData = JSON.parse(jsonData);

    var projectFile = new File("anime_template.aep"); 
    if (projectFile.exists) {
        app.open(projectFile);

        try {
            var comp = null;
            var compName = "standard-news-template";
            for (var i = 1; i <= app.project.items.length; i++) {
                var item = app.project.items[i];
                if (item instanceof CompItem && item.name == compName) {
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
                if (layer.name == "Title") {
                    titleLayer = layer;
                }
                if (layer.name == "Description") {
                    subtitleLayer = layer;
                }
                if (layer.name == "BackgroundImage") {
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

            var imageFile = new File("backgroundimage.jpg");
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
                throw new Error("Background image (backgroundimage.jpg) not found.");
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
