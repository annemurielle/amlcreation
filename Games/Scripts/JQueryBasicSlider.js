<!--  Attach the plug-in to the slider parent element and adjust the settings as required -->
   $(document).ready(function () {

        photoPaneSlider = $('#fade-example').bjqs({
            'animation': 'slide',
            'showMarkers': false,
            'centerControls': true,
            'automatic': false,
            'nextText': '<i class="icon-chevron-right icon-white"></i>',
            'prevText': '<i class="icon-chevron-left icon-white"></i>',
            'useCaptions': false,
            'keyboardNav': true,
            'width': 714,

            'height': 950
        });



    });
