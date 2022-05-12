var scaleFactor    = 1;
var dotbotcolors   = d3.scaleOrdinal(d3.schemeCategory10).range();

var playbuttonMinX     = 175
var playbuttonMaxX     = 285
var playbuttonMinSpeed =  1.00
var playbuttonMaxSpeed =  10.00

function coordinates2pixels(x,y) {
    return (10*x,10*y)
}

function gettingThingsInPlace() {
    // arming click events and tooltips on buttons
    $("#pausebutton").click(function(){
        $.post('pause')
    });
    $("#pausebutton").attr('title', 'Pause the simulation.');
    $("#frameforwardbutton").click(function(){
        $.post('frameforward')
    });
    $("#frameforwardbutton").attr('title', 'Advance the simulation by one event.');
    $("#playbuttonsliderdiv").hover(handlerPlaybuttonsliderdivHoverIn,handlerPlaybuttonsliderdivHoverOut);
    $("#playbuttonslider").hover(handlerPlaybuttonsliderdivHoverIn,handlerPlaybuttonsliderdivHoverOut);
    $("#playbutton").mousedown(slideHandlerMouseDown);
    $("#playbutton").attr('title', 'Drag to set the play speed.');
    $("#playbutton").hover(handlerPlaybuttonsliderdivHoverIn,handlerPlaybuttonsliderdivHoverOut);
    $("#fastforwardbutton").click(function(){
        $.post('fastforward')
    });
    $("#fastforwardbutton").attr('title', 'Simulate as fast as possible.');
}

function getFloorplan() {
    $.getJSON( "/floorplan.json", function( floorplan ) {
        drawFloorplan(floorplan);
    });
}

function drawFloorplan(floorplan) {
    var svg = d3.select("#floorplan");
    
    // determine scalefactor such that map fill entire width of screen
    scaleFactor = ($('body').innerWidth()-5) / floorplan.width;
    
    // scale map to fill up screen
    svg.attr("width",  scaleFactor*floorplan.width)
       .attr("height", scaleFactor*floorplan.height);
    
    // position walls
    svg.selectAll(".obstacle")
        .data(floorplan.obstacles)
        .enter().append("rect")
            .attr("x",      function(d) { return scaleFactor*d.x; })
            .attr("y",      function(d) { return scaleFactor*d.y; })
            .attr("width",  function(d) { return scaleFactor*d.width; })
            .attr("height", function(d) { return scaleFactor*d.height; })
            .attr("class",  "obstacle");
    
    // position buttons and labels
    $("#pagetitle").width(scaleFactor*floorplan.width);
    $("#frameforwardbutton").offset(  { top: scaleFactor*floorplan.height+ 70 });
    $("#fastforwardbutton").offset(   { top: scaleFactor*floorplan.height+ 70 });
    $("#playbuttonsliderdiv").offset( { top: scaleFactor*floorplan.height+ 70 });
    $("#playbuttonslider").offset(    { top: scaleFactor*floorplan.height+ 94 });
    $("#playbuttontooltip").offset(   { top: scaleFactor*floorplan.height+ 45 });
    $("#playbutton").offset(          { top: scaleFactor*floorplan.height+ 70 });
    $("#pausebutton").offset(         { top: scaleFactor*floorplan.height+ 70 });
    $("#timelabel").offset(           { top: scaleFactor*floorplan.height+ 70 });
    $("#versionlabel").offset(
        {
            top:  scaleFactor*floorplan.height+ 70,
            left: scaleFactor*floorplan.width - 190,
        },
    );
}

function getDotBots() {
    $.getJSON( "/dotbots.json", function( data ) {
        drawDotBots(data);
    });
}

