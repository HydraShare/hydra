
// read uri
function parseUri(){

    var inputParameters = { keywords : [] };

    // parse Uri
    var pars = window.location.search.replace("?","").split("&");

    if (pars[0]=="") return [];

    pars.forEach(function(d){
        keyValue = d.split("=");
        inputParameters[keyValue[0].toLowerCase()].push(decodeURIComponent(keyValue[1]));
    });

    keywords = inputParameters.keywords;
    return keywords;
}


function loadHydras(){
    // variable to hold request
    var request;

    // abort any pending request
    if (request) {
      request.abort();
    }

    // fire off the request to /form.php
    request = $.ajax({
      url: "https://script.google.com/macros/s/AKfycbxiRnl-119Qy-Ygchrjp5OiMelYUJCZ-ZHjpwKTm6dtaYCOZ9IZ/exec",
      type: "post"
    });

    // callback handler that will be called on success
    request.done(function (response, textStatus, jqXHR){
      // log a message to the console
      examples = response.samples;

      // update header for the last time that Hydras are loaded
      var hydras_last_loaded = parseDate(response.last_updated);
      d3.selectAll("span#last_updated").text(" last updated at " + hydras_last_loaded);

      // assume it's all visible
      visibility = Array.apply(null, Array(examples.length)).map(function(){return 1});

      examples.forEach(function(d, i) {
        d.created_at = parseDate(d.created_at);
        d.modified_at = parseDate(d.modified_at);
        d.visibility = "visible";
        d.position = "";
      });

      // filter on load
      display(null, filter());
    });

    // callback handler that will be called on failure
    request.fail(function (jqXHR, textStatus, errorThrown){
      // report error
      alert("The following error occured: " + textStatus + errorThrown);
    });
}


function sortHydras(sortBy){
  if (sortBy == "id"){
    d3.select(".examples")
      .selectAll(".example")
        .sort(function(a, b) {
          if(a[sortBy].toLowerCase().trim() < b[sortBy].toLowerCase().trim()) return -1;
          if(a[sortBy].toLowerCase().trim() > b[sortBy].toLowerCase().trim()) return 1;
          return 0;
          });
  } else {
    d3.select(".examples")
      .selectAll(".example")
        .sort(function(a, b) {
          if(a[sortBy] < b[sortBy]) return 1;
          if(a[sortBy] > b[sortBy]) return -1;
          return 0;
          });
  }
}

function sorData(data, sortBy){
  if (sortBy == "id"){
    data.sort(function(a, b) {
          if(a[sortBy].toLowerCase().trim() < b[sortBy].toLowerCase().trim()) return -1;
          if(a[sortBy].toLowerCase().trim() > b[sortBy].toLowerCase().trim()) return 1;
          return 0;
          });
  } else {
    data.sort(function(a, b) {
          if(a[sortBy] < b[sortBy]) return 1;
          if(a[sortBy] > b[sortBy]) return -1;
          return 0;
          });
  }

  return data;
}

function getKeywords(){
    return d3.select("#filtering").node().value.split(",");
}

function filter(){
    if (page==0){
      // re-set everything
      keywords = getKeywords();

      // filter examples
      if (keywords.length == 0 || keywords.join("").trim()==""){
        data = examples;
      } else {
        data = examples.filter(function (d){
          for (var j=0; j<keywords.length; j++){
              if (d.tags.includes(keywords[j].toLowerCase())) return true;
          }
          return false;
        });
      }
      // sort data
      data = sorData(data, sortBy);
    }

    return feedData(data);
}

function feedData(data){

    if (!data.length){
      // there is no results
      page = -1;
      d3.select(".loading").text("No Hydra found for " + keywords.join(", ") +" Sorry! :(. Try a different keyword.");
      return [];

    } else if (data.length < objectPerPage * (page + 1)) {
      // all visible data is less than image count
      // show all of them
      return data;
    } else {
      // return the portion for this page
      return data.slice(0, objectPerPage * (page + 1));
    }
}
