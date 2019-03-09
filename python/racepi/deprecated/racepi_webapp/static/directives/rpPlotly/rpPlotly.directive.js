(function() {
    "use strict";

    angular.module('racepi')
        .directive('rpPlotly', directive);

    directive.$inject = ['$window'];
    function directive($window) {
        var _directive = {
            restrict: 'E',
            scope: {
                config: '='
            },
            template: '<div></div>',
            link: link
        };
        return _directive;

        function link(scope, element) {
            var plot = element[0].children[0];
            var initialized = false;

            function update() {
                if (!scope.config) {
                    return;
                }

                if (!initialized) {
                    Plotly.newPlot(plot, scope.config.data, scope.config.layout);
                    initialized = true;
                }

                plot.data = scope.config.data;
                plot.layout = scope.config.layout;
                Plotly.redraw(plot);
                resize();
            }

            function resize() {
                if (!(initialized && scope.config)) return;
                Plotly.Plots.resize(plot);
            }

            scope.$watch('config', function (newConfig, oldConfig) {
                if (!initialized || !angular.equals(newConfig, oldConfig)) {
                    update();
                }
            }, true);

            scope.$watch(function() {
                return element[0].offsetWidth;
            }, function (newWidth, oldWidth) {
                if (newWidth !== oldWidth) {
                    resize();
                }
            })

            angular.element($window).bind('resize', resize);
        }
    }
})();
