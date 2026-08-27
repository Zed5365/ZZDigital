function handler(event) {
  var request = event.request;
  var host = (request.headers.host && request.headers.host.value || "").toLowerCase();
  if (host === "zzdigitaldesign.com" || host === "www.zzdigitaldesign.com") {
    var qs = request.querystring, parts = [];
    for (var k in qs) {
      if (qs[k].multiValue) { for (var i = 0; i < qs[k].multiValue.length; i++) parts.push(k + "=" + qs[k].multiValue[i].value); }
      else { parts.push(k + "=" + qs[k].value); }
    }
    var query = parts.length ? "?" + parts.join("&") : "";
    return {
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: { "location": { value: "https://websites.vibecraftedsoftware.com" + request.uri + query } }
    };
  }
  return request;
}