function drawDotBots(data) {
    var svg    = d3.select("#floorplan");
    
    // mode
    $("#pausebutton").css(        { opacity: data.mode=='pause'        ? 1.00 : 0.50 });
    $("#frameforwardbutton").css( { opacity: data.mode=='frameforward' ? 1.00 : 0.50 });
    $("#playbutton").css(         { opacity: data.mode=='play'         ? 1.00 : 0.50 });
    $("#fastforwardbutton").css(  { opacity: data.mode=='fastforward'  ? 1.00 : 0.50 });
    
    // timelabel
    $("#timelabel").html(data.simulatedTime);
    
    // positionerror
    var positionerror  = svg.selectAll(".positionerror")
        .data(data.dotbots);
    positionerror
        .attr("x1", function(d) { return scaleFactor*d.x; })
        .attr("y1", function(d) { return scaleFactor*d.y; })
        .attr("x2", function(d) { return scaleFactor*d.orchestratorview_x; })
        .attr("y2", function(d) { return scaleFactor*d.orchestratorview_y; });
    positionerror
        .enter().append("line")
            .attr("x1", function(d) { return scaleFactor*d.x; })
            .attr("y1", function(d) { return scaleFactor*d.y; })
            .attr("x2", function(d) { return scaleFactor*d.orchestratorview_x; })
            .attr("y2", function(d) { return scaleFactor*d.orchestratorview_y; })
            .attr("class", "positionerror");
    
    // orchestratorview
    var orchestratorview = svg.selectAll(".orchestratorview")
        .data(data.dotbots);
    orchestratorview
        .transition()
            .attr("cx", function(d) { return scaleFactor*d.orchestratorview_x; })
            .attr("cy", function(d) { return scaleFactor*d.orchestratorview_y; });
    orchestratorview
        .enter().append("circle")
            .attr("cx", function(d) { return scaleFactor*d.orchestratorview_x; })
            .attr("cy", function(d) { return scaleFactor*d.orchestratorview_y; })
            .attr("class", "orchestratorview")
            .attr("r", 6);
    
    // collisionpath
    var collisionpaths  = svg.selectAll(".collisionpath")
        .data(data.dotbots);
    collisionpaths
        .attr("x1", function(d) { return scaleFactor*d.x; })
        .attr("y1", function(d) { return scaleFactor*d.y; })
        .attr("x2", function(d) { return d.next_bump_x === null ? scaleFactor*d.x : scaleFactor*d.next_bump_x; })
        .attr("y2", function(d) { return d.next_bump_y === null ? scaleFactor*d.y : scaleFactor*d.next_bump_y; });
    collisionpaths
        .enter().append("line")
            .attr("x1", function(d) { return scaleFactor*d.x; })
            .attr("y1", function(d) { return scaleFactor*d.y; })
            .attr("x2", function(d) { return d.next_bump_x === null ? scaleFactor*d.x : scaleFactor*d.next_bump_x; })
            .attr("y2", function(d) { return d.next_bump_y === null ? scaleFactor*d.y : scaleFactor*d.next_bump_y; })
            .attr("class", "collisionpath")
            .attr("stroke",function(d,i){return dotbotcolors[i%10];});
    
    // dotbots
    var dotbots = svg.selectAll(".dotbot")
        .data(data.dotbots);
    dotbots
        .transition()
            .attr("cx", function(d) { return scaleFactor*d.x; })
            .attr("cy", function(d) { return scaleFactor*d.y; });
    dotbots
        .enter().append("circle")
            .attr("cx", function(d) { return scaleFactor*d.x; })
            .attr("cy", function(d) { return scaleFactor*d.y; })
            .attr("class", "dotbot")
            .attr("fill",function(d,i){return dotbotcolors[i%10];})
            .attr("r", 6);
    
    // discomapcomplete
    if (data.discomap.complete==true) {
        $(".discomapline").css( { stroke: 'green' } );
    } else {
        $(".discomapline").css( { stroke: 'red' } );
    }
    
    // discomapdots
    var discomapdots = svg.selectAll(".discomapdot")
        .data(data.discomap.dots);
    discomapdots
        .attr("cx", function(d) { return scaleFactor*d[0]; })
        .attr("cy", function(d) { return scaleFactor*d[1]; });
    discomapdots
        .enter().append("circle")
            .attr("cx", function(d) { return scaleFactor*d[0]; })
            .attr("cy", function(d) { return scaleFactor*d[1]; })
            .attr("class", "discomapdot")
            .attr("r", 2);
    discomapdots
        .exit()
            .remove();
    
    // discomaplines
    var discomaplines  = svg.selectAll(".discomapline")
        .data(data.discomap.lines);
    discomaplines
        .attr("x1", function(d) { return scaleFactor*d[0]; })
        .attr("y1", function(d) { return scaleFactor*d[1]; })
        .attr("x2", function(d) { return scaleFactor*d[2]; })
        .attr("y2", function(d) { return scaleFactor*d[3]; });
    discomaplines
        .enter().append("line")
            .attr("x1", function(d) { return scaleFactor*d[0]; })
            .attr("y1", function(d) { return scaleFactor*d[1]; })
            .attr("x2", function(d) { return scaleFactor*d[2]; })
            .attr("y2", function(d) { return scaleFactor*d[3]; })
            .attr("class", "discomapline");
    discomaplines
        .exit()
            .remove();
    
    // explored cells
    var exploredCells  = svg.selectAll(".exploredCells")
        .data(data.exploredCells.cellsExplored);
    exploredCells
        .attr("x",      function(d) { return scaleFactor*d.x; })
        .attr("y",      function(d) { return scaleFactor*d.y; })
        .attr("width",  function(d) { return scaleFactor*d.width; })
        .attr("height", function(d) { return scaleFactor*d.height; });
    exploredCells.enter().append("rect")
            .attr("x",      function(d) { return scaleFactor*d.x; })
            .attr("y",      function(d) { return scaleFactor*d.y; })
            .attr("width",  function(d) { return scaleFactor*d.width; })
            .attr("height", function(d) { return scaleFactor*d.height; })
            .attr("class",  "exploredCells");
    exploredCells
        .exit()
            .remove();
    var exploredCellsObstacle  = svg.selectAll(".exploredCellsObstacle")
        .data(data.exploredCells.cellsObstacle);
    exploredCellsObstacle
        .attr("x",      function(d) { return scaleFactor*d.x; })
        .attr("y",      function(d) { return scaleFactor*d.y; })
        .attr("width",  function(d) { return scaleFactor*d.width; })
        .attr("height", function(d) { return scaleFactor*d.height; });
    exploredCellsObstacle.enter().append("rect")
            .attr("x",      function(d) { return scaleFactor*d.x; })
            .attr("y",      function(d) { return scaleFactor*d.y; })
            .attr("width",  function(d) { return scaleFactor*d.width; })
            .attr("height", function(d) { return scaleFactor*d.height; })
            .attr("class",  "exploredCellsObstacle");
    exploredCellsObstacle
        .exit()
            .remove();
}


