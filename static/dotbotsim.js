var scaleFactor = 1;

function coordinates2pixels(x,y) {
    return (10*x,10*y)
}

function gettingThingsInPlace() {
    $("#nextbutton").click(function(){
        $.post('next')
    });
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
    
    // determine scalefactor such that map fill entire width of screen
    scaleFactor = ($('body').innerWidth()-50) / floorplan.width;
    
    // scale map to fill up screen
    svg.attr("width",  scaleFactor*floorplan.width)
       .attr("height", scaleFactor*floorplan.height);
    
    // position walls
    svg.selectAll("rect")
        .data(floorplan.obstacles)
        .enter().append("rect")
            .attr("x",      function(d) { return scaleFactor*d.x; })
            .attr("y",      function(d) { return scaleFactor*d.y; })
            .attr("width",  function(d) { return scaleFactor*d.width; })
            .attr("height", function(d) { return scaleFactor*d.height; })
            .attr("class",  "obstacle");
}

function getDotBots() {
    $.getJSON( "/dotbots.json", function( dotbots ) {
        drawDotBots(dotbots.dotbots);
    });
}

function drawDotBots(dotbots) {
    var svg    = d3.select("#floorplan");
    
    // position collisionpath
    var line   = svg.selectAll("line")
        .data(dotbots);
    line
        .attr("x1", function(d) { return scaleFactor*d.x; })
        .attr("y1", function(d) { return scaleFactor*d.y; })
        .attr("x2", function(d) { return d.next_bump_x === null ? scaleFactor*d.x : scaleFactor*d.next_bump_x; })
        .attr("y2", function(d) { return d.next_bump_y === null ? scaleFactor*d.y : scaleFactor*d.next_bump_y; });
    line
        .enter().append("line")
            .attr("x1", function(d) { return scaleFactor*d.x; })
            .attr("y1", function(d) { return scaleFactor*d.y; })
            .attr("x2", function(d) { return d.next_bump_x === null ? scaleFactor*d.x : scaleFactor*d.next_bump_x; })
            .attr("y2", function(d) { return d.next_bump_y === null ? scaleFactor*d.y : scaleFactor*d.next_bump_y; })
            .attr("class", "collisionpath");
    
    // position DotBots
    var circle = svg.selectAll("circle")
        .data(dotbots);
    circle
        .transition()
            .attr("cx", function(d) { return scaleFactor*d.x; })
            .attr("cy", function(d) { return scaleFactor*d.y; });
    circle
        .enter().append("circle")
            .attr("cx", function(d) { return scaleFactor*d.x; })
            .attr("cy", function(d) { return scaleFactor*d.y; })
            .attr("class", "dotbot")
            .attr("r", 6);
}
