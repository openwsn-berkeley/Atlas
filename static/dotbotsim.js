function gettingThingsInPlace() {
    $("#playbutton").click(function(){
        $.post('play')
    });
    $("#pausebutton").click(function(){
        $.post('pause')
    });
}

function getFloorplan() {
    $.getJSON( "/floorplan.json", function( floorplan ) {
        console.log(floorplan);
    });
}

function getRobotPositions() {
    $.getJSON( "/robotpositions.json", function( robotpositions ) {
        console.log(robotpositions);
    });
}