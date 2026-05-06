var entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
  };
function escapeHtml (string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
      return entityMap[s];
    });
};

function formatString (format) {
    var args = Array.prototype.slice.call(arguments, 1);
    return format.replace(/{(\d+)}/g, function(match, number) { 
        return typeof args[number] != 'undefined' ? args[number] : match;
    });
};

function extractScaledWarpedBox(warpedBox, canvasPosition) {
    var warpedBox_ = [];
    for (var i = 0; i < warpedBox.length; ++i) {
        warpedBox_.push((warpedBox[i] * canvasPosition.ratio) + ((i & 1) ? canvasPosition.yoffset : canvasPosition.xoffset));                        
    }
    return warpedBox_;
}

function drawWarpedBox(ctx, warpedBox) {
    ctx.beginPath();
    ctx.moveTo(warpedBox[0], warpedBox[1]);

    ctx.lineTo(warpedBox[2], warpedBox[3]);
    ctx.lineTo(warpedBox[4], warpedBox[5]);
    ctx.lineTo(warpedBox[6], warpedBox[7]);
    ctx.lineTo(warpedBox[0], warpedBox[1]);

    ctx.stroke();
}

function drawCar(ctx, warpedBox, make, model, color) {
    ctx.save();

    ctx.fillStyle = "red";
    ctx.strokeStyle = "red";
    ctx.globalAlpha = 1.0;
    ctx.lineWidth = 5;

    // Draw Bounding box
    ctx.beginPath();
    var halfStrokeWidth = ctx.lineWidth * 0.5;
    ctx.moveTo(warpedBox[0] - halfStrokeWidth, warpedBox[1] - halfStrokeWidth);

    ctx.lineTo(warpedBox[2] + halfStrokeWidth, warpedBox[3] - halfStrokeWidth);
    ctx.lineTo(warpedBox[4] + halfStrokeWidth, warpedBox[5] + halfStrokeWidth);
    ctx.lineTo(warpedBox[6] - halfStrokeWidth, warpedBox[7] + halfStrokeWidth);
    ctx.lineTo(warpedBox[0] - halfStrokeWidth, warpedBox[1] - halfStrokeWidth);
    ctx.stroke();

    // Draw text
    var text = formatString(
        "{0}{1}{2}", 
        make || "Car",
        model ? ", " + model : "",
        color ? ", " + color : ""
    );
     
     ctx.font = "bold 25pt FontANPR";
     var textPos = { x: warpedBox[0], y: (warpedBox[1] - ctx.lineWidth) };
     var textWidth = ctx.measureText(text).width;
     var textSize = { width: textWidth, height: textWidth / (text.length * 0.5) };
 
     ctx.fillStyle = "red";
     ctx.fillRect(textPos.x - ctx.lineWidth, textPos.y - textSize.height, textSize.width + ctx.lineWidth*2, textSize.height + halfStrokeWidth);
 
     ctx.fillStyle = "black";
     ctx.fillText(text, textPos.x, textPos.y);

    ctx.restore();
}

function drawLicensePlateNumber(ctx, warpedBox, text, countryCode) {
    ctx.save();

    // Draw warped box
    ctx.fillStyle = "yellow";
    ctx.strokeStyle = "yellow";
    ctx.globalAlpha = 1.0;
    ctx.lineWidth = 5;

    ctx.beginPath();
    var halfStrokeWidth = ctx.lineWidth * 0.5;
    ctx.moveTo(warpedBox[0] - halfStrokeWidth, warpedBox[1] - halfStrokeWidth);

    ctx.lineTo(warpedBox[2] + halfStrokeWidth, warpedBox[3] - halfStrokeWidth);
    ctx.lineTo(warpedBox[4] + halfStrokeWidth, warpedBox[5] + halfStrokeWidth);
    ctx.lineTo(warpedBox[6] - halfStrokeWidth, warpedBox[7] + halfStrokeWidth);
    ctx.lineTo(warpedBox[0] - halfStrokeWidth, warpedBox[1] - halfStrokeWidth);
    ctx.stroke();

    // Draw text
    ctx.font = "bold 25pt FontANPR";
    var textPos = { x: warpedBox[0], y: (warpedBox[1] - ctx.lineWidth) };
    var textWidth = ctx.measureText(text).width;
    var textSize = { width: textWidth, height: textWidth / (text.length * 0.5) };

    ctx.fillStyle = "yellow";
    ctx.fillRect(textPos.x - ctx.lineWidth, textPos.y - textSize.height, textSize.width + ctx.lineWidth*2, textSize.height + halfStrokeWidth);

    ctx.fillStyle = "black";
    ctx.fillText(text, textPos.x, textPos.y);

    // Draw country code
    if (countryCode) {
        ctx.font = "bold 15pt FontANPR";
        var countryCodePos = { x: warpedBox[6], y: (warpedBox[7] + ctx.lineWidth) };
        var countryCodeWidth = ctx.measureText(countryCode).width;
        var countryCodeSize = { width: countryCodeWidth, height: countryCodeWidth / (countryCode.length * 0.5) };

        ctx.fillStyle = "blue";
        ctx.fillRect(countryCodePos.x - ctx.lineWidth, countryCodePos.y, countryCodeSize.width + ctx.lineWidth*2, countryCodeSize.height + halfStrokeWidth);

        ctx.fillStyle = "white";
        ctx.fillText(countryCode, countryCodePos.x, countryCodePos.y + countryCodeSize.height);
    }

    ctx.restore();
}

