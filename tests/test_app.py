"""Unit tests. Written with unittest so they run with `python -m unittest` or pytest."""
import unittest

from app import create_app, transit


class TransitLogicTests(unittest.TestCase):
    def test_arrival_exactly_on_time_is_due(self):
        # R1 departs S1 at t=0, reaches S2 (1/3 of the way) at t=600 s.
        # Leaving at k=-1 puts a bus at S2 at t=0.
        first = transit.next_arrivals("R1", "S2", now_s=0, count=2)
        self.assertEqual(first[0]["eta_seconds"], 0)
        self.assertEqual(first[1]["eta_seconds"], 600)

    def test_arrival_eta_in_minutes(self):
        first = transit.next_arrivals("R1", "S2", now_s=100, count=1)[0]
        self.assertEqual(first["eta_seconds"], 500)
        self.assertEqual(first["eta_min"], 8)

    def test_search_only_returns_forward_direction(self):
        forward = transit.search("S1", "S6", now_s=0)
        self.assertEqual([r["route_id"] for r in forward], ["R1"])
        self.assertEqual(transit.search("S6", "S1", now_s=0), [])

    def test_search_sorted_by_total_time(self):
        results = transit.search("S1", "S7", now_s=0)
        totals = [r["total_min"] for r in results]
        self.assertEqual(totals, sorted(totals))
        self.assertTrue(len(results) >= 2)  # R2 and R4 both serve S1 -> S7

    def test_validate_search(self):
        self.assertIsNone(transit.validate_search("S1", "S2"))
        self.assertIsNotNone(transit.validate_search("S1", "S1"))
        self.assertIsNotNone(transit.validate_search("S1", "ZZZ"))
        self.assertIsNotNone(transit.validate_search("<script>", "S2"))

    def test_arrivals_board_sorted_and_limited(self):
        board = transit.arrivals_at_stop("S1", now_s=1234, limit=4)
        self.assertLessEqual(len(board), 4)
        etas = [a["eta_seconds"] for a in board]
        self.assertEqual(etas, sorted(etas))

    def test_vehicle_progress_is_between_zero_and_one(self):
        for now in (0, 1, 599, 123456, 1_800_000_000):
            for v in transit.active_vehicles(now_s=now):
                self.assertGreaterEqual(v["progress"], 0)
                self.assertLessEqual(v["progress"], 1)
                self.assertIn(v["occupancy"], transit.OCCUPANCY)

    def test_every_route_has_vehicles_in_service(self):
        routes_seen = {v["route_id"] for v in transit.active_vehicles(now_s=1_800_000_000)}
        self.assertEqual(routes_seen, set(transit.ROUTES))


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_pages_render(self):
        for path in ("/", "/routes", "/track", "/scrum", "/about", "/stops/S1"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_search_valid(self):
        response = self.client.get("/?origin=S1&destination=S6")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Blue Line Express", response.data)

    def test_search_invalid_returns_400(self):
        self.assertEqual(self.client.get("/?origin=S1&destination=S1").status_code, 400)
        self.assertEqual(self.client.get("/?origin=nope&destination=S2").status_code, 400)

    def test_search_input_is_escaped(self):
        response = self.client.get("/?origin=%3Cscript%3Ealert(1)%3C/script%3E&destination=S2")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(b"<script>alert(1)</script>", response.data)

    def test_unknown_stop_page_404(self):
        self.assertEqual(self.client.get("/stops/NOPE").status_code, 404)

    def test_unknown_page_404(self):
        self.assertEqual(self.client.get("/does-not-exist").status_code, 404)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_api_routes_and_vehicles(self):
        routes = self.client.get("/api/routes").get_json()
        self.assertEqual(len(routes), len(transit.ROUTES))
        self.assertIsInstance(self.client.get("/api/vehicles").get_json(), list)

    def test_api_arrivals(self):
        ok = self.client.get("/api/arrivals/S2")
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.get_json()["arrivals"])
        self.assertEqual(self.client.get("/api/arrivals/XYZ").status_code, 404)
        self.assertEqual(self.client.get("/api/nope").status_code, 404)

    def test_security_headers_present(self):
        headers = self.client.get("/").headers
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")

    def test_api_not_cached(self):
        self.assertEqual(self.client.get("/api/vehicles").headers["Cache-Control"], "no-store")

    def test_no_inline_scripts_or_styles(self):
        # The CSP forbids them, so templates must not contain any.
        for path in ("/", "/track", "/scrum"):
            body = self.client.get(path).get_data(as_text=True).lower()
            self.assertNotIn("<script>", body)
            self.assertNotIn(" style=", body)

    def test_oversized_request_rejected(self):
        response = self.client.post("/", data=b"x" * (20 * 1024))
        self.assertIn(response.status_code, (405, 413))


if __name__ == "__main__":
    unittest.main()
