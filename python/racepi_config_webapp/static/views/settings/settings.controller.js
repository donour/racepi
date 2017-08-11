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

        this.load_fields = function() {
            console.log(vm.selectedConfig);
            $http.get('/settings/'+vm.selectedConfig).then(set_vm_fields);
            function set_vm_fields(response) {
                vm.config_setting = response.data;
            }
        }

        this.save_fields = function() {
            console.log("save");
            var data = JSON.stringify(vm.config_setting)
            console.log(data);
            $http.post('/settings/'+vm.selectedConfig, data);
            $http.get('/active_setting_profile/'+vm.selectedConfig);
        }
    }
})();