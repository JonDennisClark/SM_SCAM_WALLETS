function youTubeScraping() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var active = sheet.getActiveSheet();

  var allResults = [];
  var nextPageToken = '';

  do {
    var search = YouTube.Search.list("snippet,id", {q: "xAI token", maxResults: 50, pageToken: nextPageToken});

    var results = search.items.map(function(item) {
      return [item.id.channelId, item.id.videoId, item.snippet.title, item.snippet.publishedAt, item.snippet.description];
    });
    
    allResults = allResults.concat(results);

    nextPageToken = search.nextPageToken;

  } while (nextPageToken);

  if (allResults.length > 0) {
    active.getRange(2, 1, allResults.length, allResults[0].length).setValues(allResults);
  }
}
