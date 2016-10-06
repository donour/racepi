"use strict";
app.controller('imuCtrl', function($scope, $http) {
    $http.get("/imu")
    .then(function (response) {$scope.samples = response.data.result;});
});