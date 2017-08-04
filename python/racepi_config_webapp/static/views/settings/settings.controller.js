(function() {
    "use strict";

    angular.module('racepi')
        .controller('SettingsCtrl', controller);

    controller.$inject = ['$http'];
    function controller($http) {
        var vm = this;
        $http.get('/settings').then(setSettings);
        function setSettings(response) {
            vm.config_profiles = response.data.configuration_profiles;
        }
    }
})();