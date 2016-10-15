"use strict";
var App = angular.module('routingDemoApp',['ui.router', 'ngResource']);

App.config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider){
                // For any unmatched url, send to /business
                $urlRouterProvider.otherwise("/business")

                $stateProvider
                        .state('business', {//State demonstrating Nested views
                            url: "/business",
                            templateUrl: "static/views/tableData/tableData.html"
                        })
                        .state('sessions', {
                            url: "/sessions",
                            templateUrl:"static/views/sessionData/sessionData.html",
                            controller: 'sessionDataController',
                            controllerAs: "vm"
                        })
                        .state('gps', {
                            url: "/gps",
                            templateUrl:"static/views/tableData/tableData.html",
                            controller: 'imuDataController',
                            controllerAs: "vm"
                        })

            }])
            .controller('sessionDataController', function($scope, $http, $rootScope) {
                var vm = this;
                vm.selectSession = function selectSession(source) {
                    console.log(source[0]);
                    vm.selectedSession = source[0]
                    $rootScope.selectedSession = source[0];
                     $http.get('/data/imu?session_id='+ $rootScope.selectedSession)
                                    .then(function(response) {
                                        $scope.imuSamples = response.data.result;})
                                    $http.get('/data/gps?session_id='+ $rootScope.selectedSession)
                                        .then(function(response) {
                                            $scope.gpsSamples = response.data.result;})
                };
                $http.get('/data/sessions')
                .then(function(response) {
                    $scope.sessions = response.data.result;
            })})
            .controller('imuDataController', function($scope, $http, $rootScope) {


            })

            .controller('gpsDataController', function($scope, $http, $rootScope) {
                $http.get('/data/gps?session_id='+ $rootScope.selectedSession)
                .then(function(response) {
                     $scope.gpsSamples = response.data.result;
            })});


