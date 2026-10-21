"""Smart Public Transportation web application (Flask application factory)."""
from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from . import transit
from .backlog import BACKLOG, DEFINITION_OF_DONE, SPRINTS

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # this app never needs large request bodies

    @app.after_request
    def set_security_headers(response):
        response.headers["Content-Security-Policy"] = CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        if request.path.startswith("/api/") or request.path == "/health":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        origin = request.args.get("origin", "")
        destination = request.args.get("destination", "")
        results, error, status = None, None, 200
        if origin or destination:
            error = transit.validate_search(origin, destination)
            if error:
                status = 400
            else:
                results = transit.search(origin, destination)
        page = render_template(
            "index.html",
            stops=transit.STOPS,
            origin=origin,
            destination=destination,
            results=results,
            error=error,
            route_count=len(transit.ROUTES),
            stop_count=len(transit.STOPS),
        )
        return page, status

    @app.get("/routes")
    def routes():
        return render_template("routes.html", routes=transit.list_routes())

    @app.get("/stops/<stop_id>")
    def stop_board(stop_id: str):
        if stop_id not in transit.STOPS:
            return render_template("error.html", code=404, message="That stop does not exist."), 404
        return render_template(
            "stop.html",
            stop_id=stop_id,
            stop_name=transit.STOPS[stop_id],
            stops=transit.STOPS,
            arrivals=transit.arrivals_at_stop(stop_id),
        )

    @app.get("/track")
    def track():
        return render_template("track.html", routes=transit.list_routes())

    @app.get("/scrum")
    def scrum():
        done_points = sum(item["points"] for item in BACKLOG if item["status"] == "Done")
        total_points = sum(item["points"] for item in BACKLOG)
        return render_template(
            "scrum.html",
            sprints=SPRINTS,
            backlog=BACKLOG,
            definition_of_done=DEFINITION_OF_DONE,
            done_points=done_points,
            total_points=total_points,
        )

    @app.get("/about")
    def about():
        return render_template("about.html")

    # ---- JSON API -------------------------------------------------------
    @app.get("/api/routes")
    def api_routes():
        return jsonify(transit.list_routes())

    @app.get("/api/arrivals/<stop_id>")
    def api_arrivals(stop_id: str):
        if stop_id not in transit.STOPS:
            return jsonify(error="unknown stop"), 404
        return jsonify(stop=stop_id, name=transit.STOPS[stop_id], arrivals=transit.arrivals_at_stop(stop_id))

    @app.get("/api/vehicles")
    def api_vehicles():
        return jsonify(transit.active_vehicles())

    @app.get("/health")
    def health():
        return jsonify(status="ok", routes=len(transit.ROUTES), stops=len(transit.STOPS))

    # ---- Errors ---------------------------------------------------------
    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="not found"), 404
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("error.html", code=413, message="Request too large."), 413

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("error.html", code=500, message="Something went wrong on our side."), 500

    return app
