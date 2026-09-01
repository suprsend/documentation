/**
 * Apollo.io website visitor tracking.
 *
 * Mintlify automatically includes every .js file in the content directory on
 * every page, so this file needs no registration in docs.json.
 *
 * Mintlify runs custom scripts after the page becomes interactive and does not
 * re-run them on client-side navigation. The Apollo tracker handles that itself:
 * it re-sends a page-visit event when a click changes location.href.
 *
 * Company-level visits are attributed to docs.suprsend.com, which is registered
 * as an allowed referrer on the Apollo tracker. Removing this file stops
 * documentation visitor tracking.
 */
(function () {
  var APOLLO_APP_ID = "663116d8353db703004051bb";

  if (window.__apolloTrackerLoaded) return;
  window.__apolloTrackerLoaded = true;

  var script = document.createElement("script");
  script.src =
    "https://assets.apollo.io/micro/website-tracker/tracker.iife.js?nocache=" +
    Math.random().toString(36).substring(7);
  script.async = true;
  script.defer = true;
  script.onload = function () {
    window.trackingFunctions.onLoad({ appId: APOLLO_APP_ID });
  };
  document.head.appendChild(script);
})();
