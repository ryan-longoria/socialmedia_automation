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

            var titleLayer = doc.artLayers.getByName("Title");
            var subtitleLayer = doc.artLayers.getByName("Description");

            var titleText = postData.title;
            var subtitleText = postData.description;

            adjustFontSizeAndLeadingBasedOnLength(titleLayer, titleText, titleLayer.textItem.size, 70, 10, 1.1, 15);
            adjustFontSizeAndLeadingBasedOnLength(subtitleLayer, subtitleText, subtitleLayer.textItem.size, 60, 5, 4, 3.5);

            var imageUrl = postData.image_url;

            if (imageUrl) {
                var tempFile = new File("/tmp/background_image.jpg");
                var downloadImage = new File(imageUrl);

                var imageDownload = downloadImage.open("r");
                if (imageDownload) {
                    downloadImage.copy(tempFile);
                    var backgroundLayer = doc.artLayers.add();
                    backgroundLayer.kind = LayerKind.NORMAL;
                    var placedImage = doc.artLayers.add();
                    app.load(tempFile);
                }
            }

            var saveFile = new File("anime_post.psd");
            doc.saveAs(saveFile, new PhotoshopSaveOptions(), true);
            doc.close(SaveOptions.DONOTSAVECHANGES);

        } catch (e) {
            alert("Error: " + e.message);
        }
    } else {
        alert("Template file not found at the specified path.");
    }
} else {
    alert("JSON file not found.");
}
