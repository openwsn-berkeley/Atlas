<!doctype html>

<meta charset="utf-8">
<title>{{pagetitle}}</title>

<link   rel="stylesheet" href="/static/dotbotsim.css">
<script src="/static/jquery-3.5.1.min.js" charset="utf-8"></script>
<script src="/static/dotbotsim.js" charset="utf-8"></script>

<h1  id="pagetitle">{{pagetitle}}</h1>
<div id="floorplan" on></div>
<div id="playbutton"></div>
<div id="pausebutton"></div>
<div id="versionLabel"><p>{{version}}</p></div>

<script id="js">
    $(document).ready(function() {
        gettingThingsInPlace();
        getFloorplan();
        getRobotPositions();
        // periodically refresh
        setInterval(function() {
            getRobotPositions()
        }, 1000);
    });
</script>