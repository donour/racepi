(function() {
    "use strict";

    angular.module('racepi')
        .controller('DetailsCtrl', controller);

    controller.$inject = ['$http', '$stateParams'];
    function controller($http, $stateParams) {
        var vm = this;
        vm.sessionId = $stateParams.sessionId;

        if (vm.sessionId) {
            init(vm.sessionId);
        }

        function init(sessionId) {
            $http.get('/data/gps?session_id=' + sessionId)
                .then(setGpsData);

            $http.get('/plot/accel?session_id=' + sessionId)
                .then(setAccelPlot);

            $http.get('/plot/gps?session_id=' + sessionId)
                .then(setGpsPlot);

        }

        function setGpsData(response) {
            vm.gps = response.data.result;
        }

        function setAccelPlot(response) {
            vm.accelPlotConfig = response.data;
        }

        function setGpsPlot(response) {
            vm.gpsPlotConfig = response.data;
        }

    }
})();