function handlerPlaybuttonsliderdivHoverIn(e) {
    $("#playbuttonslider").css( { opacity: 0.30 } );
}

function handlerPlaybuttonsliderdivHoverOut(e) {
    $("#playbuttonslider").css( { opacity: 0.10 } );
}

function slideHandlerMouseDown(e) {
    
    // avoid default event
    e = e || window.event;
    e.preventDefault();
    
    // arm handlers
    document.onmousemove = slideHandlerMouseMove;
    document.onmouseup   = slideHandlerMouseUp;
}

function slideHandlerMouseMove(e) {
    
    // avoid default event
    e = e || window.event;
    e.preventDefault();
    
    // record mouse position
    newX = e.clientX;
    
    // move play button
    if (newX<playbuttonMinX) {newX=playbuttonMinX};
    if (newX>playbuttonMaxX) {newX=playbuttonMaxX};
    $("#playbutton").offset({ left: newX-25 });
    
    // compute current speed setting
    portion = (newX-playbuttonMinX) / (playbuttonMaxX-playbuttonMinX)
    speed   = Math.round(playbuttonMinSpeed + portion*(playbuttonMaxSpeed-playbuttonMinSpeed));
    
    // display tootip
    $("#playbuttontooltip").offset({ left: newX-20 });
    $("#playbuttontooltip").html(speed+' x');
}

function slideHandlerMouseUp(e) {
    
    // avoid default event
    e = e || window.event;
    e.preventDefault();
    
    // disarm handlers
    document.onmousemove = null;
    document.onmouseup   = null;
    
    // remove tootip
    $("#playbuttontooltip").html('');
    $("#playbuttontooltip").offset({ left: -100 });
    
    
    // determine speed
    buttonX = $("#playbutton").position().left+25;
    portion = (buttonX-playbuttonMinX) / (playbuttonMaxX-playbuttonMinX)
    speed   = playbuttonMinSpeed + portion*(playbuttonMaxSpeed-playbuttonMinSpeed);
    
    // send command
    $.ajax({
        type:           "POST",
        url:            'play',
        contentType:    'application/json',
        data:           JSON.stringify({
            'speed':    speed,
        })
    });
}
