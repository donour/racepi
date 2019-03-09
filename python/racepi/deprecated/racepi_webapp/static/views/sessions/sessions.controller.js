(function() {
    "use strict";

    angular.module('racepi')
        .controller('SessionsCtrl', controller);

    controller.$inject = ['$http'];
    function controller($http) {
        var vm = this;

        $http.get('/data/sessions').then(setSessions);

        function setSessions(response) {
            vm.sessions = response.data.result;
        }
    }
})();