function coordinates2pixels(x,y) {
    return (10*x,10*y)
}

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
        drawFloorplan(floorplan);
    });
}

function drawFloorplan(floorplan) {
    var svg = d3.select("#floorplan");
    
    // scale map to fill up screen
    svg.attr("width",  400)
       .attr("height", 300);
    
    // position walls
    /*
    svg.append("rect")
        .attr("id","svglegend")
        .attr("x",      100)
        .attr("y",      50)
        .attr("width",  200)
        .attr("height", 100)
    */
}

function getDotBots() {
    $.getJSON( "/dotbots.json", function( dotbots ) {
        drawDotBots(dotbots.dotbots);
    });
}

function drawDotBots(dotbots) {
    var svg    = d3.select("#floorplan");
    var circle = svg.selectAll("circle")
        .data(dotbots);
    
    // position DotBots
    circle
        .transition()
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });
    circle
        .enter().append("circle")
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; })
            .attr("r", 2.5);
}
