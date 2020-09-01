<!doctype html>

<meta charset="utf-8">
<title>{{pagetitle}}</title>

<link   rel="stylesheet" href="/static/dotbotsim.css">
<script src="/static/d3.min.js"></script>
<script src="/static/jquery-3.5.1.min.js" charset="utf-8"></script>
<script src="/static/dotbotsim.js" charset="utf-8"></script>

<div id="pagetitle">{{pagetitle}}</div>
<svg id="floorplan"></svg>
<img id="nextbutton"         src="/static/button_next.svg"/>
<img id="fastforwardbutton"  src="/static/button_fastforward_inactive.svg"/>
<img id="playbutton"         src="/static/button_play_inactive.svg"/>
<img id="pausebutton"        src="/static/button_pause_inactive.svg"/>
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