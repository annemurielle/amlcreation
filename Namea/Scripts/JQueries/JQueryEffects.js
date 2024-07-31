    $(function () {
        $(".tabs").tabs();
    });

    $(function () {
        $(".dialog").dialog();
    });

    $(function () {
        $(".accordion").accordion();
    });
    
    $(function () {
        // run the currently selected effect
        // get effect type from 

        // most effect types need no options passed by default
        var options = {};
        // some effects have required parameters

        // run the effect
        $(".togglerblind").toggle("blind", options, 500);
        $(".togglerbounce").toggle("bounce", options, 500);
        $(".togglerclip").toggle("clip", options, 500);
        $(".togglerdrop").toggle("drop", options, 500);
        $(".togglerexplode").toggle("explode", options, 500);
        $(".togglerfold").toggle("fold", options, 500);
        $(".togglerhighlight").toggle("highlight", options, 500);
        $(".togglerpuff").toggle("puff", options, 500);
        $(".togglerpulsate").toggle("pulsate", options, 500);
        $(".togglershake").toggle("shake", options, 500);
        $(".togglerslide").toggle("slide", options, 500);

        options = { percent: 0 };

        $(".togglerscale").toggle("scale", options, 500);

        options = { to: { width: 200, height: 60} };

        $(".togglersize").toggle("size", options, 500);


    });

