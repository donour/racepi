(function() {
    "use strict";

    angular.module('racepi')
        .directive('rpNavBar', directive);

    directive.$inject = ['$stateParams'];
    function directive($stateParams) {
        var _directive = {
            restrict: 'E',
            scope: {},
            templateUrl: 'static/directives/rpNavBar/rpNavBar.template.html',
            controller: controller,
            controllerAs: 'vm',
            bindToController: true
        };
        return _directive;

        controller.$inject = ['$scope', '$stateParams'];
        function controller($scope, $stateParams) {
            var vm = this;

            if ($stateParams.sessionId) {
                setSessionId($stateParams.sessionId);
            }
            $scope.$watch(function () {
                return $stateParams.sessionId
            }, setSessionId);

            function setSessionId(sessionId) {
                vm.sessionId = sessionId;
                console.log('', vm)
            }
        }
    }
})();