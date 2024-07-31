
    $(document).ready(function () {

        // This initialises carousels on the container elements specified, in this case, carousel1.
        $("#carousel1").CloudCarousel(
		{

		    reflHeight: 56,
		    reflGap: 2,
		    buttonLeft: $("#left-but"),
		    buttonRight: $("#right-but"),
		    altBox: $("#alt-text"),
		    titleBox: $("#title-text"),
		    yRadius: 200,
		    xPos: 450,
		    yPos: 200,
		    speed: 0.15,
		    mouseWheel: true
		}
	);
    });

