(function() {
    "use strict";

    angular.module('racepi', ['ui.router'])
        .config(routeConfig);

    routeConfig.$inject = ['$stateProvider', '$urlRouterProvider'];
    function routeConfig($stateProvider, $urlRouterProvider) {
        // For any unmatched url, send to /sessions
        $urlRouterProvider.otherwise("/sessions");

        $stateProvider
            .state('sessions', {
                url: "/sessions",
                templateUrl:"static/views/sessions/sessions.template.html",
                controller: 'SessionsCtrl',
                controllerAs: "vm"
            })
            .state('details', {
                url: "/details/{sessionId}",
                templateUrl:"static/views/details/details.template.html",
                controller: 'DetailsCtrl',
                controllerAs: "vm"
            });
    }

})();
