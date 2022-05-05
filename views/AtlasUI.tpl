<!doctype html>

<meta charset="utf-8">
<title>{{pagetitle}}</title>

<link   rel="stylesheet" href="/static/dotbotsim.css">
<script src="/static/d3.min.js"></script>
<script src="/static/jquery-3.5.1.min.js" charset="utf-8"></script>
<script src="/static/dotbotsim.js" charset="utf-8"></script>

<div id="pagetitle"><strong>DOTBOT</strong>SIMULATOR</div>
<svg id="floorplan"></svg>
<div id="timelabel"></div>
<div id="versionlabel">version {{version}}</div>
<img id="pausebutton"        src="/static/button_pause.svg"/>
<img id="frameforwardbutton" src="/static/button_frameforward.svg"/>
<div id="playbuttontooltip"></div>
<div id="playbuttonsliderdiv"></div>
<div id="playbuttonslider"></div>
<img id="playbutton"         src="/static/button_play.svg"/>
<img id="fastforwardbutton"  src="/static/button_fastforward.svg"/>

<script id="js">
    $(document).ready(function() {
        gettingThingsInPlace();
        getFloorplan();
        getDotBots();
        // periodically refresh
        setInterval(function() {
            getDotBots()
        }, 100);
    });
</script>