function drawMRZLines(ctx, warpedBox, lines) {
    ctx.save();

    ctx.font = "bold 15pt FontOCRB";
    ctx.setLineDash([]);
    ctx.globalAlpha = 0.9;

    var textPos = { x: warpedBox[0], y: (warpedBox[1] - ctx.lineWidth) };
    var halfStrokeWidth = ctx.lineWidth * 0.5;
    
    for (var i = lines.length - 1; i >= 0; --i) {
        var text = lines[i].text;

        var textWidth = ctx.measureText(text).width;
        var textSize = { width: textWidth, height: textWidth / (text.length * 0.5) };

        ctx.fillStyle = "yellow";
        ctx.fillRect(textPos.x - ctx.lineWidth, textPos.y - textSize.height, textSize.width + ctx.lineWidth*2, textSize.height + halfStrokeWidth);

        ctx.fillStyle = "black";
        ctx.fillText(text, textPos.x, textPos.y);

        textPos.y -= textSize.height;
    }

    ctx.restore();
}

function drawMICRLine(ctx, warpedBox, text, klass) {
    ctx.save();

    ctx.font = (klass == 1 ? "bold 20pt FontE13B" : "bold 15pt FontCMC7");
    ctx.globalAlpha = 0.9;

    var textPos = { x: warpedBox[0], y: (warpedBox[1] - ctx.lineWidth) };
    var halfStrokeWidth = ctx.lineWidth * 0.5;

    var textWidth = ctx.measureText(text).width;
    var textSize = { width: textWidth, height: textWidth / (text.length * 0.5) };

    ctx.fillStyle = "yellow";
    ctx.fillRect(textPos.x - ctx.lineWidth, textPos.y - textSize.height, textSize.width + ctx.lineWidth*2, textSize.height + halfStrokeWidth);

    ctx.fillStyle = "black";
    ctx.fillText(text, textPos.x, textPos.y);

    ctx.restore();
}

function drawImageScaled(img, ctx, canvasPosition) {
    const imgw = img.videoWidth || img.width;
    const imgh = img.videoHeight || img.height;
    const canvas = ctx.canvas ;
    const xratio = canvas.width / imgw;
    const yratio =  canvas.height / imgh;
    canvasPosition.ratio  = Math.min ( xratio, yratio );
    canvasPosition.xoffset = ( canvas.width - imgw*canvasPosition.ratio ) * 0.5;
    canvasPosition.yoffset = 0/*( canvas.height - img.height*canvasPosition.ratio ) * 0.5*/; 
    ctx.drawImage(img, 
        0, 0, imgw, imgh, 
        canvasPosition.xoffset, canvasPosition.yoffset, imgw*canvasPosition.ratio, imgh*canvasPosition.ratio
    );
}

function reCAPTCHA_execute(action, callback) {
    if (appsConfig.reCAPTCHA_enabled) {
        try {
            grecaptcha.ready(function() {
                grecaptcha.execute(appsConfig.reCAPTCHA_sitekey, {action: (action || 'null')}).then(function(token) {
                    if (callback && callback instanceof Function) {
                        callback(token);
                    }
                });
            });
        }
        catch (error) {
           console.error(error);
            alert('reCAPTCHA error. You should refresh the page. Please let us know about the issue:' + error);
        }
    }
    else if (callback && callback instanceof Function) {
        callback(null);
    }
}

function turnstile_execute(action, config, callback) {
    if (appsConfig.reCAPTCHA_enabled) {
        try {
            turnstile.execute(
                config['widget-id'],
                {...config, ...{ 'callback': (token) => { callback(token); turnstile.reset(); }, 'action': action }}
            );
        }
        catch (error) {
            console.error(error);
             alert('Turnstile error. You should refresh the page. Please let us know about the issue:' + error);
         }
    }
    else if (callback && callback instanceof Function) {
        callback(null);
    }
}