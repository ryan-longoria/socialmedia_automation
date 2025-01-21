if (typeof JSON === "undefined") { 
    var JSON = {
        parse: function (str) {
            return eval('(' + str + ')');
        },
        stringify: function (obj) {
            var t = typeof(obj);
            if (t != "object" || obj === null) {
                if (t == "string") obj = '"' + obj + '"';
                return String(obj);
            } else {
                var n, v, json = [], arr = (obj && obj.constructor == Array);
                for (n in obj) {
                    v = obj[n];
                    t = typeof(v);
                    if (t == "string") v = '"' + v + '"';
                    else if (t == "object" && v !== null) v = JSON.stringify(v);
                    json.push((arr ? "" : '"' + n + '":') + String(v));
                }
                return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}"); 
            } 
        }
    };
}

var jsonFile = new File("most_recent_post.json");

if (jsonFile.exists) {
    jsonFile.open("r");
    var jsonData = jsonFile.read();
    jsonFile.close();

    var postData = JSON.parse(jsonData);

    var templateFile = new File("standard-news-template.psd");
    if (templateFile.exists) {
        var doc = app.open(templateFile);

        try {
            // Function to adjust font size and leading based on the length of the text
            function adjustFontSizeAndLeadingBasedOnLength(layer, text, baseFontSize, baseLeading, fontSizeReduction, leadingReduction, reductionFactor) {
                if (layer.kind !== LayerKind.TEXT) {
                    throw new Error("Layer is not a text layer.");
                }

                var textLength = text.length;
                var fontSize = baseFontSize + 25;
                var leading = baseLeading;

                var reduction = Math.floor(textLength / reductionFactor);
                fontSize -= reduction * fontSizeReduction;

                leading -= (reduction - 15) * leadingReduction;

                if (fontSize < 10) fontSize = 10;
                if (leading < 10) leading = 10;

                layer.textItem.kind = TextType.PARAGRAPHTEXT;
                layer.textItem.size = fontSize;
                layer.textItem.leading = leading;
                layer.textItem.contents = text;

                return layer;
            }

            // Fetch the layers from the template
            var titleLayer = doc.artLayers.getByName("Title");
            var subtitleLayer = doc.artLayers.getByName("Description");

            // Update the text content with font size and leading adjustments
            var titleText = postData.title;
            var subtitleText = postData.description;

            adjustFontSizeAndLeadingBasedOnLength(titleLayer, titleText, titleLayer.textItem.size, 70, 15, 1.1, 15); 
            adjustFontSizeAndLeadingBasedOnLength(subtitleLayer, subtitleText, subtitleLayer.textItem.size, 60, 5, 4, 3.5);

            // Path to the image file
            var imageFile = new File("backgroundimage.jpg");

            if (imageFile.exists) {
                // Open the image as a new document
                var imgDoc = open(imageFile);

                // Duplicate the first layer of the opened image to the target document
                var duplicatedLayer = imgDoc.artLayers[0].duplicate(doc, ElementPlacement.PLACEATBEGINNING);

                // Close the opened image document without saving
                imgDoc.close(SaveOptions.DONOTSAVECHANGES);

                // Ensure the image layer is at the bottom of the layer stack
                var allLayers = doc.artLayers;
                
                // Move the image layer to the very bottom of the layer stack
                duplicatedLayer.move(allLayers[allLayers.length - 1], ElementPlacement.PLACEAFTER);

                // Resize the image layer to match document width and height (after ensuring it’s positioned behind)
                var imgLayer = duplicatedLayer;
                var docWidth = doc.width;
                var docHeight = doc.height;

                // Resize the image without scaling percentages (direct pixel resizing)
                var imgWidth = imgLayer.bounds[2] - imgLayer.bounds[0];
                var imgHeight = imgLayer.bounds[3] - imgLayer.bounds[1];

                // Calculate the scaling factor
                var scaleWidth = (docWidth / imgWidth) * 100;
                var scaleHeight = (docHeight / imgHeight) * 100;

                // Resize the image proportionally
                imgLayer.resize(scaleWidth, scaleHeight);

                // Position the image to fill the canvas (if necessary)
                var translateX = new UnitValue(-(imgLayer.bounds[0] - 0), 'px');
                var translateY = new UnitValue(-(imgLayer.bounds[1] - 0), 'px');

                // Apply the translation
                imgLayer.translate(translateX, translateY);

            } else {
                alert("The image file does not exist at the specified path.");
            }

            // Save the document with the new background layer
            var saveFile = new File("anime_post.psd");
            doc.saveAs(saveFile, new PhotoshopSaveOptions(), true);
            doc.close(SaveOptions.DONOTSAVECHANGES);

        } catch (e) {
            alert("Error: " + e.message);
        }
    } else {
        alert("Template file not found.");
    }
} else {
    alert("JSON file not found.");
}
