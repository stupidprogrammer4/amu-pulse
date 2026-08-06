from src.modules.chart.candle.routers.chart import router


class TestWhatTheChartRoutesSay:
    def test_a_chart_is_drawn_for_an_asset_and_for_a_source(self) -> None:
        paths = {route.path for route in router.routes}  # type: ignore[attr-defined]

        assert paths == {
            "/panel/candles/assets/{id:int}",
            "/panel/candles/sources/{id:int}",
        }

    def test_a_chart_is_only_ever_read(self) -> None:
        methods = {
            method
            for route in router.routes
            for method in route.methods  # type: ignore[attr-defined]
        }

        assert methods == {"GET"}
