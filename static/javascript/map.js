//function to get user's location, used in case customer has not enetered an address
function getLocation(){

    //check if the user has added an address
    if ($('input[name="address"]').val().length > 0){
        return $('input[name="address"]').val();
    } else {
        if (navigator.geolocation) {
            show('loading', true);
            navigator.geolocation.getCurrentPosition(showPosition,showError);
            function checkLocationValue() {
                if($('input[name="address"]').val().length === 0) {//we want to wait till the html is updated
                    setTimeout(checkLocationValue, 250);//wait 250 millisecnds then recheck
                }
                else{
                    show('loading', false);
                    return $('input[name="address"]').val();
                }
            }
            checkLocationValue();
        } else {
            alert("Geolocation is not supported by this browser.");
            return "";
        }
    }
    //show('loading', false);
}

//call back function for getCurrent position
function showPosition(position) {
    //x.innerHTML = "Latitude: " + position.coords.latitude +
    //"<br>Longitude: " + position.coords.longitude;
    $('input[name="address"]').attr('value', position.coords.latitude + "," + position.coords.longitude);
    $('input[name="address"]').attr('readonly', true);
}

function setMap() {

        origin_ = getLocation();
        console.log(origin_)

        if (typeof origin_ === 'undefined'){
            setTimeout(setMap, 250);//wait 250 millisecnds then rerun the function
        }else{
            newSRC(origin_);
        }
    }

function showError(error) {
        switch(error.code) {
        case error.PERMISSION_DENIED:
          //x.innerHTML = "User denied the request for Geolocation.";
          alert("Enter your address");
          break;
        case error.POSITION_UNAVAILABLE:
          //x.innerHTML = "Location information is unavailable."
          alert("Location information is unavailable.")
          break;
        case error.TIMEOUT:
          //x.innerHTML = "The request to get user location timed out."
          alert("The request to get user location timed out.")
          break;
        case error.UNKNOWN_ERROR:
          //x.innerHTML = "An unknown error occurred."
          alert("An unknown error occurred.")
          break;
        }
    }

function slider(optionSelected){
    var deferred = $.Deferred();
    var selectedValue = optionSelected;
    if (selectedValue === 'hospitals'){

        $.getJSON($SCRIPT_ROOT + '/hospitalWaitTimes', {}, function(data) {
            $("#radioButtons").html(data.table);
            deferred.resolve(true);
        });
    }
    else if (selectedValue === 'medicentres'){

        $.getJSON($SCRIPT_ROOT + '/medicentreWaitTimes', {}, function(data) {
            $("#radioButtons").html(data.table);
            deferred.resolve(true);
        });
    }
    else if (selectedValue === 'other'){

        $.getJSON($SCRIPT_ROOT + '/otherClinics', {}, function(data) {
            $("#radioButtons").html(data.table);
            deferred.resolve(true);
        });
    }
    else{
        deferred.resolve(true);
    }

    return deferred.promise();
}

$(function() {
  $(".sidenav a").on("click", function() {
    $(".sidenav a").removeClass("active");
    $(this).addClass("active");
    slider(this.getAttribute('value'));
  });
});

function recommend(){

    origin_ = getLocation();
    console.log(origin_)

    if (typeof origin_ === 'undefined'){
        setTimeout(recommend, 250);//wait 250 millisecnds then rerun the function
    }else{

        console.log(origin_);

        if (origin_){
            show('loading', true);
            var getRecommendation = function(e) {
              $.getJSON($SCRIPT_ROOT + '/recommend', {
                origin: origin_
              }, function(data) {
                var where = data.where;
                var type = data.type;
                var time_ = data.bestTime;
                var promise = slider(type);
                //console.log(type);
                console.log(where);
                //console.log(typeof(where));
                console.log(time_);
                promise.then(function(result) {
                    if (type == null){
                        alert("Please review your address.");
                        show('loading', false);
                    } else{
                        $('label:contains(' + where +')').children()[0].checked = true;
                        newSRC(origin_);
                        $('#recommend').html('<p>Recommendation: ' + where + '<\p><p>You will be seen by approximately ' + time_ + '<\p>');
                        show('loading', false);
                    }
                });
              });
              return false;
            };

            getRecommendation();
        }
    }
}

function newSRC(origin){

        if (typeof $('input[name="optradio"]:checked').val() != 'undefined'){
            //console.log(api);
            url = "https://www.google.com/maps/embed/v1/directions" +
                        "?key=" + encodeURIComponent(api) +
                        "&origin=" + encodeURIComponent(origin) +
                        "&destination=" + encodeURIComponent($('input[name="optradio"]:checked').val()) +
                        "&mode=transit" +
                        "&avoid=tolls|highways";
            console.log($('input[name="optradio"]:checked').val());
            console.log(url);
            document.getElementById('iFrame').setAttribute('src', url);
        } else {
            //check if the user has selected a clinic, if not then throw an alert.
            alert("Make a selection or Get a recommendation")
        }

    }

function show(id, value) {
    document.getElementById(id).style.display = value ? 'block' : 'none';
}