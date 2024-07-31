
    $(".chzn-select").chosen();
    $(".chzn-select-deselect").chosen({ allow_single_deselect: true });
    $(".chzn-select").chosen().change(
      function () {
          photoPaneSlider.goto($(this).val());
      }
      );
