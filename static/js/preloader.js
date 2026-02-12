/**
 * preloader.js - Handles the initial loading screen for shop management system
 */
(function ($) {
  "use strict";

  var PRELOADER_CONFIG = {
    minTime: 1800, // Minimum display time in ms
    wrapperId: "#preloader-wrapper",
    progressBar: ".progress-bar",
    animationDuration: 2000, // Progress bar animation duration
  };

  function animateProgressBar($progressBar, duration) {
    var start = null;
    var initialWidth = 0;
    var targetWidth = 100;

    function step(timestamp) {
      if (!start) start = timestamp;
      var progress = timestamp - start;
      var percentage = Math.min(
        (progress / duration) * targetWidth,
        targetWidth,
      );

      $progressBar.css("width", percentage + "%");

      if (progress < duration) {
        window.requestAnimationFrame(step);
      }
    }

    window.requestAnimationFrame(step);
  }

  function initPreloader() {
    var $preloader = $(PRELOADER_CONFIG.wrapperId);
    if (!$preloader.length) return;

    var $progressBar = $preloader.find(PRELOADER_CONFIG.progressBar);
    var startTime = Date.now();

    // Start progress bar animation
    if ($progressBar.length) {
      animateProgressBar($progressBar, PRELOADER_CONFIG.animationDuration);
    }

    $(window).on("load", function () {
      var elapsedTime = Date.now() - startTime;
      var remainingTime = Math.max(0, PRELOADER_CONFIG.minTime - elapsedTime);

      setTimeout(function () {
        $preloader.css({
          transition: "opacity 0.5s ease, visibility 0.5s ease",
          opacity: "0",
          visibility: "hidden",
        });

        // Remove from DOM after transition
        setTimeout(function () {
          $preloader.remove();
          // Re-enable body scroll
          $("body").css("overflow", "auto");
        }, 500);
      }, remainingTime);
    });
  }

  // Initialize immediately
  initPreloader();
})(jQuery);
