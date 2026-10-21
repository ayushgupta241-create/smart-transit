(function () {
  "use strict";

  var STOP_WIDTH = 96; // must match .stop width in style.css
  var REFRESH_MS = 5000;
  var status = document.getElementById("live-status");

  function render(vehicles) {
    document.querySelectorAll("[data-route]").forEach(function (section) {
      var lane = section.querySelector(".vehicles");
      var list = section.querySelector(".vehicle-list");
      lane.replaceChildren();
      list.replaceChildren();

      vehicles
        .filter(function (v) { return v.route_id === section.dataset.route; })
        .forEach(function (v) {
          var dot = document.createElement("div");
          dot.className = "vehicle";
          dot.style.left = "calc(" + STOP_WIDTH / 2 + "px + " + v.progress + " * (100% - " + STOP_WIDTH + "px))";
          dot.title = v.id + " · next stop " + v.next_stop + " · occupancy " + v.occupancy;
          dot.textContent = v.id.slice(-3);
          lane.appendChild(dot);

          var item = document.createElement("li");
          item.textContent = v.id + " → " + v.next_stop + " (occupancy: " + v.occupancy + ")";
          list.appendChild(item);
        });
    });
  }

  function refresh() {
    fetch("/api/vehicles", { headers: { Accept: "application/json" } })
      .then(function (res) {
        if (!res.ok) { throw new Error("HTTP " + res.status); }
        return res.json();
      })
      .then(function (vehicles) {
        render(vehicles);
        status.textContent = "Live · updated " + new Date().toLocaleTimeString();
      })
      .catch(function () {
        status.textContent = "Live data unavailable. Retrying…";
      });
  }

  refresh();
  setInterval(refresh, REFRESH_MS);
})();
