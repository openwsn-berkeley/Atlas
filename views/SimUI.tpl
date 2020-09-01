<!doctype html>

<meta charset="utf-8">
<title>{{pagetitle}}</title>

<link   rel="stylesheet" href="/static/dotbotsim.css">
<script src="/static/d3.min.js"></script>
<script src="/static/jquery-3.5.1.min.js" charset="utf-8"></script>
<script src="/static/dotbotsim.js" charset="utf-8"></script>

<div id="pagetitle">{{pagetitle}}</div>
<svg id="floorplan"></svg>
<div id="nextbutton">Next</div>
<div id="playbutton">Play</div>
<div id="pausebutton">Pause</div>
<div id="timelabel">poipoi</div>
<div id="versionlabel">version {{version}}</div>

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