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

            $http.get('/plot/run?session_id=' + sessionId)
                .then(setRunPlot);

            $http.get('/plot/speed?session_id=' + sessionId)
                .then(setSpeedPlot);

        }

        function setGpsData(response) {
            vm.gps = response.data.result;
        }

        function setRunPlot(response) {
            vm.runPlotConfig = response.data;
        }
        function setSpeedPlot(response) {
            vm.speedPlot = response.data;
        }
    }
})();