"use strict";
app.controller('gpsCtrl', function($scope, $http) {
    $http.get("/gps")
    .then(function (response) {$scope.samples = response.data.result;});
});