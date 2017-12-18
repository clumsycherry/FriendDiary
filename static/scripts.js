$(document).ready(function() {
    $('input.city').typeahead({
        name: 'city',
        remote: 'city.php?query=%QUERY'
    });
});

// configure typeahead
$("#q").typeahead({
    highlight: false,
    minLength: 1
},
{
    display: function(suggestion) { return null; },
    limit: 10,
    source: search,
    templates: {
        suggestion: Handlebars.compile(
            "<div>{{place_name}}, {{admin_name1}}, {{postal_code}}</div>"
        )
    }
});


function search(query, syncResults, asyncResults)
{
    // get places matching query (asynchronously)
    var parameters = {
        q: query
    };
    $.getJSON(Flask.url_for("search"), parameters)
    .done(function(data, textStatus, jqXHR) {

        // call typeahead's callback with search results (i.e., places)
        asyncResults(data);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());

        // call typeahead's callback with no results
        asyncResults([]);
    });
}